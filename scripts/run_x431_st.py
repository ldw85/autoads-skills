#!/usr/bin/env python3
import sys
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')
from src.google_ads_client import GoogleAdsClientWrapper

env_path = Path('/root/.openclaw/workspace/autoads/archer-roi/.env')
if env_path.exists():
 load_dotenv(env_path)

client = GoogleAdsClientWrapper()

customer_id = '6660356395'
campaign_id = '23921712661'

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

query = f"""
SELECT
 search_term_view.search_term,
 ad_group.id,
 ad_group.name,
 metrics.impressions,
 metrics.clicks,
 metrics.cost_micros,
 metrics.conversions,
 metrics.conversions_value
FROM search_term_view
WHERE campaign.id = {campaign_id}
 AND segments.date BETWEEN '{start_date}' AND '{end_date}'
 AND metrics.clicks >=1
ORDER BY metrics.clicks DESC
"""

results = client.search(query, customer_id)
print(f'Time range: {start_date} ~ {end_date}')
print(f'Campaign: {campaign_id} (archer666-035-6395)')
print('=' *110)
header = f'{"Search Term":<55} {"AG":<10} {"Imp":>6} {"Clicks":>6} {"Cost":>10} {"Conv":>5} {"Value":>10}'
print(header)
print('=' *110)
total_cost =0.0
total_clicks =0
total_conv =0.0
total_value =0.0
count =0
for row in results:
 cost_micros = row.metrics.cost_micros or 0
 cost = cost_micros /1000000
 value = row.metrics.conversions_value or 0
 conv = row.metrics.conversions or 0
 ag_name = row.ad_group.name
 term = row.search_term_view.search_term
 print(f'{term[:55]:<55} {ag_name[:10]:<10} {row.metrics.impressions:>6} {row.metrics.clicks:>6} {cost:>10.2f} {conv:>5} {value:>10.2f}')
 total_cost += cost
 total_clicks += row.metrics.clicks
 total_conv += conv
 total_value += value
 count +=1
print('=' *110)
print(f'Total: {count} search terms | Clicks: {total_clicks} | Cost: ${total_cost:.2f} | Conv: {total_conv} | Value: ${total_value:.2f}')
