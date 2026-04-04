"""
Archer 产品监控器 v2
==================
每次监控都实时检查产品状态，不用快照

工作流程：
1. 从 /get_all_links 获取当前所有有效的 ASIN
2. 从 /check_product 逐个验证每个 ASIN 是否仍然有效
3. 无效的 ASIN → 在 Google Ads 中搜索并暂停对应广告系列
"""

import os
import json
import logging
from typing import List, Set, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from .archer_client import ArcherClient
from .google_ads_data import GoogleAdsDataFetcher

logger = logging.getLogger(__name__)

REMOVED_LOG = os.path.join(os.path.dirname(__file__), "..", "logs", "removed_products.json")


@dataclass
class RemovedProduct:
    """被删除/下架的产品记录"""
    asin: str
    detected_at: str
    product_name: str = ""
    linked_campaigns: List[str] = None

    def __post_init__(self):
        if self.linked_campaigns is None:
            self.linked_campaigns = []


@dataclass
class MonitorResult:
    """监控结果"""
    checked_at: str
    total_checked_asins: int
    newly_unavailable: List[str]      # 本次新发现无效的 ASIN
    all_unavailable_asins: List[str] # 历史所有无效 ASIN
    paused_campaigns: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProductMonitor:
    """
    Archer 产品监控器 v2

    核心逻辑：
    1. 从 /get_all_links 获取当前所有已创建的 ASIN
    2. 对每个 ASIN 调用 /check_product 验证是否仍然有效
    3. 无效的 ASIN → 暂停 Google Ads 中 final_url 包含该 ASIN 的广告系列
    """

    def __init__(self, archer_client: ArcherClient, gads_fetcher: GoogleAdsDataFetcher):
        self.archer = archer_client
        self.gads = gads_fetcher

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(REMOVED_LOG), exist_ok=True)

    # ─────────────────────────────────────────────
    # Step 1: 获取当前所有 ASIN（从 /get_all_links）
    # ─────────────────────────────────────────────
    def fetch_current_asins(self) -> Dict[str, Dict[str, str]]:
        """
        从 /get_all_links 获取所有有效 ASIN

        Returns:
            {asin: {"link_name": ..., "product_name": ...}}
        """
        asins: Dict[str, Dict[str, str]] = {}
        page = 1
        limit = 500
        max_pages = 10

        while page <= max_pages:
            logger.info(f"正在获取 Archer Attribution Links，第 {page} 页...")

            try:
                response = self.archer.get_all_links(page=page, limit=limit)
                links = response.get("all_links", []) or response.get("links", []) or []

                if not links:
                    break

                for link in links:
                    asin = link.get("asin", "").strip()
                    if asin:
                        asins[asin] = {
                            "link_name": link.get("link_name", ""),
                            "product_name": link.get("product_name", "")
                        }

                pagination = response.get("pagination_info", {})
                total_pages = pagination.get("total_pages", 1)
                if page >= total_pages:
                    break

                page += 1

            except Exception as e:
                logger.error(f"获取 Archer Attribution Links 失败: {e}")
                break

        logger.info(f"Archer 当前共有 {len(asins)} 个有效 ASIN")
        return asins

    # ─────────────────────────────────────────────
    # Step 2: 验证每个 ASIN 的状态
    # ─────────────────────────────────────────────
    def check_asins(self, asins: Dict[str, Dict[str, str]]) -> Dict[str, bool]:
        """
        对每个 ASIN 调用 /check_product 验证是否仍然有效

        Returns:
            {asin: True(有效)/False(无效)}
        """
        results = {}
        asin_list = list(asins.keys())

        logger.info(f"正在验证 {len(asin_list)} 个 ASIN 的状态...")

        for asin in asin_list:
            try:
                is_available = self.archer.is_product_available(asin)
                results[asin] = is_available
            except Exception as e:
                logger.warning(f"检查 ASIN {asin} 失败: {e}")
                results[asin] = False

            if results[asin]:
                logger.info(f"  ✅ {asin} 有效")
            else:
                logger.warning(f"  ❌ {asin} 无效")

        return results

    # ─────────────────────────────────────────────
    # Step 3: 暂停无效 ASIN 对应的广告系列
    # ─────────────────────────────────────────────
    def pause_campaigns_by_asin(self, asin: str) -> List[Dict[str, Any]]:
        """
        查找并暂停所有 final_url 包含指定 ASIN 的广告系列
        """
        logger.info(f"正在搜索包含 ASIN={asin} 的广告...")

        paused = []
        all_records = self.gads.fetch_all_customers_ads(
            start_date="20200101",
            end_date=datetime.now().strftime("%Y%m%d")
        )

        # 按 campaign 聚合
        campaign_ads: Dict[str, List] = {}
        for rec in all_records:
            if asin in (rec.final_url or ""):
                if rec.campaign_id not in campaign_ads:
                    campaign_ads[rec.campaign_id] = []
                campaign_ads[rec.campaign_id].append(rec)

        if not campaign_ads:
            logger.info(f"  未找到包含 ASIN={asin} 的广告")
            return []

        logger.info(f"  找到 {len(campaign_ads)} 个广告系列包含此 ASIN")

        for campaign_id, records in campaign_ads.items():
            campaign_name = records[0].campaign_name

            try:
                success = self.gads._client.pause_campaign(campaign_id)
                if success:
                    logger.info(f"  ✅ 已暂停: {campaign_name} (ID: {campaign_id})")
                    paused.append({
                        "asin": asin,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "customer_id": records[0].customer_id,
                        "paused_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    })
                else:
                    logger.warning(f"  ⚠️ 暂停失败: {campaign_name}")
            except Exception as e:
                logger.error(f"  ❌ 暂停出错: {campaign_name} - {e}")

        return paused

    # ─────────────────────────────────────────────
    # 历史删除记录管理
    # ─────────────────────────────────────────────
    def load_removed_log(self) -> Dict[str, RemovedProduct]:
        if not os.path.exists(REMOVED_LOG):
            return {}
        try:
            with open(REMOVED_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: RemovedProduct(**v) for k, v in data.items()}
        except Exception:
            return {}

    def save_removed_log(self, removed: Dict[str, RemovedProduct]):
        self._ensure_dirs()
        data = {k: asdict(v) for k, v in removed.items()}
        with open(REMOVED_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ─────────────────────────────────────────────
    # 核心监控流程
    # ─────────────────────────────────────────────
    def check_and_pause(self) -> MonitorResult:
        """
        执行监控：实时验证产品状态 + 暂停无效广告

        Returns:
            MonitorResult
        """
        logger.info("=" * 50)
        logger.info("开始产品监控（实时验证）")
        logger.info("=" * 50)

        # Step 1: 获取当前 ASIN 列表
        current_asins = self.fetch_current_asins()

        # Step 2: 逐个验证状态
        validation_results = self.check_asins(current_asins)

        # 找出无效的 ASIN
        unavailable_asins = [asin for asin, ok in validation_results.items() if not ok]
        logger.info(f"\n检查完成：{len(unavailable_asins)} 个 ASIN 无效/已下架")

        # Step 3: 加载历史记录
        removed_log = self.load_removed_log()

        # 标记新增无效
        newly_unavailable = [asin for asin in unavailable_asins if asin not in removed_log]
        logger.info(f"新增无效: {len(newly_unavailable)} 个")

        # Step 4: 暂停新增无效 ASIN 的广告
        paused_campaigns = []
        if newly_unavailable:
            logger.info("=" * 50)
            logger.info(f"正在暂停 {len(newly_unavailable)} 个无效 ASIN 对应的广告...")
            logger.info("=" * 50)

            for asin in newly_unavailable:
                paused = self.pause_campaigns_by_asin(asin)
                paused_campaigns.extend(paused)

                # 更新历史记录
                removed_log[asin] = RemovedProduct(
                    asin=asin,
                    detected_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    product_name=current_asins.get(asin, {}).get("product_name", ""),
                    linked_campaigns=[c["campaign_id"] for c in paused]
                )

        # 保存历史记录
        self.save_removed_log(removed_log)

        result = MonitorResult(
            checked_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            total_checked_asins=len(current_asins),
            newly_unavailable=newly_unavailable,
            all_unavailable_asins=unavailable_asins,
            paused_campaigns=paused_campaigns
        )

        self._log_result(result)
        return result

    def _log_result(self, result: MonitorResult):
        """打印并保存结果"""
        print("\n" + "=" * 60)
        print(f"  Archer 产品监控报告  |  {result.checked_at}")
        print("=" * 60)
        print(f"  本次检查 ASIN 数:    {result.total_checked_asins}")
        print(f"  本次新增无效:       {len(result.newly_unavailable)}")
        print(f"  累计无效 ASIN:      {len(result.all_unavailable_asins)}")
        print(f"  本次暂停广告系列:    {len(result.paused_campaigns)}")

        if result.newly_unavailable:
            print("-" * 60)
            print(f"  {'ASIN':<15} {'广告系列':<35}")
            print("-" * 60)
            for c in result.paused_campaigns:
                name = c["campaign_name"][:33] + ".." if len(c["campaign_name"]) > 35 else c["campaign_name"]
                print(f"  {c['asin']:<15} {name:<35}")

        print("=" * 60)

        # 保存到日志
        log_file = os.path.join(
            os.path.dirname(REMOVED_LOG),
            f"monitor_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"监控结果已保存: {log_file}")
