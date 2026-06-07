#!/usr/bin/env python3
"""
修复现有广告系列的广告素材
=========================
针对 Campaign 23868234951 (Momcozy Baby Monitor)
1. 获取广告组
2. 预校验并去重素材
3. 创建RSA广告
"""

import sys
import os
import logging
import json

# Setup paths
AUTOADS_DIR = '/root/.openclaw/workspace/autoads'
sys.path.insert(0, AUTOADS_DIR)

from src.google_ads_client import GoogleAdsClientWrapper
from src.ad_researcher import AdResearcher
from src.ad_prevalidator import validate_ad_creative
from src.refined_campaign_creator import RefinedCampaignCreator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
CUSTOMER_ID = '6052559425'
CAMPAIGN_ID = '23868234951'
BRAND = 'Momcozy'
PRODUCT_NAME = 'Smart WiFi Baby Monitor with Camera and Audio'
FINAL_URL = 'https://www.amazon.com/dp/B0DQXPWHSK'
URL_SUFFIX = 'maas=maas_adg_api_578435546800514248_static_9_129&ref_=aa_maas&tag=maas&aa_campaignid=lv_Qdr2IHhjDPl2LcCV8q&aa_adgroupid=lv_ciorfyK3auf36BzGKU&aa_creativeid=lv_x0vjm9nHCN9nq1XAJs'

def get_ad_groups(client, customer_id, campaign_id):
    query = f"""
        SELECT ad_group.id, ad_group.name 
        FROM ad_group 
        WHERE campaign.id = {campaign_id}
    """
    results = client.search(query, customer_id=customer_id)
    return [{'id': row.ad_group.id, 'name': row.ad_group.name} for row in results]

def main():
    client = GoogleAdsClientWrapper()
    creator = RefinedCampaignCreator()
    researcher = AdResearcher()
    
    # 1. 获取广告组
    ad_groups = get_ad_groups(client, CUSTOMER_ID, CAMPAIGN_ID)
    if not ad_groups:
        logger.error("未找到广告组")
        return
    
    logger.info(f"找到 {len(ad_groups)} 个广告组")
    
    # 2. 生成原始素材
    logger.info("正在生成广告素材...")
    ad_creative = researcher.research(
        product_description="Momcozy Smart WiFi Baby Monitor BM04 features: 5-inch 1080P screen, WiFi connectivity, motion & cry detection, safe fence alert, night vision, 5000mAh battery, 2-way talk, photo & video recording.",
        product_url=FINAL_URL,
        brand=BRAND,
        product_name=PRODUCT_NAME,
        price=169.99,
        commission_rate=0.135
    )
    
    # 3. 预校验（包含去重和语义精简）
    logger.info("执行素材预校验...")
    ad_creative = validate_ad_creative(ad_creative)
    
    # 4. 修复RSA广告
    for ag in ad_groups:
        logger.info(f"正在为广告组 {ag['name']} ({ag['id']}) 创建RSA广告...")
        try:
            ad_id = creator.create_rsa(
                customer_id=CUSTOMER_ID,
                ad_group_id=ag['id'],
                headlines=ad_creative['headlines'],
                descriptions=ad_creative['descriptions'],
                final_url=FINAL_URL,
                url_suffix=URL_SUFFIX
            )
            logger.info(f"✅ 成功创建广告: {ad_id}")
        except Exception as e:
            logger.error(f"❌ 创建失败: {e}")

if __name__ == "__main__":
    main()