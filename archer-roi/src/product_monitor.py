"""
Archer 产品监控器
================
每隔2小时检测是否有产品在 Archer 联盟被删除/下架，
如有则自动暂停对应的 Google Ads 广告系列

快照文件: data/snapshot_asins.json
检测结果: logs/removed_products.json
"""

import os
import json
import logging
from typing import List, Set, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .archer_client import ArcherClient
from .google_ads_data import GoogleAdsDataFetcher

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOT_FILE = os.path.join(SNAPSHOT_DIR, "snapshot_asins.json")
REMOVED_LOG = os.path.join(os.path.dirname(__file__), "..", "logs", "removed_products.json")


@dataclass
class RemovedProduct:
    """被删除的产品记录"""
    asin: str
    detected_at: str          # 检测时间
    last_seen_at: str         # 上次快照中最后出现的时间
    product_name: str         # 产品名称（从快照中获取）
    linked_campaigns: List[str] = None  # 被暂停的广告系列列表

    def __post_init__(self):
        if self.linked_campaigns is None:
            self.linked_campaigns = []


@dataclass
class MonitorResult:
    """监控结果"""
    checked_at: str
    total_active_asins: int
    newly_removed: List[str]          # 新删除的 ASIN 列表
    all_removed_asins: List[str]     # 历史所有删除的 ASIN（从未恢复）
    paused_campaigns: List[Dict[str, Any]]  # 本次暂停的广告系列

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProductMonitor:
    """
    Archer 产品监控器

    工作流程：
    1. 从 Archer 获取当前所有有效产品的 ASIN
    2. 加载上次快照，对比找出新增删除的 ASIN
    3. 对每个被删除的 ASIN，在 Google Ads 中搜索并暂停对应广告
    4. 保存新快照
    """

    def __init__(self, archer_client: ArcherClient, gads_fetcher: GoogleAdsDataFetcher):
        self.archer = archer_client
        self.gads = gads_fetcher

    def _ensure_dirs(self):
        """确保数据目录存在"""
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(REMOVED_LOG), exist_ok=True)

    # ─────────────────────────────────────────────
    # Archer 数据获取
    # ─────────────────────────────────────────────

    def fetch_current_asins(self) -> Set[str]:
        """
        从 Archer 获取当前所有有效的 ASIN

        通过 get_all_links 获取所有 Attribution Links，
        提取其中的 ASIN（去重）
        """
        asins: Set[str] = set()
        page = 1
        limit = 500
        max_pages = 10

        while page <= max_pages:
            logger.info(f"正在获取 Archer 产品列表，第 {page} 页...")

            try:
                response = self.archer.get_all_links(page=page, limit=limit)
                links = response.get("all_links", []) or response.get("links", []) or []

                if not links:
                    break

                for link in links:
                    asin = link.get("asin", "").strip()
                    if asin:
                        asins.add(asin)

                # 分页判断
                pagination = response.get("pagination_info", {})
                total_pages = pagination.get("total_pages", 1)
                if page >= total_pages:
                    break

                page += 1

            except Exception as e:
                logger.error(f"获取 Archer 产品列表失败: {e}")
                break

        logger.info(f"Archer 当前共有 {len(asins)} 个有效 ASIN")
        return asins

    # ─────────────────────────────────────────────
    # 快照管理
    # ─────────────────────────────────────────────

    def load_snapshot(self) -> Dict[str, str]:
        """
        加载上次快照

        Returns:
            {asin: detected_at} 字典
        """
        if not os.path.exists(SNAPSHOT_FILE):
            return {}

        try:
            with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"已加载快照，包含 {len(data)} 个 ASIN")
            return data
        except Exception as e:
            logger.warning(f"加载快照失败: {e}")
            return {}

    def save_snapshot(self, asins: Set[str]):
        """保存当前 ASIN 集合为快照"""
        self._ensure_dirs()

        snapshot = {
            asin: datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            for asin in asins
        }

        with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        logger.info(f"快照已保存: {SNAPSHOT_FILE} ({len(snapshot)} ASIN)")

    def load_removed_log(self) -> Dict[str, RemovedProduct]:
        """加载历史删除记录"""
        if not os.path.exists(REMOVED_LOG):
            return {}

        try:
            with open(REMOVED_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: RemovedProduct(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"加载删除记录失败: {e}")
            return {}

    def save_removed_log(self, removed: Dict[str, RemovedProduct]):
        """保存历史删除记录"""
        self._ensure_dirs()

        data = {k: asdict(v) for k, v in removed.items()}
        with open(REMOVED_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ─────────────────────────────────────────────
    # 核心监控逻辑
    # ─────────────────────────────────────────────

    def check_and_pause(self) -> MonitorResult:
        """
        执行监控：检测被删产品 + 暂停广告

        Returns:
            MonitorResult 监控结果
        """
        logger.info("=" * 50)
        logger.info("开始产品监控")
        logger.info("=" * 50)

        # Step 1: 获取当前 ASIN 列表
        current_asins = self.fetch_current_asins()

        # Step 2: 加载快照
        snapshot = self.load_snapshot()
        snapshot_asins = set(snapshot.keys())

        # Step 3: 找出新增删除的 ASIN
        removed_asins = snapshot_asins - current_asins
        logger.info(f"快照中有 {len(snapshot_asins)} ASIN，当前 {len(current_asins)}，"
                    f"检测到 {len(removed_asins)} 个已删除")

        # 加载历史删除记录
        removed_log = self.load_removed_log()

        # 标记新增删除
        newly_removed = []
        for asin in removed_asins:
            if asin not in removed_log:
                product_name = ""  # 快照中没有产品名，从 link_info 补
                removed_log[asin] = RemovedProduct(
                    asin=asin,
                    detected_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    last_seen_at=snapshot.get(asin, ""),
                    product_name=product_name
                )
                newly_removed.append(asin)

        # Step 4: 暂停对应的 Google Ads 广告系列
        paused_campaigns = []
        if newly_removed:
            logger.info("=" * 50)
            logger.info(f"正在暂停 {len(newly_removed)} 个已删除 ASIN 对应的广告...")
            logger.info("=" * 50)

            for asin in newly_removed:
                paused = self._pause_campaigns_by_asin(asin)
                paused_campaigns.extend(paused)

                # 更新删除记录
                if asin in removed_log:
                    removed_log[asin].linked_campaigns = [
                        c["campaign_id"] for c in paused
                    ]

        # Step 5: 保存新快照和删除记录
        self.save_snapshot(current_asins)
        self.save_removed_log(removed_log)

        result = MonitorResult(
            checked_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            total_active_asins=len(current_asins),
            newly_removed=newly_removed,
            all_removed_asins=list(removed_asins),
            paused_campaigns=paused_campaigns
        )

        self._log_result(result)
        return result

    def _pause_campaigns_by_asin(self, asin: str) -> List[Dict[str, Any]]:
        """
        查找并暂停所有 final_url 包含指定 ASIN 的广告系列

        Returns:
            被暂停的广告系列列表
        """
        logger.info(f"正在搜索包含 ASIN={asin} 的广告...")

        paused = []
        all_records = self.gads.fetch_all_customers_ads(
            start_date="20200101",  # 从尽可能早的时间开始
            end_date=datetime.now().strftime("%Y%m%d")
        )

        # 按 campaign 聚合：同一个 campaign 可能有多条广告
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
            customer_id = records[0].campaign_name  # 需要从记录中拿到 customer_id

            try:
                success = self.gads._client.pause_campaign(campaign_id)
                if success:
                    logger.info(f"  ✅ 已暂停: {campaign_name} (ID: {campaign_id})")
                    paused.append({
                        "asin": asin,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "paused_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    })
                else:
                    logger.warning(f"  ⚠️ 暂停失败: {campaign_name} (ID: {campaign_id})")
            except Exception as e:
                logger.error(f"  ❌ 暂停出错: {campaign_name} - {e}")

        return paused

    def _log_result(self, result: MonitorResult):
        """打印结果摘要"""
        print("\n" + "=" * 60)
        print(f"  产品监控报告  |  {result.checked_at}")
        print("=" * 60)
        print(f"  当前有效 ASIN:    {result.total_active_asins}")
        print(f"  本次新增删除:     {len(result.newly_removed)}")
        print(f"  累计删除（未恢复）: {len(result.all_removed_asins)}")
        print(f"  本次暂停广告系列:  {len(result.paused_campaigns)}")

        if result.paused_campaigns:
            print("-" * 60)
            print(f"  {'ASIN':<15} {'广告系列':<35}")
            print("-" * 60)
            for c in result.paused_campaigns:
                name = c["campaign_name"][:33] + ".." if len(c["campaign_name"]) > 35 else c["campaign_name"]
                print(f"  {c['asin']:<15} {name:<35}")

        print("=" * 60)

        # 保存到日志文件
        log_file = os.path.join(
            os.path.dirname(REMOVED_LOG),
            f"monitor_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"监控结果已保存: {log_file}")
