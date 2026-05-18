#!/usr/bin/env python3
"""Complete creation of Aiper Scuba S1 layered campaign"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config
from src.ad_researcher import AdResearcher
from src.refined_bid_optimizer import RefinedBidOptimizer, AdContent

# Config
CUSTOMER_ID = "4772859239"
CAMPAIGN_ID = "23846833146"
BRAND = "Aiper Scuba"
PRODUCT_NAME = "Aiper Scuba S1 Robotic Pool Cleaner"
PRODUCT_URL = "https://www.amazon.com/dp/B0FJ818NNZ?maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICitxU4_agbrrg_c&th=1"
PRICE = 549.98
COMMISSION_RATE = 0.10
BUDGET = 20.0
MAX_CPC = 6.83

# Extract URL suffix
final_url = "https://www.amazon.com/dp/B0FJ818NNZ"
url_suffix = "maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICitxU4_agbrrg_c&th=1"

app_config = get_config()
client = GoogleAdsClientWrapper(config=app_config.google_ads)
optimizer = RefinedBidOptimizer()

print("\n" + "=" * 70)
print("Aiper Scuba S1 精细化广告系列创建")
print("=" * 70)

# Step 1: Generate ad creative with AI
print("\n⏳ Step 1: 生成广告素材...")

product_description = """Aiper Scuba S1 Robotic Pool Cleaner
- Wall & Waterline Cleaning
- Dual Filtration System
- Extended 180-Min Battery Life  
- Smarter Navigation with High-Precision Sensors
- App Support & OTA Upgrade"""

researcher = AdResearcher()
try:
    ad_result = researcher.research(
        product_description=product_description,
        product_url=PRODUCT_URL,
        brand_name=BRAND,
        features=PRODUCT_NAME,
        customer_id=None
    )
    headlines = ad_result.get('headlines', [])
    descriptions = ad_result.get('descriptions', [])
    print(f"   ✅ Headlines: {len(headlines)}")
    print(f"   ✅ Descriptions: {len(descriptions)}")
except Exception as e:
    print(f"   ⚠️ AI生成失败: {e}")
    headlines = []
    descriptions = []

# Step 2: Generate keywords
print("\n⏳ Step 2: 生成关键词...")
keywords = client.generate_keyword_ideas(
    customer_id=CUSTOMER_ID,
    url=PRODUCT_URL,
    country='US',
    language='EN'
)
print(f"   ✅ 获取到 {len(keywords)} 个关键词")

# Step 3: Classify keywords into layers
print("\n⏳ Step 3: 关键词分层...")

core_terms = ["robotic pool cleaner", "pool cleaner", "pool vacuum robot", "pool vacuum"]
brand_terms = ["aiper"]

classified = {'L1': [], 'L2': [], 'L3': [], 'L5': []}
for kw in keywords:
    text = kw['text'].lower()
    if any(b in text for b in brand_terms):
        classified['L1'].append(kw)
    elif any(c in text for c in core_terms):
        classified['L2'].append(kw)
    elif len(text.split()) >= 4:
        classified['L5'].append(kw)
    else:
        classified['L3'].append(kw)

for layer, kws in classified.items():
    print(f"   {layer}: {len(kws)} 关键词")

# Step 4: Create ad groups and add content
print("\n⏳ Step 4: 创建广告组...")

LAYER_CONFIG = {
    'L1': {'name': f'{BRAND}_Brand', 'bid_mult': 0.80, 'match': 'PHRASE'},
    'L2': {'name': f'{BRAND}_Core', 'bid_mult': 1.00, 'match': 'PHRASE'},
    'L3': {'name': f'{BRAND}_Generic', 'bid_mult': 0.80, 'match': 'PHRASE'},
    'L5': {'name': f'{BRAND}_LongTail', 'bid_mult': 0.70, 'match': 'PHRASE'},
}

ad_content = AdContent(
    brand=BRAND,
    core_product_terms=core_terms,
    headlines=headlines[:15] if headlines else [],
    descriptions=descriptions[:4] if descriptions else [],
    final_url=final_url,
    url_suffix=url_suffix,
    sitelinks=[]
)

created_groups = {}
for layer, config in LAYER_CONFIG.items():
    try:
        bid = MAX_CPC * config['bid_mult']
        ag = client.create_ad_group(
            campaign_id=CAMPAIGN_ID,
            name=config['name'],
            cpc_bid=bid
        )
        if ag:
            created_groups[layer] = {
                'id': ag.id,
                'name': config['name'],
                'keywords': classified[layer]
            }
            print(f"   ✅ {layer}: {config['name']} (ID: {ag.id})")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")

# Step 5: Add keywords to ad groups
print("\n⏳ Step 5: 添加关键词...")

for layer, info in created_groups.items():
    if not info['keywords']:
        continue
    try:
        count = optimizer.add_keywords_to_ad_group(
            customer_id=CUSTOMER_ID,
            ad_group_id=info['id'],
            keywords=info['keywords'],
            match_type=LAYER_CONFIG[layer]['match']
        )
        print(f"   ✅ {layer}: 添加 {count} 个关键词")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")

# Step 6: Create ads
print("\n⏳ Step 6: 创建广告...")

for layer, info in created_groups.items():
    if not headlines:
        continue
    try:
        ad_id = optimizer._create_ad_for_ad_group(
            customer_id=CUSTOMER_ID,
            ad_group_id=info['id'],
            ad_content=ad_content
        )
        if ad_id:
            print(f"   ✅ {layer}: 广告创建成功")
    except Exception as e:
        print(f"   ❌ {layer}: {e}")

# Summary
print("\n" + "=" * 70)
print("✅ 创建完成!")
print("=" * 70)
print(f"\n📋 Campaign ID: {CAMPAIGN_ID}")
print(f"📋 广告系列: Aiper Scuba S1 Pool Cleaner - PartnerBoost - US")
for layer, info in created_groups.items():
    print(f"   {layer}: {info['name']} ({len(info['keywords'])} 关键词)")
print("\n⚠️ 重要提醒:")
print("   1. 请检查并切换出价策略为 Manual CPC")
print("   2. 检查广告组状态是否为启用")