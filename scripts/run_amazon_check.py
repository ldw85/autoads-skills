#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/root/.openclaw/workspace/autoads/archer-roi')
os.chdir('/root/.openclaw/workspace/autoads/archer-roi')
from runner import run_product_check

results = run_product_check(network_filter='archer', include_pause=True)
print(f"Checked {len(results)} products")

# Count statuses
available = sum(1 for r in results if r.get('status') == 'available')
unavailable = sum(1 for r in results if r.get('status') == 'unavailable')
unknown = sum(1 for r in results if r.get('status') == 'unknown')
hidden = sum(1 for r in results if r.get('status') == 'hidden_no_active_ads')

print(f"Available: {available}")
print(f"Unavailable: {unavailable}")
print(f"Unknown: {unknown}")
print(f"Hidden (no active ads): {hidden}")

# Print unavailable ASINs
oos = [r for r in results if r.get('status') == 'unavailable']
if oos:
    print("\nUnavailable products:")
    for r in oos:
        print(f"  {r['asin']} ({r.get('network','')}) - {r.get('details',{})}")