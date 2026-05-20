#!/usr/bin/env python3
"""
搜索词质量分析脚本 - 精简版
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')
from src.google_ads_client import GoogleAdsClientWrapper
import re

IRRELEVANT = [
    (r'\b(laser|laserjet|inkjet|officejet|deskjet|envy)\b', 'OFFICE_PRINTER'),
    (r'\b(brother|mfc|dcp)\b', 'OFFICE_PRINTER'),
    (r'\b(canonselphy|canon pixma|canon g\d|canon tr|canon ts)\b', 'OFFICE_PRINTER'),
    (r'\b(epson ecotank|epson et|epson l\d|epson wf|epson xp)\b', 'OFFICE_PRINTER'),
    (r'\b(hp printer|hp deskjet|hp envy|hp officejet|hp laserjet)\b', 'OFFICE_PRINTER'),
    (r'\b(price|buy|cheap|discount|sale|for sale|budget)\b', 'SHOPPING'),
    (r'\b(all in one|multifunction|copier|scanner|fax)\b', 'OFFICE_PRINTER'),
    (r'\b(amazon|walmart|best buy)\b', 'PLATFORM'),
    (r'\b(sublimat|dtf)\b', 'WRONG_TYPE'),
    (r'\b(ecotank|megatank|smart tank)\b', 'OFFICE_PRINTER'),
]

client = GoogleAdsClientWrapper()
customer_id = '4772859239'
campaign_id = 23792756828

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
AND segments.date DURING LAST_7_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 5000
'''

gaas = client.client.get_service('GoogleAdsService')
response = gaas.search(customer_id=customer_id, query=query)

high_risk = []
all_terms = []
for row in response:
    term = row.search_term_view.search_term if row.search_term_view else ''
    if not term:
        continue
    term_lower = term.lower()
    issues = []
    for pattern, cat in IRRELEVANT:
        m = re.search(pattern, term_lower, re.IGNORECASE)
        if m:
            issues.append(cat)
    
    cost = row.metrics.cost_micros / 1000000 if row.metrics else 0
    clicks = row.metrics.clicks if row.metrics else 0
    
    if issues:
        high_risk.append({
            'term': term,
            'cost': cost,
            'clicks': clicks,
            'issues': issues
        })
    all_terms.append({'term': term, 'cost': cost, 'clicks': clicks, 'issues': issues})

high_risk.sort(key=lambda x: x['cost'], reverse=True)

print(f'搜索词质量分析 - Campaign {campaign_id}')
print(f'总搜索词: {len(all_terms)} | 高风险: {len(high_risk)}')
print()
print('=== 🔴 高风险搜索词 (建议加否定) ===')
for item in high_risk[:50]:
    print(f"{item['term'][:50]:<50} ${item['cost']:>6.2f} clicks:{item['clicks']:>3} {item['issues']}")