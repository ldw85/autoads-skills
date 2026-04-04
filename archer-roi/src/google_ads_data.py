"""
Google Ads 数据拉取模块
=======================
从 Google Ads API 拉取 Amazon 广告的花费数据，
并提取 final_url_suffix 中的追踪参数用于关联 Archer 数据
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


@dataclass
class AdRecord:
    """单条广告记录"""
    customer_id: str = ""     # Google Ads Customer ID
    campaign_id: str = ""
    campaign_name: str = ""
    ad_group_id: str = ""
    ad_group_name: str = ""
    ad_id: str = ""
    final_url: str = ""
    url_suffix: str = ""       # 追踪参数（包含 aa_campaignid 等）
    clicks: int = 0
    impressions: int = 0
    cost: float = 0.0         # 花费（微克朗）
    conversions: float = 0.0
    
    # 从 suffix 解析出的关键字段
    aa_campaignid: str = ""
    aa_adgroupid: str = ""
    aa_creativeid: str = ""
    affiliate_tag: str = ""
    asin: str = ""
    
    # 非构造参数（仅用于引用）
    _initialized: bool = False
    
    def parse_suffix(self):
        """从 url_suffix 中解析出各追踪参数"""
        if not self.url_suffix:
            return
        
        try:
            params = parse_qs(self.url_suffix)
            # parse_qs 会把值变成列表，取第一个
            self.aa_campaignid = params.get("aa_campaignid", [""])[0]
            self.aa_adgroupid = params.get("aa_adgroupid", [""])[0]
            self.aa_creativeid = params.get("aa_creativeid", [""])[0]
            self.affiliate_tag = params.get("tag", [""])[0]
            
            # 尝试从 final_url 提取 ASIN
            if "amazon.com/dp/" in self.final_url:
                parts = self.final_url.split("amazon.com/dp/")[1].split("/")[0].split("?")[0]
                self.asin = parts
        except Exception as e:
            logger.warning(f"解析 url_suffix 失败: {e}")
    
    @property
    def cost_usd(self) -> float:
        """花费金额（美元）"""
        return self.cost / 1_000_000  # Google Ads 使用微货币
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "ad_group_id": self.ad_group_id,
            "ad_id": self.ad_id,
            "asin": self.asin,
            "aa_campaignid": self.aa_campaignid,
            "aa_adgroupid": self.aa_adgroupid,
            "aa_creativeid": self.aa_creativeid,
            "clicks": self.clicks,
            "impressions": self.impressions,
            "cost_usd": round(self.cost_usd, 2),
            "conversions": self.conversions,
            "affiliate_tag": self.affiliate_tag
        }


class GoogleAdsDataFetcher:
    """
    从 Google Ads 拉取 Amazon 广告数据
    
    关联方式：通过 final_url_suffix 中的 aa_campaignid / aa_adgroupid / aa_creativeid
    与 Archer 联盟平台创建的 Attribution Link 进行关联
    """
    
    def __init__(self, google_ads_client):
        """
        Args:
            google_ads_client: google_ads_api 客户端实例
        """
        self._client = google_ads_client
        self._customer_ids = [
            "3674729801",  # 主要账户
            "6052559425",  # yeahpromos 账户
        ]
    
    def fetch_amazon_ads(
        self,
        customer_id: str,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[str]] = None
    ) -> List[AdRecord]:
        """
        拉取指定时间范围内所有 Amazon 广告的花费数据
        
        Args:
            customer_id: Google Ads Customer ID
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            campaign_ids: 可选，只拉取这些 campaign
            
        Returns:
            AdRecord 列表
        """
        logger.info(f"正在拉取 Google Ads 数据: Customer={customer_id}, 日期={start_date}~{end_date}")
        
        # Note: ad.final_url is not accessible in v23, use ad.final_urls (list) and filter in Python
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad.id,
                ad.final_urls,
                ad.final_url_suffix,
                metrics.clicks,
                metrics.impressions,
                metrics.cost_micros,
                metrics.conversions
            FROM ad
            WHERE
                campaign.status = 'ENABLED'
                AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        """

        if campaign_ids:
            campaign_id_list = ", ".join(campaign_ids)
            query += f" AND campaign.id IN ({campaign_id_list})"

        try:
            results = self._client.search(query, customer_id=customer_id)

            records = []
            for row in results:
                # ad.final_urls is a list of strings; filter for amazon.com URLs in Python
                urls = list(row.ad.final_urls) if row.ad.final_urls else []
                amazon_url = next((u for u in urls if 'amazon.com/dp/' in u), None)

                if not amazon_url:
                    continue

                record = AdRecord(
                    customer_id=customer_id,
                    campaign_id=str(row.campaign.id),
                    campaign_name=row.campaign.name,
                    ad_group_id=str(row.ad_group.id),
                    ad_group_name=row.ad_group.name,
                    ad_id=str(row.ad.id),
                    final_url=amazon_url,
                    url_suffix=row.ad.final_url_suffix or "",
                    clicks=row.metrics.clicks,
                    impressions=row.metrics.impressions,
                    cost=row.metrics.cost_micros or 0,
                    conversions=row.metrics.conversions or 0.0
                )
                record.parse_suffix()
                records.append(record)

            logger.info(f"拉取到 {len(records)} 条广告记录")
            return records
            
        except Exception as e:
            logger.error(f"拉取 Google Ads 数据失败: {e}")
            return []
    
    def fetch_all_customers_ads(
        self,
        start_date: str,
        end_date: str,
        campaign_ids: Optional[List[str]] = None
    ) -> List[AdRecord]:
        """
        拉取所有配置账户的 Amazon 广告数据
        
        Returns:
            所有账户的 AdRecord 列表
        """
        all_records = []
        
        for customer_id in self._customer_ids:
            try:
                records = self.fetch_amazon_ads(
                    customer_id=customer_id,
                    start_date=start_date,
                    end_date=end_date,
                    campaign_ids=campaign_ids
                )
                all_records.extend(records)
            except Exception as e:
                logger.warning(f"拉取账户 {customer_id} 失败: {e}")
                continue
        
        return all_records
    
    def group_by_asin(self, records: List[AdRecord]) -> Dict[str, Dict[str, Any]]:
        """
        按 ASIN 汇总广告花费数据
        
        Returns:
            {asin: {"records": [...], "total_cost": float, "total_clicks": int, ...}}
        """
        asin_groups: Dict[str, Dict[str, Any]] = {}
        
        for rec in records:
            if not rec.asin:
                # 尝试用 campaign_id 作为 key
                key = rec.campaign_id
            else:
                key = rec.asin
            
            if key not in asin_groups:
                asin_groups[key] = {
                    "asin": rec.asin,
                    "campaign_id": rec.campaign_id,
                    "campaign_name": rec.campaign_name,
                    "records": [],
                    "total_cost_usd": 0.0,
                    "total_clicks": 0,
                    "total_impressions": 0,
                    "total_conversions": 0.0
                }
            
            asin_groups[key]["records"].append(rec)
            asin_groups[key]["total_cost_usd"] += rec.cost_usd
            asin_groups[key]["total_clicks"] += rec.clicks
            asin_groups[key]["total_impressions"] += rec.impressions
            asin_groups[key]["total_conversions"] += rec.conversions
        
        return asin_groups

    def search_ads_by_asin(self, asins: List[str]) -> Dict[str, List[AdRecord]]:
        """
        按 ASIN 搜索所有账户中的广告（不受时间限制）

        通过三个查询构建 ad→ad_group→campaign 的完整链路：
        1. ad: ad_id + final_urls
        2. ad_group_ad: ad_id → ad_group_id
        3. ad_group: ad_group_id → campaign_id + campaign_name + ad_group_name

        Returns:
            {asin: [AdRecord列表]}  每个 ASIN 对应的广告记录
        """
        asin_to_records: Dict[str, List[AdRecord]] = {asin: [] for asin in asins}

        for customer_id in self._customer_ids:
            try:
                # Step 1: Get all ads with their final_urls
                ad_url_map: Dict[int, List[str]] = {}  # ad_id → list of URLs
                query1 = "SELECT ad.id, ad.final_urls FROM ad LIMIT 1000"
                for row in self._client.search(query1, customer_id=customer_id):
                    urls = list(row.ad.final_urls) if row.ad.final_urls else []
                    ad_url_map[row.ad.id] = urls

                # Step 2: Get ad → ad_group mapping
                ad_to_ag: Dict[int, str] = {}  # ad_id → ad_group resource name
                query2 = "SELECT ad_group_ad.ad.id, ad_group_ad.ad_group FROM ad_group_ad LIMIT 1000"
                for row in self._client.search(query2, customer_id=customer_id):
                    ad_to_ag[row.ad_group_ad.ad.id] = row.ad_group_ad.ad_group

                # Step 3: Get ad_group → campaign + names
                ag_info: Dict[int, Dict[str, str]] = {}  # ad_group_id → {campaign, campaign_name, ad_group_name}
                query3 = "SELECT ad_group.id, ad_group.campaign, ad_group.name FROM ad_group LIMIT 1000"
                for row in self._client.search(query3, customer_id=customer_id):
                    ag_id = row.ad_group.id
                    camp_res = row.ad_group.campaign
                    camp_id = camp_res.split('/')[-1] if camp_res else ''
                    ag_info[ag_id] = {
                        'campaign_id': camp_id,
                        'ad_group_name': row.ad_group.name or ''
                    }

                # Step 4: Build records for matching ASINs
                for ad_id, urls in ad_url_map.items():
                    for url in urls:
                        if 'amazon.com/dp/' not in url:
                            continue
                        asin = url.split('amazon.com/dp/')[1].split('/')[0].split('?')[0]
                        if asin not in asin_to_records:
                            continue

                        ad_group_res = ad_to_ag.get(ad_id)
                        if ad_group_res:
                            ag_id = int(ad_group_res.split('/')[-1])
                            info = ag_info.get(ag_id, {})
                            camp_id = info.get('campaign_id', '')
                            ag_name = info.get('ad_group_name', '')
                        else:
                            camp_id = ''
                            ag_name = ''

                        record = AdRecord(
                            customer_id=customer_id,
                            campaign_id=camp_id,
                            campaign_name='',  # will be resolved separately
                            ad_group_id=str(ag_id) if ad_group_res else '',
                            ad_group_name=ag_name,
                            ad_id=str(ad_id),
                            final_url=url,
                            url_suffix="",
                            clicks=0,
                            impressions=0,
                            cost=0.0,
                            conversions=0.0
                        )
                        asin_to_records[asin].append(record)

            except Exception as e:
                logger.warning(f"搜索账户 {customer_id} 广告失败: {e}")
                continue

        return asin_to_records
