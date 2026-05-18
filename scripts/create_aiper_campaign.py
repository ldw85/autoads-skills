#!/usr/bin/env python3
"""Create refined campaign for Aiper Scuba S1"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config

# Config
CUSTOMER_ID = "4772859239"
BRAND = "Aiper Scuba"
PRODUCT_NAME = "Aiper Scuba S1 Robotic Pool Cleaner"
PRODUCT_URL = "https://www.amazon.com/dp/B0FJ818NNZ?maas=maas_adg_api_590892048320336634_static_12_201&ref_=aa_maas&tag=maas&aa_campaignid=PB87d91be16a8fd2a9f3cf7677f11ef384&aa_adgroupid=77c1bhHVGNDx3U_aStqy5msovo5umc8uNUdVUO93hYCubEAAPVqpn6_baZyUcZ7m2_bwxWK0R_ahD3n9UFxe4p0xIpR2&aa_creativeid=3b3a8bRBjNoARwxyVLYPGGnIcF5jJy4sWyICitxU4_agbrrg_c&th=1"
CAMPAIGN_NAME = "Aiper Scuba S1 Pool Cleaner - PartnerBoost - US"
PRICE = 549.98
COMMISSION_RATE = 0.10
BUDGET = 20.0

# Calculate CPC
MAX_CPC = PRICE * COMMISSION_RATE / 50 * 6.9 * 0.9
print(f"📊 CPC 计算: ${PRICE} × {COMMISSION_RATE} / 50 × 6.9 × 0.9 = ${MAX_CPC:.2f}")

app_config = get_config()
client = GoogleAdsClientWrapper(config=app_config.google_ads)

print("\n" + "=" * 70)
print("创建 Aiper Scuba S1 精细化分层广告系列")
print("=" * 70)

# Step 1: Create Campaign
print("\n⏳ Step 1: 创建广告系列...")

try:
    campaign = client.create_campaign(
        name=CAMPAIGN_NAME,
        daily_budget=BUDGET,
        network='SEARCH',
        max_cpc_bid=MAX_CPC
    )
    if campaign:
        campaign_id = campaign.id
        print(f"   ✅ 广告系列创建成功: {campaign_id}")
    else:
        print("   ❌ 广告系列创建失败")
        sys.exit(1)
    
except Exception as e:
    print(f"   ❌ 广告系列创建失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Generate keywords using Google Keyword Planner
print("\n⏳ Step 2: 生成关键词...")

try:
    keywords = client.generate_keyword_ideas(
        customer_id=CUSTOMER_ID,
        url=PRODUCT_URL,
        country='US',
        language='EN'
    )
    print(f"   ✅ 获取到 {len(keywords)} 个关键词")
except Exception as e:
    print(f"   ❌ 关键词生成失败: {e}")
    keywords = []

# Step 3: Create layered ad groups
print("\n⏳ Step 3: 创建分层广告组...")

from src.refined_bid_optimizer import RefinedBidOptimizer, AdContent

optimizer = RefinedBidOptimizer()

# Core terms for pool cleaner
core_terms = ["robotic pool cleaner", "pool cleaner", "pool vacuum robot"]
brand_terms = ["aiper scuba", "aiper"]

# Create result structure for ad group creation
result = {
    'layers': {
        'L1': {'keywords': []},
        'L2': {'keywords': []},
        'L3': {'keywords': []},
        'L5': {'keywords': []}
    },
    'brand': BRAND,
    'core_product_terms': core_terms,
    'max_cpc': MAX_CPC
}

# Classify keywords
for kw in keywords:
    text = kw['text'].lower()
    
    # L1: Brand keywords
    if any(b in text for b in brand_terms):
        result['layers']['L1']['keywords'].append(kw)
    # L2: Core product terms
    elif any(c in text for c in core_terms):
        result['layers']['L2']['keywords'].append(kw)
    # L5: Long-tail (4+ words)
    elif len(text.split()) >= 4:
        result['layers']['L5']['keywords'].append(kw)
    # L3: Generic
    else:
        result['layers']['L3']['keywords'].append(kw)

# Show classification
for layer, data in result['layers'].items():
    print(f"   {layer}: {len(data['keywords'])} 关键词")

print("\n" + "=" * 70)
print(f"✅ 初步完成")
print(f"   Campaign ID: {campaign_id}")
print("=" * 70)
print("\n⚠️ 注意: 广告组结构已准备好，但需要实际调用API创建")
print("   需要完整实现 ad group 创建 + 广告创建 + sitelinks")