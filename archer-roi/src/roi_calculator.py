"""
ROI 计算器
==========
合并 Google Ads 花费数据 + Archer 佣金数据，计算每个链接的收益率

关联逻辑：
  Google Ads final_url_suffix 包含 aa_campaignid, aa_adgroupid, aa_creativeid
  Archer 的 get_link_data 返回结果中，每个链接有类似字段可对应
  关联 key = aa_campaignid + aa_adgroupid + aa_creativeid
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .archer_client import ArcherClient
from .google_ads_data import AdRecord, GoogleAdsDataFetcher

logger = logging.getLogger(__name__)


@dataclass
class LinkROI:
    """单个链接的 ROI 数据"""
    # 关联 key
    link_name: str
    asin: str
    product_name: str = ""   # 产品名称
    created_date: str = ""    # 广告创建日期

    # Google Ads 花费数据
    campaign_id: str = ""
    campaign_name: str = ""
    ad_group_id: str = ""
    ad_id: str = ""
    clicks: int = 0
    impressions: int = 0
    cost_usd: float = 0.0
    conversions: float = 0.0
    
    # Archer 佣金数据
    archer_clicks: int = 0           # Archer 记录的点击
    archer_sales: float = 0.0         # Archer 记录的销售额
    archer_units: int = 0             # Archer 记录的销售数量
    archer_commission: float = 0.0    # Archer 记录的佣金
    
    # 计算指标
    ROAS: float = 0.0      # 广告支出回报率 = 销售额 / 广告花费
    RPC: float = 0.0       # 每次点击收入
    CPA: float = 0.0       # 每次转化成本
    commission_rate: float = 0.0  # 估算佣金率 = 佣金 / 销售额
    
    # 元数据
    date_range: str = ""


class ROIReport:
    """ROI 报告"""
    
    def __init__(self):
        self.links: List[LinkROI] = []
        self.date_range: str = ""
        self.generated_at: str = ""
    
    def add(self, link_roi: LinkROI):
        self.links.append(link_roi)
    
    def to_dict(self) -> Dict[str, Any]:
        total_cost = sum(l.cost_usd for l in self.links)
        total_sales = sum(l.archer_sales for l in self.links)
        total_commission = sum(l.archer_commission for l in self.links)
        total_clicks_gads = sum(l.clicks for l in self.links)
        total_clicks_archer = sum(l.archer_clicks for l in self.links)
        
        return {
            "date_range": self.date_range,
            "generated_at": self.generated_at,
            "summary": {
                "total_cost_usd": round(total_cost, 2),
                "total_sales_usd": round(total_sales, 2),
                "total_commission_usd": round(total_commission, 2),
                "overall_roas": round(total_sales / total_cost, 2) if total_cost > 0 else 0,
                "overall_roi_pct": round((total_commission - total_cost) / total_cost * 100, 2) if total_cost > 0 else 0,
                "total_ads_clicks": total_clicks_gads,
                "total_archer_clicks": total_clicks_archer,
                "link_count": len(self.links)
            },
            "links": [asdict(l) for l in self.links]
        }
    
    def print_summary(self):
        """打印格式化报告 - 按产品(ASIN)汇总"""
        d = self.to_dict()
        s = d["summary"]

        print("\n" + "=" * 80)
        print(f"  Archer × Google Ads ROI 报告  |  {d['date_range']}")
        print("=" * 80)
        print(f"  总广告花费:     ${s['total_cost_usd']:.2f}")
        print(f"  总销售额:       ${s['total_sales_usd']:.2f}")
        print(f"  总佣金:         ${s['total_commission_usd']:.2f}")
        print(f"  整体 ROAS:      {s['overall_roas']:.2f}x")
        active_count = sum(1 for l in self.links if l.cost_usd > 0 or l.archer_commission > 0)
        print(f"  整体 ROI:       {s['overall_roi_pct']:.1f}%")
        print(f"  有数据产品:     {active_count} 个")
        print("-" * 80)

        if not self.links:
            print("  无数据")
            return

        # ── 按 ASIN 汇总 ──────────────────────────────
        asins: Dict[str, Dict[str, Any]] = {}
        for link in self.links:
            asin = link.asin or "Unknown"
            if asin not in asins:
                asins[asin] = {
                    "cost": 0.0,
                    "sales": 0.0,
                    "commission": 0.0,
                    "clicks": 0,
                    "campaigns": set(),
                    "product_name": link.product_name or "",
                    "created_date": link.created_date or "",
                }

            # 记录创建时间（同一ASIN取最早的）
            cd = link.created_date or ""
            if cd and (not asins[asin]["created_date"] or cd < asins[asin]["created_date"]):
                asins[asin]["created_date"] = cd
            asins[asin]["cost"] += link.cost_usd
            asins[asin]["sales"] += link.archer_sales
            asins[asin]["commission"] += link.archer_commission
            asins[asin]["clicks"] += link.clicks
            if link.campaign_id:
                asins[asin]["campaigns"].add(link.campaign_id)

        # 按佣金降序排列
        sorted_asins = sorted(asins.items(), key=lambda x: x[1]["commission"], reverse=True)

        print(f"  {'ASIN':<14} {'产品名称':<24} {'创建日期':<12} {'广告费':>8} {'佣金':>8} {'ROI%':>8}")
        print("-" * 95)

        active = [(a, d) for a, d in sorted_asins if d["cost"] > 0 or d["commission"] > 0]
        inactive = [(a, d) for a, d in sorted_asins if d["cost"] == 0 and d["commission"] == 0]

        for asin, data in active:
            name = (data.get("product_name") or asin or "Unknown")[:22]
            name = name + " " * (22 - len(name)) if len(name) < 22 else name[:22] + ".."
            created = data.get("created_date", "—")

            if data["cost"] > 0:
                roi_pct = (data["commission"] - data["cost"]) / data["cost"] * 100
                roi_str = f"{roi_pct:+.0f}%"
                if roi_pct > 0:
                    roi_str += " 💰"
                elif roi_pct < 0:
                    roi_str += " ⬇"
            else:
                roi_str = "+∞ 💰"

            print(f"  {asin:<14} {name:<24} {created:<12} ${data['cost']:>6.2f} ${data['commission']:>6.2f} {roi_str}")

        if inactive:
            print(f"  ... 另有 {len(inactive)} 个产品无广告费也无佣金")

        print("=" * 80)
        print()


class ROICalculator:
    """
    ROI 计算器
    
    核心流程：
    1. 从 Google Ads 拉取 Amazon 广告花费数据
    2. 从 Archer 获取各链接佣金数据
    3. 通过 aa_campaignid / aa_adgroupid / aa_creativeid 关联
    4. 计算 ROI 并输出报告
    """
    
    # Archer 链接数据中的排序字段映射
    SORT_CLICKS = 0
    SORT_SALES = 1
    SORT_UNITS = 2
    SORT_PURCHASES = 3
    
    def __init__(
        self,
        archer_client: ArcherClient,
        gads_fetcher: GoogleAdsDataFetcher
    ):
        self.archer = archer_client
        self.gads = gads_fetcher
    
    def _parse_date(self, date_str: str) -> str:
        """确保日期格式为 YYYYMMDD"""
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        # 尝试解析并转换
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d")
    
    def _fetch_archer_link_data(
        self,
        start_date: str,
        end_date: str,
        min_clicks: int = 0
    ) -> List[Dict[str, Any]]:
        """
        从 Archer 获取所有链接的汇总数据
        
        Returns:
            链接数据列表，每条包含:
            - link_name
            - asin
            - totalClickThroughs
            - totalAttributedSales14d
            - totalUnitsSold14d
            - totalCommission (需要根据字段名计算)
        """
        all_links = []
        page = 1
        limit = 100
        max_pages = 20  # 防止无限循环
        
        while page <= max_pages:
            logger.info(f"正在获取 Archer 链接数据，第 {page} 页...")
            
            params = {
                "startdate": start_date,
                "enddate": end_date,
                "sort_order": False,  # 降序
                "sort": self.SORT_SALES,  # 按销售额排序
                "minclicks": min_clicks,
                "minsales": 0,
                "limit": limit,
                "page": page
            }
            
            try:
                response = self.archer._get("/link_data", params=params)
                
                # 解析响应结构 - 实际字段：Links_Data（首字母大写）
                links = response.get("Links_Data", []) or response.get("links", []) or []
                
                # 分页信息
                pagination = response.get("pagination_info", {})
                total_pages = pagination.get("total_pages", 1)
                
                if not links:
                    break
                
                all_links.extend(links)
                
                # 检查是否有更多页
                if page >= total_pages:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"获取 Archer 链接数据失败: {e}")
                break
        
        logger.info(f"共获取 {len(all_links)} 条 Archer 链接数据")
        return all_links
    
    def _fetch_archer_all_links(self) -> List[Dict[str, Any]]:
        """
        获取所有 Archer Attribution Links（基本信息）
        用于建立 link_name → 追踪参数的映射
        """
        all_links = []
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
                
                all_links.extend(links)
                
                if len(links) < limit:
                    break
                    
                page += 1
                
            except Exception as e:
                logger.error(f"获取 Archer Attribution Links 失败: {e}")
                break
        
        logger.info(f"共获取 {len(all_links)} 条 Archer Attribution Links")
        return all_links
    
    def calculate(
        self,
        start_date: str,
        end_date: str,
        min_archer_clicks: int = 0,
        output_format: str = "print"
    ) -> ROIReport:
        """
        计算 ROI
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            min_archer_clicks: Archer 数据最少点击过滤
            output_format: 输出格式 ("print", "json", "both")
            
        Returns:
            ROIReport 对象
        """
        start_date = self._parse_date(start_date)
        end_date = self._parse_date(end_date)
        date_range = f"{start_date} ~ {end_date}"
        
        logger.info(f"开始 ROI 计算: {date_range}")
        
        # Step 1: 从 Google Ads 拉取花费数据
        logger.info("=" * 40)
        logger.info("Step 1: 拉取 Google Ads 数据")
        logger.info("=" * 40)
        gads_records = self.gads.fetch_all_customers_ads(
            start_date=start_date,
            end_date=end_date
        )
        
        if not gads_records:
            logger.warning("未从 Google Ads 获取到任何 Amazon 广告数据")
        
        # 建立 Google Ads 记录索引：按 aa_campaignid 为 key
        gads_by_campaign: Dict[str, List[AdRecord]] = {}
        for rec in gads_records:
            key = rec.aa_campaignid or rec.campaign_id
            if key not in gads_by_campaign:
                gads_by_campaign[key] = []
            gads_by_campaign[key].append(rec)
        
        logger.info(f"Google Ads 数据: {len(gads_records)} 条记录, {len(gads_by_campaign)} 个 campaign")
        
        # Step 2: 从 Archer 获取链接数据
        logger.info("=" * 40)
        logger.info("Step 2: 拉取 Archer 佣金数据")
        logger.info("=" * 40)
        
        try:
            archer_data = self._fetch_archer_link_data(
                start_date=start_date,
                end_date=end_date,
                min_clicks=min_archer_clicks
            )
        except Exception as e:
            logger.error(f"Archer 数据拉取失败: {e}")
            archer_data = []
        
        # Step 3: 获取 Archer Attribution Links（用于 link_name 映射）
        archer_links_map: Dict[str, Dict[str, Any]] = {}
        try:
            archer_links = self._fetch_archer_all_links()
            for link in archer_links:
                link_name = link.get("link_name", "")
                if link_name:
                    archer_links_map[link_name] = link
        except Exception as e:
            logger.warning(f"获取 Archer Attribution Links 映射失败: {e}")
        
        # Step 4: 关联数据并计算 ROI
        logger.info("=" * 40)
        logger.info("Step 3: 关联数据并计算 ROI")
        logger.info("=" * 40)
        
        report = ROIReport()
        report.date_range = date_range
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 已知 Archer 数据结构（基于 API 文档）：
        # link_name, asin, totalClickThroughs, totalAttributedSales14d, totalUnitsSold14d
        # commission 需要根据响应确定字段名
        
        for archer_item in archer_data:
            # link_info 包含 link_name 和 asin
            link_info = archer_item.get("link_info", {})
            link_name = link_info.get("link_name", "") or archer_item.get("link_name", "")
            asin = link_info.get("asin", "") or archer_item.get("asin", "")
            
            # commission_amount 是实际字段名（来自 API 响应示例）
            commission = archer_item.get("commission_amount", 0)
            sales = archer_item.get("totalAttributedSales14d", 0)
            units = archer_item.get("totalUnitsSold14d", 0)
            archer_clicks = archer_item.get("totalClickThroughs", 0)
            attributed_purchases = archer_item.get("totalAttributedTotalPurchases14d", 0)
            
            # 从 archer_links_map 获取产品名称和创建时间
            product_name = ""
            created_date = ""
            if link_name in archer_links_map:
                link_data = archer_links_map[link_name]
                product_name = link_data.get("product_name", "")
                created_date = link_data.get("created_date_time", "")[:10] if link_data.get("created_date_time") else ""
                # 存回 roi
            # 建立 ROI 记录
            roi = LinkROI(
                link_name=link_name,
                asin=asin,
                product_name=product_name,
                created_date=created_date,
                archer_clicks=archer_clicks,
                archer_sales=float(sales) if sales else 0.0,
                archer_units=int(units) if units else 0,
                archer_commission=float(commission) if commission else 0.0,
                date_range=date_range
            )
            matched_gads = False
            
            for gads_rec in gads_records:
                # 匹配逻辑1: link_name 包含 campaign_name
                if link_name and gads_rec.campaign_name:
                    if link_name.lower() in gads_rec.campaign_name.lower() or \
                       gads_rec.campaign_name.lower() in link_name.lower():
                        self._attach_gads_record(roi, gads_rec)
                        matched_gads = True
                
                # 匹配逻辑2: ASIN 匹配
                if asin and gads_rec.asin == asin:
                    self._attach_gads_record(roi, gads_rec)
                    matched_gads = True
            
            # 计算衍生指标
            if roi.cost_usd > 0:
                roi.ROAS = roi.archer_sales / roi.cost_usd if roi.cost_usd > 0 else 0
                roi.RPC = roi.archer_sales / roi.clicks if roi.clicks > 0 else 0
                roi.CPA = roi.cost_usd / roi.conversions if roi.conversions > 0 else 0
            
            if roi.archer_sales > 0:
                roi.commission_rate = roi.archer_commission / roi.archer_sales
            
            report.add(roi)
        
        # 输出报告
        if output_format in ("print", "both"):
            report.print_summary()
        
        return report
    
    def _attach_gads_record(self, roi: LinkROI, rec: AdRecord):
        """将 Google Ads 数据附加到 ROI 记录"""
        roi.campaign_id = rec.campaign_id
        roi.campaign_name = rec.campaign_name
        roi.ad_group_id = rec.ad_group_id
        roi.ad_id = rec.ad_id
        roi.clicks += rec.clicks
        roi.impressions += rec.impressions
        roi.cost_usd += rec.cost_usd
        roi.conversions += rec.conversions
