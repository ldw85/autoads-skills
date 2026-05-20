#!/usr/bin/env python3
"""
Add negative keywords and new keywords to Liene M100 campaign (23792756828)
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')

from src.google_ads_client import GoogleAdsClientWrapper
from google.ads.googleads.v23.enums.types.keyword_match_type import KeywordMatchTypeEnum

client = GoogleAdsClientWrapper()
customer_id = '4772859239'
campaign_id = '23792756828'

# Ad group IDs
ad_group_ids = {
    'L1_Brand': 199656304754,
    'L2_Core': 199452185671,
    'L3_Generic': 199452185671,
    'L5_LongTail': 196238824989,
}

# ============================================================
# Part 1: Add Negative Keywords (Campaign Level)
# ============================================================

negative_keywords = [
    'carverall laser printer',
    'hp 525 printer',
    'hp ink tank',
    'hp envy',
    'epson 8550',
    'epson l14150',
    'canon selphy',
    'canon printer',
    'rangeen printer',
    'hp print anywhere',
    'wireless printer',
    'printer price',
]

def add_negative_keywords(customer_id, campaign_id, keywords):
    """Add negative keywords to campaign level"""
    service = client.client.get_service("CampaignCriterionService")
    
    operations = []
    for kw_text in keywords:
        operation = client.client.get_type("CampaignCriterionOperation")
        criterion = operation.create
        criterion.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"
        criterion.negative = True
        
        keyword_info = criterion.keyword
        keyword_info.text = kw_text
        keyword_info.match_type = KeywordMatchTypeEnum.KeywordMatchType.PHRASE
        
        operations.append(operation)
    
    if operations:
        response = service.mutate_campaign_criteria(
            customer_id=customer_id,
            operations=operations
        )
        return response
    return None

print("=" * 60)
print("Adding negative keywords to campaign...")
print("=" * 60)

result = add_negative_keywords(customer_id, campaign_id, negative_keywords)
if result:
    print(f"✅ Added {len(result.results)} negative keywords")
    for r in result.results:
        print(f"   Created: {r.resource_name}")
else:
    print("❌ No results returned")

# ============================================================
# Part 2: Add New Keywords to Ad Groups
# ============================================================

new_keywords = {
    'L2_Core': [
        'phone photo printer',
        'portable photo printer 4x6',
        'mini photo printer for iphone',
        'bluetooth photo printer',
    ],
    'L3_Generic': [
        'bluetooth photo printer',
        'dye sublimation printer',
        'photo sticker printer',
    ],
}

def add_keywords_to_adgroup(customer_id, ad_group_id, keywords):
    """Add keywords to ad group"""
    service = client.client.get_service("AdGroupCriterionService")
    
    operations = []
    for kw_text in keywords:
        operation = client.client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
        
        keyword_info = criterion.keyword
        keyword_info.text = kw_text
        keyword_info.match_type = KeywordMatchTypeEnum.KeywordMatchType.PHRASE
        
        operations.append(operation)
    
    if operations:
        response = service.mutate_ad_group_criteria(
            customer_id=customer_id,
            operations=operations
        )
        return response
    return None

print()
print("=" * 60)
print("Adding new keywords to ad groups...")
print("=" * 60)

for layer, keywords in new_keywords.items():
    ad_group_id = ad_group_ids.get(layer)
    if ad_group_id:
        print(f"\n{layer} ({ad_group_id}):")
        result = add_keywords_to_adgroup(customer_id, ad_group_id, keywords)
        if result and hasattr(result, 'results'):
            print(f"   ✅ Added {len(result.results)} keywords")
            for r in result.results:
                print(f"      Created: {r.resource_name}")
        else:
            print(f"   ⚠️ No results")

print()
print("Done!")