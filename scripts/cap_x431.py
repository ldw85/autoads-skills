#!/usr/bin/env python3
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')
from src.google_ads_client import GoogleAdsClientWrapper

env_path = Path('/root/.openclaw/workspace/autoads/archer-roi/.env')
if env_path.exists():
 load_dotenv(env_path)

client = GoogleAdsClientWrapper()
customer_id = '6660356395'
campaign_id = '23921712661'

query = f"""
SELECT
 campaign.id,
 campaign.name,
 campaign.status,
 ad_group.id,
 ad_group.name,
 ad_group.status,
 ad_group.cpc_bid_micros,
 ad_group_criterion.criterion_id,
 ad_group_criterion.keyword.text,
 ad_group_criterion.keyword.match_type,
 ad_group_criterion.status
FROM keyword_view
WHERE campaign.id = {campaign_id}
"""

print('=== Campaign23921712661 (Archer666-035-6395) ===')
for row in client.search(query, customer_id):
 camp_status = row.campaign.status
 ag_status = row.ad_group.status
 ag_bid_micros = row.ad_group.cpc_bid_micros
 if ag_bid_micros is None:
  ag_bid_micros = 0
 ag_bid = ag_bid_micros / 1000000
 kw_obj = row.ad_group_criterion.keyword
 kw = kw_obj.text if kw_obj else '(no keyword)'
 kw_match = kw_obj.match_type if kw_obj else ''
 kw_status = row.ad_group_criterion.status
 kw_id = row.ad_group_criterion.criterion_id

 print(f'Campaign: {row.campaign.name[:60]} | Status: {camp_status}')
 print(f' AdGroup: {row.ad_group.name} | Status: {ag_status} | CPC bid: ${ag_bid:.2f}')
 print(f' Keyword: [{kw}] match={kw_match} status={kw_status} id={kw_id}')
 print()
