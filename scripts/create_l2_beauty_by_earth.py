#!/usr/bin/env python3
"""Create L2 Core ad group for Beauty by Earth"""

import sys
import os
os.chdir('/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper, get_config

# Campaign info
CAMPAIGN_ID = "23720243976"
CUSTOMER_ID = "6052559425"

# Core terms for this product - these go to L2
CORE_TERMS = ["self tanner", "self tanning", "self tanning lotion"]
BRAND = "Beauty by Earth"
PRODUCT_URL = "https://www.amazon.com/dp/B00L2PB3BW"

app_config = get_config()
client = GoogleAdsClientWrapper(config=app_config.google_ads)

print("=" * 70)
print("为广告系列 23720243976 创建 L2 Core 广告组")
print("=" * 70)

# Step 1: Generate all keywords via Google Keyword Planner
print("\n⏳ Step 1: 调用 Google 关键词工具...")
try:
    keywords = client.generate_keyword_ideas(
        customer_id=CUSTOMER_ID,
        url=PRODUCT_URL,
        country='US',
        language='EN'
    )
    print(f"✅ 获取到 {len(keywords)} 个关键词")
except Exception as e:
    print(f"❌ Google 关键词工具失败: {e}")
    sys.exit(1)

# Step 2: Filter keywords for L2 (containing core terms)
l2_keywords = []
for kw in keywords:
    text_lower = kw['text'].lower()
    for core_term in CORE_TERMS:
        if core_term in text_lower:
            l2_keywords.append(kw)
            break

print(f"\n📊 L2 关键词 (包含核心产品词 'self tanner' 等): {len(l2_keywords)}")
for kw in l2_keywords[:15]:
    print(f"  • {kw['text']}")
if len(l2_keywords) > 15:
    print(f"  ... 还有 {len(l2_keywords) - 15} 个")

# Step 3: Check if L2 ad group already exists
print("\n⏳ Step 2: 检查 L2 广告组是否已存在...")
l2_ad_group_id = None

query = f"""
SELECT ad_group.id, ad_group.name
FROM ad_group
WHERE ad_group.campaign = 'customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}'
"""
try:
    service = client.client.get_service("GoogleAdsService")
    response = service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        if 'L2' in row.ad_group.name or 'Core' in row.ad_group.name:
            l2_ad_group_id = row.ad_group.id
            print(f"   ⚠️ L2 广告组已存在: {row.ad_group.name} (ID: {l2_ad_group_id})")
            break
except Exception as e:
    print(f"   警告: {e}")

if l2_ad_group_id:
    print("❌ L2 广告组已存在，无需创建")
    sys.exit(0)

# Step 4: Get base CPC from existing ad group
print("\n⏳ Step 3: 获取基准 CPC...")
cpc_query = f"""
SELECT ad_group.cpc_bid_micros
FROM ad_group
WHERE ad_group.id = 195257783023
"""
try:
    response = service.search(customer_id=CUSTOMER_ID, query=cpc_query)
    for row in response:
        base_cpc = row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else 0.62
        print(f"   基准 CPC: ${base_cpc:.2f}")
except:
    base_cpc = 0.62
    print(f"   使用默认 CPC: ${base_cpc:.2f}")

# Step 5: Create L2 Core ad group
print("\n⏳ Step 4: 创建 L2 Core 广告组...")
try:
    ad_group_service = client.client.get_service("AdGroupService")
    
    operation = client.client.get_type("AdGroupOperation")
    ad_group = operation.create
    ad_group.name = f"{BRAND}_Core"
    ad_group.campaign = f"customers/{CUSTOMER_ID}/campaigns/{CAMPAIGN_ID}"
    ad_group.status = client.client.get_type("AdGroupStatusEnum").AdGroupStatus.ENABLED
    ad_group.cpc_bid_micros = int(base_cpc * 1_000_000)  # L2 is 100% of base
    
    response = ad_group_service.mutate_ad_groups(
        customer_id=CUSTOMER_ID,
        operations=[operation]
    )
    
    l2_ad_group_id = response.results[0].resource_name.split('/')[-1]
    print(f"✅ 创建广告组: {l2_ad_group_id} (Beauty by Earth_Core)")
    
except Exception as e:
    print(f"❌ 创建广告组失败: {e}")
    sys.exit(1)

# Step 6: Add keywords to L2 ad group
print(f"\n⏳ Step 5: 添加 {len(l2_keywords)} 个关键词到 L2 广告组...")

try:
    criterion_service = client.client.get_service("AdGroupCriterionService")
    
    # Batch keywords to avoid overload
    batch_size = 10
    total_added = 0
    
    for i in range(0, len(l2_keywords), batch_size):
        batch = l2_keywords[i:i+batch_size]
        operations = []
        
        for kw in batch:
            op = client.client.get_type("AdGroupCriterionOperation")
            criterion = op.create
            criterion.ad_group = f"customers/{CUSTOMER_ID}/adGroups/{l2_ad_group_id}"
            criterion.keyword.text = kw['text']
            criterion.keyword.match_type = client.client.get_type("KeywordMatchTypeEnum").KeywordMatchType.PHRASE
            criterion.negative = False
            criterion.cpc_bid_micros = int(base_cpc * 1_000_000)
            
            operations.append(op)
        
        response = criterion_service.mutate_ad_group_criteria(
            customer_id=CUSTOMER_ID,
            operations=operations
        )
        total_added += len(batch)
        print(f"   已添加 {total_added}/{len(l2_keywords)}")
    
    print(f"\n✅ 成功添加 {total_added} 个关键词到 L2 广告组")
    
except Exception as e:
    print(f"❌ 添加关键词失败: {e}")

print("\n" + "=" * 70)
print("✅ 完成!")
print("=" * 70)
print(f"\n📋 创建结果:")
print(f"   广告系列: {CAMPAIGN_ID}")
print(f"   L2 广告组 ID: {l2_ad_group_id}")
print(f"   L2 广告组名称: Beauty by Earth_Core")
print(f"   添加关键词: {total_added}")
print(f"\n⚠️ 重要: 请将 L2 广告组出价策略切换为 Manual CPC")