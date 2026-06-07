#!/bin/bash
# 修复 Momcozy Campaign 23868234951 的广告素材
# ===============================================

cd /root/.openclaw/workspace/skills/refined-campaign-new

python3 - <<'PYEOF'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper
from src.ad_researcher import AdResearcher
from src.ad_prevalidator import validate_ad_creative
from src.refined_campaign_creator import RefinedCampaignCreator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

CUSTOMER_ID = '6052559425'
CAMPAIGN_ID = '23868234951'

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
    
    ad_groups = get_ad_groups(client, CUSTOMER_ID, CAMPAIGN_ID)
    if not ad_groups:
        logger.error("未找到广告组")
        return
    
    logger.info(f"找到 {len(ad_groups)} 个广告组: {[ag['name'] for ag in ad_groups]}")
    logger.info("正在生成广告素材...")
    
    ad_creative = researcher.research(
        product_description="""
            Momcozy Smart WiFi Baby Monitor BM04 features:
            5-inch 1080P screen with wall mount
            Motion & Cry Detection, Safe Fence alert
            Clear Night Vision, 5000mAh Battery
            2-Way Talk, Photo & Video Recording
            WiFi/NON-WiFi dual connection
            Supports up to 20 family members
        """.replace('\n', ' ').replace('  ', ' '),
        product_url="https://www.amazon.com/dp/B0DQXPWHSK",
        brand_name="Momcozy",
        features="5-inch 1080P screen, WiFi, motion detection, cry detection, night vision, 5000mAh battery, 2-way talk",
        customer_id=CUSTOMER_ID,
        discount_info={'price': 169.99, 'original_price': 199.99, 'discount_percentage': 15}
    )
    
    logger.info(f"Research complete: headlines={len(ad_creative.headlines)}, descriptions={len(ad_creative.descriptions)}")
    
    # 转换为字典格式
    ad_creative_dict = {
        'headlines': ad_creative.headlines,
        'descriptions': ad_creative.descriptions
    }
    
    # 预校验
    logger.info("执行素材预校验...")
    ad_creative_dict = validate_ad_creative(ad_creative_dict)
    logger.info(f"预校验后: {len(ad_creative_dict['headlines'])} headlines, {len(ad_creative_dict['descriptions'])} descriptions")
    
    # 创建RSA
    for ag in ad_groups:
        logger.info(f"正在为 {ag['name']} ({ag['id']}) 创建RSA...")
        try:
            ad_id = creator.create_rsa(
                customer_id=CUSTOMER_ID,
                ad_group_id=ag['id'],
                headlines=ad_creative_dict['headlines'],
                descriptions=ad_creative_dict['descriptions'],
                final_url="https://www.amazon.com/dp/B0DQXPWHSK",
                url_suffix="maas=maas_adg_api_578435546800514248_static_9_129&ref_=aa_maas&tag=maas&aa_campaignid=lv_Qdr2IHhjDPl2LcCV8q&aa_adgroupid=lv_ciorfyK3auf36BzGKU&aa_creativeid=lv_x0vjm9nHCN9nq1XAJs"
            )
            logger.info(f"✅ 成功: {ag['name']} - Ad ID {ad_id}")
        except Exception as e:
            logger.error(f"❌ 失败: {ag['name']} - {e}")

if __name__ == "__main__":
    main()
PYEOF

echo "Exit code: $?"