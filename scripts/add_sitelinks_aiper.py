#!/usr/bin/env python3
"""Add sitelinks to campaign 23846856186 with URL suffix"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config
from src.refined_campaign_creator import RefinedCampaignCreator

CAMPAIGN_ID = "23846856186"
CUSTOMER_ID = "4772859239"

# URL info
FINAL_URL = "https://www.amazon.com/dp/B0FJ818NNZ"
URL_SUFFIX = "maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICcitxU4_agbrrg_c&th=1"

# Sitelinks for Aiper Scuba S1 Pool Cleaner
SITELINKS = [
    {"link_text": "Customer Reviews", "description1": "Read Testimonials", "description2": "Proven Quality"},
    {"link_text": "Shop Now", "description1": "Best Price Guaranteed", "description2": "Limited Stock"},
    {"link_text": "2-Year Warranty", "description1": "Full Coverage", "description2": "Hassle-Free"},
    {"link_text": "Free Shipping", "description1": "On All Orders", "description2": "Fast Delivery"},
    {"link_text": "Wall Cleaning", "description1": "Wall & Waterline", "description2": "Complete Coverage"},
    {"link_text": "App Control", "description1": "Smart App Control", "description2": "OTA Updates"},
]

print("=" * 70)
print("为广告系列 23846856186 添加 Sitelinks")
print("=" * 70)
print(f"\n📋 Campaign ID: {CAMPAIGN_ID}")
print(f"📋 Customer ID: {CUSTOMER_ID}")
print(f"📋 Final URL: {FINAL_URL}")
print(f"📋 URL Suffix: {URL_SUFFIX[:50]}...")

creator = RefinedCampaignCreator()

print(f"\n⏳ 创建 {len(SITELINKS)} 个 Sitelinks...")
try:
    asset_ids = creator.create_sitelinks(
        customer_id=CUSTOMER_ID,
        campaign_id=CAMPAIGN_ID,
        sitelinks=SITELINKS,
        final_url=FINAL_URL,
        url_suffix=URL_SUFFIX
    )
    
    print(f"\n✅ 成功创建 {len(asset_ids)} 个 Sitelinks!")
    
    print("\n📋 Sitelinks 列表:")
    for i, sl in enumerate(SITELINKS, 1):
        print(f"   {i}. {sl['link_text']}: {sl['description1']} | {sl['description2']}")
    
except Exception as e:
    print(f"\n❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)