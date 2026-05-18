#!/usr/bin/env python3
"""Create Aiper Scuba S1 layered campaign with fixed campaign creation"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config
from src.refined_campaign_creator import RefinedCampaignCreator
from src.refined_bid_optimizer import AdContent

# Config
CUSTOMER_ID = "4772859239"
BRAND = "Aiper Scuba"
PRODUCT_NAME = "Aiper Scuba S1 Robotic Pool Cleaner"
PRODUCT_URL = "https://www.amazon.com/dp/B0FJ818NNZ?maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICcitxU4_agbrrg_c&th=1"
CAMPAIGN_NAME = "Aiper Scuba S1 Pool Cleaner - PartnerBoost - US"
PRICE = 549.98
COMMISSION_RATE = 0.10
BUDGET = 20.0

# URL parsing
final_url = "https://www.amazon.com/dp/B0FJ818NNZ"
url_suffix = "maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICcitxU4_agbrrg_c&th=1"

# Core terms for classification
CORE_TERMS = ["robotic pool cleaner", "pool cleaner robot", "pool vacuum robot", "automatic pool cleaner"]
BRAND_TERMS = ["aiper"]

print("=" * 70)
print("创建 Aiper Scuba S1 精细化分层广告系列")
print("=" * 70)
print(f"\n📋 Customer ID: {CUSTOMER_ID}")
print(f"📋 Brand: {BRAND}")
print(f"📋 Product: {PRODUCT_NAME}")
print(f"📋 Price: ${PRICE}")
print(f"📋 Commission: {COMMISSION_RATE * 100}%")

# Calculate CPC
MAX_CPC = PRICE * COMMISSION_RATE / 50 * 6.9 * 0.9
print(f"📊 Calculated CPC: ${MAX_CPC:.2f}")

# Initialize creator
creator = RefinedCampaignCreator()

# Step 1: Create campaign
print("\n⏳ Step 1: 创建广告系列...")
try:
    campaign_id = creator.create_campaign(
        customer_id=CUSTOMER_ID,
        campaign_name=CAMPAIGN_NAME,
        budget=BUDGET,
        max_cpc=MAX_CPC,
        country='US'
    )
    print(f"   ✅ Campaign ID: {campaign_id}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Get keywords
print("\n⏳ Step 2: 生成关键词...")
client = GoogleAdsClientWrapper(config=get_config().google_ads)
try:
    keywords = client.generate_keyword_ideas(
        customer_id=CUSTOMER_ID,
        url=PRODUCT_URL,
        country='US',
        language='EN'
    )
    print(f"   ✅ 获取到 {len(keywords)} 个关键词")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    keywords = []

# Step 3: Classify keywords
print("\n⏳ Step 3: 关键词分层...")
classified = {'L1': [], 'L2': [], 'L3': [], 'L5': []}
for kw in keywords:
    text = kw['text'].lower()
    if any(b in text for b in BRAND_TERMS):
        classified['L1'].append(kw['text'])
    elif any(c in text for c in CORE_TERMS):
        classified['L2'].append(kw['text'])
    elif len(text.split()) >= 5:
        classified['L5'].append(kw['text'])
    else:
        classified['L3'].append(kw['text'])

for layer, kws in classified.items():
    print(f"   {layer}: {len(kws)} 关键词")

# Step 4: Create ad groups and add keywords
print("\n⏳ Step 4: 创建广告组...")
ad_groups = {}
LAYER_CONFIG = {
    'L1': {'name': f'{BRAND}_Brand', 'bid_mult': 0.80, 'match': 'PHRASE'},
    'L2': {'name': f'{BRAND}_Core', 'bid_mult': 1.00, 'match': 'PHRASE'},
    'L3': {'name': f'{BRAND}_Generic', 'bid_mult': 0.80, 'match': 'PHRASE'},
    'L5': {'name': f'{BRAND}_LongTail', 'bid_mult': 0.70, 'match': 'PHRASE'},
}

for layer, config in LAYER_CONFIG.items():
    bid = MAX_CPC * config['bid_mult']
    try:
        ad_group_id = creator.create_ad_group(
            customer_id=CUSTOMER_ID,
            campaign_id=campaign_id,
            ad_group_name=config['name'],
            cpc_bid=bid
        )
        ad_groups[layer] = {
            'id': ad_group_id,
            'name': config['name'],
            'keywords': classified[layer],
            'match': config['match']
        }
        print(f"   ✅ {layer}: {config['name']} (ID: {ad_group_id})")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")

# Step 5: Add keywords
print("\n⏳ Step 5: 添加关键词...")
for layer, info in ad_groups.items():
    if not info['keywords']:
        continue
    try:
        count = creator.add_keywords(
            customer_id=CUSTOMER_ID,
            ad_group_id=info['id'],
            keywords=info['keywords'],
            match_type=info['match']
        )
        print(f"   ✅ {layer}: 添加 {count} 个关键词")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")

# Step 6: Generate and create ads
print("\n⏳ Step 6: 生成广告素材...")
headlines = [
    "Aiper Scuba S1 Pool Cleaner",
    "Robotic Pool Cleaner Sale",
    "Best Robotic Pool Vacuum",
    "Automatic Pool Cleaner",
    "Wall & Waterline Cleaning",
    "180-Min Battery Life",
    "Smart App Control",
    "Dual Filtration System",
    "Pool Vacuum Robot",
    "Easy Pool Maintenance",
    "OTA Software Updates",
    "2-Year Warranty",
    "Clean Pool Guaranteed",
    "Pool Cleaning Robot",
    "Smart Navigation System"
]

descriptions = [
    "Aiper Scuba S1 robotic pool cleaner with 180-min battery life. Wall & waterline cleaning, dual filtration, smart app control. 2-year warranty.",
    "Automatic robotic pool vacuum with intelligent navigation. Dual filtration captures fine dust and debris. Easy app control and OTA updates.",
    "Professional pool cleaning robot with 11 high-precision sensors. Adapts to any pool shape. Wall, waterline, and floor cleaning in one device."
]

ad_content = AdContent(
    brand=BRAND,
    core_product_terms=CORE_TERMS,
    headlines=headlines,
    descriptions=descriptions,
    final_url=final_url,
    url_suffix=url_suffix,
    sitelinks=[]
)

# Step 7: Create ads for each ad group
print("\n⏳ Step 7: 创建广告...")
for layer, info in ad_groups.items():
    if not headlines:
        continue
    try:
        ad_id = creator.create_rsa(
            customer_id=CUSTOMER_ID,
            ad_group_id=info['id'],
            headlines=headlines,
            descriptions=descriptions,
            final_url=final_url,
            url_suffix=url_suffix
        )
        if ad_id:
            print(f"   ✅ {layer}: 广告创建成功 (ID: {ad_id})")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("✅ 创建完成!")
print("=" * 70)
print(f"\n📋 Campaign ID: {campaign_id}")
print(f"📋 Campaign Name: {CAMPAIGN_NAME}")
print(f"\n📊 广告组:")
for layer, info in ad_groups.items():
    print(f"   {layer}: {info['name']} ({len(info['keywords'])} 关键词)")
print("\n⚠️ 重要提醒:")
print("   1. 请在 Google Ads 界面检查广告系列状态")
print("   2. 确认出价策略为 Manual CPC")
print("   3. 启用广告系列后开始投放")