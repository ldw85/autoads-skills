#!/usr/bin/env python3
"""获取所有广告系列的搜索词数据，用于AI分析"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import GoogleAdsClientWrapper
import json
from datetime import datetime

client = GoogleAdsClientWrapper()

ACCOUNTS = [
    ('6052559425', 'YeahPromos'),
    ('4772859239', 'PartnerBoost'),
    ('3674729801', 'Archer-Yang'),
    ('6660356395', 'Archer'),
]

def get_campaigns_with_spending(customer_id, days=7, min_cost=1):
    query = f'''
    SELECT campaign.id, campaign.name, campaign.status,
           metrics.cost_micros, metrics.clicks, metrics.impressions
    FROM campaign
    WHERE campaign.status = 'ENABLED'
    AND metrics.cost_micros > {min_cost * 1000000}
    AND segments.date DURING LAST_{days}_DAYS
    ORDER BY metrics.cost_micros DESC
    LIMIT 20
    '''
    gaas = client.client.get_service('GoogleAdsService')
    response = gaas.search(customer_id=customer_id, query=query)
    campaigns = []
    for row in response:
        cost = row.metrics.cost_micros / 1000000 if row.metrics else 0
        clicks = row.metrics.clicks if row.metrics else 0
        campaigns.append({
            'id': row.campaign.id,
            'name': row.campaign.name,
            'cost': cost,
            'clicks': clicks,
        })
    return campaigns

def get_search_terms(customer_id, campaign_id, days=7):
    query = f'''
    SELECT 
        search_term_view.search_term,
        search_term_view.status,
        ad_group.id,
        ad_group.name,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions
    FROM search_term_view
    WHERE campaign.id = {campaign_id}
    AND metrics.cost_micros > 0
    AND segments.date DURING LAST_{days}_DAYS
    ORDER BY metrics.cost_micros DESC
    LIMIT 200
    '''
    gaas = client.client.get_service('GoogleAdsService')
    response = gaas.search(customer_id=customer_id, query=query)
    terms = []
    for row in response:
        term = row.search_term_view.search_term if row.search_term_view else ''
        if not term:
            continue
        terms.append({
            'term': term.lower().strip(),
            'ad_group_name': row.ad_group.name if row.ad_group else '',
            'clicks': row.metrics.clicks if row.metrics else 0,
            'cost': row.metrics.cost_micros / 1000000 if row.metrics else 0,
            'conversions': row.metrics.conversions if row.metrics else 0,
        })
    return terms


def get_existing_keywords(customer_id, campaign_id):
    """获取广告系列已有的关键词列表"""
    query = f'''
    SELECT ad_group_criterion.keyword.text
    FROM ad_group_criterion
    WHERE campaign.id = {campaign_id}
    AND ad_group_criterion.type = KEYWORD
    '''
    gaas = client.client.get_service('GoogleAdsService')
    try:
        response = gaas.search(customer_id=customer_id, query=query)
        keywords = set()
        for row in response:
            kw_text = row.ad_group_criterion.keyword.text
            if kw_text:
                keywords.add(kw_text.lower().strip())
        return keywords
    except Exception as e:
        print(f"    Warning: Could not fetch existing keywords: {e}")
        return set()

# Collect all data
all_data = {}
for acc_id, acc_name in ACCOUNTS:
    campaigns = get_campaigns_with_spending(acc_id, days=7, min_cost=1)
    if not campaigns:
        print(f'{acc_name}: No spending campaigns')
        continue
    print(f'\n=== {acc_name} ({acc_id}) ===')
    print(f'有花费广告系列: {len(campaigns)}')
    
    for camp in campaigns[:5]:  # Top 5 per account
        terms = get_search_terms(acc_id, camp['id'], days=7)
        existing_keywords = get_existing_keywords(acc_id, camp['id'])
        if terms:
            key = f"{acc_name}_{camp['id']}"
            all_data[key] = {
                'campaign_name': camp['name'],
                'campaign_id': camp['id'],
                'account': acc_name,
                'account_id': acc_id,
                'terms': terms,
                'existing_keywords': list(existing_keywords)  # 已有关键词列表
            }
            print(f"  {camp['name'][:50]} (ID:{camp['id']}) - {len(terms)} terms, ${camp['cost']:.2f}, {len(existing_keywords)} existing keywords")

# Save to file
output_file = '/root/.openclaw/workspace/logs/search_terms_for_ai.json'
import os
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, 'w') as f:
    json.dump(all_data, f, indent=2, ensure_ascii=False)

print(f'\n\n✅ 数据已保存到: {output_file}')
print(f'共 {len(all_data)} 个广告系列有搜索词数据')