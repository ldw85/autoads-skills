#!/usr/bin/env python3
"""Create roborock Q7 M5+ layered campaign with PAS framework AI generation"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.refined_campaign_creator import RefinedCampaignCreator

# Config
CUSTOMER_ID = "4772859239"
BRAND = "roborock"
PRODUCT_NAME = "roborock Q7 M5+ Robot Vacuum and Mop"
PRODUCT_URL = "https://www.amazon.com/dp/B0DWX69JVG?maas=maas_adg_api_585625124253623110_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB1cdf710570bb6c7fd45bd7cdd390dc24&aa_adgroupid=f9093PPT_bWOMX4ygpUM1i90z8zyiiJWfFBVZ66ZR4ZL7epRdvzye8dLjhIHd4NEnWFE7CdPfEWGnjZ1xfcrzJzms5ytN&aa_creativeid=893f0euqLqfPNbBbMNylbC3qSZxgLwLEpaWT_aLf8izpBFXA_c&th=1"
CAMPAIGN_NAME = "roborock Q7 M5+ - PartnerBoost - US"
PRICE = 249.98
COMMISSION_RATE = 0.13
BUDGET = 20.0
COUNTRY = "US"

PRODUCT_DESCRIPTION = """roborock Q7 M5+ Robot Vacuum and Mop, Upgraded from Q5 Max+, Up to 7-9 Weeks Self-Empty, 10000Pa Suction, Dual Anti-Tangle System for Pet Hair & Carpet, PreciSense LiDAR Navigation, App Control"""

print("=" * 70)
print("创建 roborock Q7 M5+ 精细化分层广告系列 (PAS框架)")
print("=" * 70)

# Initialize creator
creator = RefinedCampaignCreator()

# Use create_layered_campaign which properly uses PAS framework
try:
    result = creator.create_layered_campaign(
        customer_id=CUSTOMER_ID,
        campaign_name=CAMPAIGN_NAME,
        product_url=PRODUCT_URL,
        product_description=PRODUCT_DESCRIPTION,
        brand=BRAND,
        product_name=PRODUCT_NAME,
        price=PRICE,
        commission_rate=COMMISSION_RATE,
        country=COUNTRY,
        budget=BUDGET
    )
    
    print("\n" + "=" * 70)
    print("✅ 创建完成!")
    print("=" * 70)
    
    if result.get('campaign_id'):
        print(f"\n📋 Campaign ID: {result['campaign_id']}")
        print(f"📋 Campaign Name: {CAMPAIGN_NAME}")
        
        print(f"\n📊 广告组:")
        for layer, info in result.get('layers', {}).items():
            print(f"   {layer}: {info.get('name')} ({info.get('keywords_added', 0)} 关键词)")
        
        if result.get('sitelinks_count'):
            print(f"\n📊 Sitelinks: {result['sitelinks_count']} 个")
        if result.get('negative_keywords_count'):
            print(f"📊 否定关键词: {result['negative_keywords_count']} 个")
        
        if result.get('errors'):
            print(f"\n⚠️ 错误:")
            for err in result['errors']:
                print(f"   - {err}")
    else:
        print(f"\n❌ 创建失败: {result.get('errors')}")
    
except Exception as e:
    print(f"\n❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)