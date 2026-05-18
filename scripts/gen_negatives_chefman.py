#!/usr/bin/env python3
"""Generate negative keywords for Chefman Air Fryer 8 Qt"""

import importlib.util
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

# Load the negative keyword generator module
module_path = '/root/.openclaw/workspace/autoads/src/negative_keyword_generator.py'
spec = importlib.util.spec_from_file_location("negative_keyword_generator", module_path)
neg_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(neg_module)

NegativeKeywordGenerator = neg_module.NegativeKeywordGenerator

# Product info
product_name = "Chefman Air Fryer 8 Qt"
product_type = "air fryer"
brand = "Chefman"
features = [
    "8 quart", "XL nonstick basket", "dishwasher safe", 
    "stainless steel", "450°F", "turbofry", "bake", "dehydrate", "frozen"
]
category = "kitchen appliance"

# Generate negatives with AI
gen = NegativeKeywordGenerator()
result = gen.generate(
    product_name=product_name,
    category=category,
    brand=brand,
    features=features,
    product_type=product_type,
    use_ai=True,
    ai_product_description="Chefman TurboFry 4-in-1 Air Fryer 8 Qt with 450°F Hi-Fry option. Functions: Bake, Dehydrate, Frozen cooking. Features: XL Nonstick Dishwasher-Safe Basket, Stainless Steel exterior. Perfect for family meals, crispy results without oil."
)

# Group by match type
phrase_negatives = result.get_by_match_type("PHRASE")
exact_negatives = result.get_by_match_type("EXACT")

# Group by category
intent_negatives = result.get_by_category("intent")
category_negatives = result.get_by_category("category")
alternative_negatives = result.get_by_category("alternative")
ai_negatives = result.get_by_category("ai")
feature_negatives = result.get_by_category("feature")

print("=" * 70)
print("否定关键词生成 - Chefman Air Fryer 8 Qt")
print("=" * 70)

print(f"\n📋 产品: {product_name}")
print(f"📋 类型: {product_type}")
print(f"📋 品牌: {brand}")

print(f"\n📊 总计: {len(result.negatives)} 个否定关键词")
print(f"   - PHRASE: {len(phrase_negatives)}")
print(f"   - EXACT: {len(exact_negatives)}")

print("\n" + "=" * 70)
print("🔴 PHRASE 匹配 (替代产品/配件类)")
print("=" * 70)

if category_negatives:
    print(f"\n📦 替代厨房电器 ({len(category_negatives)}):")
    for neg in sorted(category_negatives):
        print(f"   • {neg}")

if alternative_negatives:
    print(f"\n🔄 配件/相关产品 ({len(alternative_negatives)}):")
    for neg in sorted(alternative_negatives):
        print(f"   • {neg}")

if ai_negatives:
    print(f"\n🤖 AI智能识别 ({len(ai_negatives)}):")
    for neg in sorted(ai_negatives):
        print(f"   • {neg}")

print("\n" + "=" * 70)
print("🟡 EXACT 匹配 (非购买意图)")
print("=" * 70)

if intent_negatives:
    print(f"\n🔍 搜索/研究意图 ({len(intent_negatives)}):")
    for neg in sorted(intent_negatives):
        print(f"   • {neg}")

if feature_negatives:
    print(f"\n⚙️ 功能配件意图 ({len(feature_negatives)}):")
    for neg in sorted(feature_negatives):
        print(f"   • {neg}")

# Recommended list for campaign-level negatives (broader)
print("\n" + "=" * 70)
print("📋 推荐应用到广告系列级别的否定关键词")
print("=" * 70)

# PHRASE keywords for campaign level
print("\n【PHRASE 匹配】(建议广告系列级别)")
campaign_level_phrase = [n for n in phrase_negatives if len(n) > 3]
for neg in sorted(set(campaign_level_phrase)):
    print(f"  • {neg}")

print("\n【EXACT 匹配】(建议广告系列级别)")
# Filter EXACT to remove overly specific feature matches
filtered_exact = []
skip_patterns = ['450', 'hi-fry', 'turbofry', 'bake', 'dehydrate', 'frozen']
for neg in exact_negatives:
    skip = False
    for pattern in skip_patterns:
        if pattern.lower() in neg.lower():
            skip = True
            break
    if not skip and len(neg) > 4:
        filtered_exact.append(neg)

for neg in sorted(set(filtered_exact)):
    print(f"  • {neg}")

print("\n" + "=" * 70)
print("💡 说明")
print("=" * 70)
print("""
✅ 已排除以下类型（不会误杀真正买家）：
   - 高购买意图词: buy online, order online, for sale, on sale, best price
   - 品牌比较词: vs, versus, alternative, compare, better than
   - 折扣促销词: free, cheap, discount, coupon, promo code, deal

✅ 保留的否定词类型：
   - 替代厨房电器: deep fryer, convection oven, toaster oven, rotisserie
   - 配件类: air fryer accessory, air fryer liner, air fryer recipe book
   - 非购买意图: how to use, how to install, DIY, repair guide

⚠️ 注意: 如添加品牌比较词（如 "vs ninja air fryer"），会阻止正在比较品牌的买家
""")