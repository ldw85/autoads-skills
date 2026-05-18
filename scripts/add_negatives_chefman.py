#!/usr/bin/env python3
"""Add negative keywords to campaign 23728136579 (Chefman Air Fryer)"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config

# Campaign info
CAMPAIGN_ID = "23728136579"
CUSTOMER_ID = "6052559425"

# Negative keywords categorized
negatives_to_add = []

# PHRASE - 替代产品/配件类
phrase_negatives = [
    # 替代电器
    "deep fryer",
    "convection oven",
    "toaster oven",
    "rotisserie",
    "dutch oven",
    # 配件类
    "air fryer accessory",
    "air fryer liner",
    "air fryer recipe book",
    "cast iron skillet",
    "frying oil",
]

# BROAD - 非购买意图
broad_negatives = [
    # 研究意图
    "how to use",
    "how to install",
    "DIY",
    "repair guide",
    # 非购买行为
    "refurbished",
    "open box",
    "second hand",
    "wholesale",
]

# Create categorized negatives
for neg in phrase_negatives:
    negatives_to_add.append(type('CategorizedNegative', (), {'keyword': neg, 'category': 'category', 'match_type': 'PHRASE'})())

for neg in broad_negatives:
    negatives_to_add.append(type('CategorizedNegative', (), {'keyword': neg, 'category': 'intent', 'match_type': 'BROAD'})())

print("=" * 70)
print("添加否定关键词到广告系列 23728136579")
print("=" * 70)
print(f"\n📋 Campaign ID: {CAMPAIGN_ID}")
print(f"📋 Customer ID: {CUSTOMER_ID}")
print(f"\n📊 总计: {len(negatives_to_add)} 个否定关键词")
print(f"   - PHRASE: {len(phrase_negatives)}")
print(f"   - BROAD: {len(broad_negatives)}")

# Connect to Google Ads
app_config = get_config()
client = GoogleAdsClientWrapper(config=app_config.google_ads)
if not client.client:
    print("\n❌ 错误: 无法连接到Google Ads API")
    sys.exit(1)

# Get campaign info first
query = f"""
SELECT campaign.id, campaign.name, campaign.status
FROM campaign
WHERE campaign.id = {CAMPAIGN_ID}
"""
try:
    service = client.client.get_service("GoogleAdsService")
    response = service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        print(f"\n📌 广告系列名称: {row.campaign.name}")
        status_map = {1: "启用", 2: "暂停"}
        print(f"📌 当前状态: {status_map.get(row.campaign.status, '未知')}")
except Exception as e:
    print(f"⚠️ 无法获取广告系列信息: {e}")

# Add negative keywords
print("\n⏳ 正在添加否定关键词...")
try:
    criterion_service = client.client.get_service("CampaignCriterionService")
    mt_enum = client.client.get_type("KeywordMatchTypeEnum").KeywordMatchType
    
    # Group by match type
    by_match_type = {}
    for cat_neg in negatives_to_add:
        if cat_neg.match_type not in by_match_type:
            by_match_type[cat_neg.match_type] = []
        by_match_type[cat_neg.match_type].append(cat_neg.keyword)
    
    total_created = 0
    for match_type, keywords in by_match_type.items():
        if match_type == "EXACT":
            mt = mt_enum.EXACT
        elif match_type == "PHRASE":
            mt = mt_enum.PHRASE
        else:
            mt = mt_enum.BROAD
        
        for keyword in keywords:
            operation = client.client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}"
            criterion.keyword.text = keyword
            criterion.keyword.match_type = mt
            criterion.negative = True
            
            criterion_service.mutate_campaign_criteria(
                customer_id=CUSTOMER_ID,
                operations=[operation]
            )
            total_created += 1
    
    print(f"\n✅ 成功添加 {total_created} 个否定关键词!")
    print("\n📋 PHRASE 匹配 (替代产品/配件):")
    for neg in phrase_negatives:
        print(f"   • {neg}")
    print("\n📋 BROAD 匹配 (非购买意图):")
    for neg in broad_negatives:
        print(f"   • {neg}")
        
except Exception as e:
    print(f"\n❌ 添加失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)