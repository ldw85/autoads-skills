#!/usr/bin/env python3
import sys
from dotenv import load_dotenv
from pathlib import Path
from google.protobuf import field_mask_pb2

sys.path.insert(0, '/root/.openclaw/workspace/autoads')
sys.path.insert(0, '/root/.openclaw/workspace/autoads/src')
from google.ads.googleads.errors import GoogleAdsException
from src.google_ads_client import GoogleAdsClientWrapper

env_path = Path('/root/.openclaw/workspace/autoads/archer-roi/.env')
if env_path.exists():
    load_dotenv(env_path)

client = GoogleAdsClientWrapper()
customer_id = '4772859239'
campaign_id = '23787626367'

layer_ad_groups = [
    'REDTIGER_Core',
    'REDTIGER_Generic',
    'REDTIGER_LongTail',
]

query = "SELECT ad_group.id, ad_group.name, ad_group.status FROM ad_group WHERE campaign.id = " + campaign_id
ag_map = {}
for row in client.search(query, customer_id):
    ag_map[row.ad_group.name] = (row.ad_group.id, row.ad_group.status)

ga_client = client._create_client()
service = ga_client.get_service("AdGroupService")

print("=" * 70)
print("ENABLING PAUSED layered ad groups in Campaign " + campaign_id)
print("=" * 70)

for ag_name in layer_ad_groups:
    if ag_name not in ag_map:
        print("  WARNING " + ag_name + ": NOT FOUND")
        continue
    ag_id, ag_status = ag_map[ag_name]
    if ag_status == 1:
        print("  OK " + ag_name + " (ID " + str(ag_id) + "): already ENABLED, skip")
        continue
    op = ga_client.get_type("AdGroupOperation")
    op.update.resource_name = "customers/" + customer_id + "/adGroups/" + str(ag_id)
    op.update.status = ga_client.get_type("AdGroupStatusEnum").AdGroupStatus.ENABLED
    fm = field_mask_pb2.FieldMask()
    fm.paths.append("status")
    op.update_mask.CopyFrom(fm)
    try:
        response = service.mutate_ad_groups(
            customer_id=customer_id,
            operations=[op],
        )
        print("  ENABLED " + ag_name + " (ID " + str(ag_id) + "): PAUSED -> ENABLED")
    except GoogleAdsException as ex:
        err_msg = ex.failure.errors[0].message if ex.failure and ex.failure.errors else str(ex)
        print("  FAILED " + ag_name + " (ID " + str(ag_id) + "): " + err_msg)

print("=" * 70)
print("Done")
