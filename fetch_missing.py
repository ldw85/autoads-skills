#!/usr/bin/env python3
"""补跑缺失的13个ASIN"""
import json, time, random, urllib.request, urllib.error

DECODO_API_URL = "https://scraper-api.decodo.com/v2/scrape"
DECODO_AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"

missing = ['B00004R9VW', 'B07RKW5H68', 'B085WTVV18', 'B0BSP4NS28', 'B001IWNDDA',
           'B0744B55QV', 'B09CJG22ZT', 'B001CWX26Y', 'B0942BQ81N', 'B0BS4KNVZN',
           'B09J9T8NT2', 'B00CPGMUXW', 'B0BHDGZXW5']

results = []
for i, asin in enumerate(missing):
    print(f"[{i+1}/{len(missing)}] {asin}...", end=" ", flush=True)
    
    payload = json.dumps({
        "target": "amazon_pricing", "query": asin,
        "headless": "html", "page_from": "1", "parse": True
    }).encode('utf-8')
    
    req = urllib.request.Request(DECODO_API_URL, data=payload, headers={
        'Accept': 'application/json', 'Authorization': f'Basic {DECODO_AUTH}',
        'Content-Type': 'application/json'}, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pricing = (data.get('results', [{}])[0].get('content', {})
                      .get('results', {}).get('pricing', []))
            if pricing:
                price = float(pricing[0].get('price', 0))
                print(f"${price:.2f}")
                results.append({"asin": asin, "price": price, "status": "success"})
            else:
                print("NO PRICING DATA")
                results.append({"asin": asin, "price": 0, "status": "error"})
    except Exception as e:
        print(f"ERROR: {e}")
        results.append({"asin": asin, "price": 0, "status": "error"})
    
    time.sleep(random.uniform(0.1, 0.3))

with open('/root/.openclaw/workspace/decodo_missing_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} missing results")
for r in results:
    print(f"  {r['asin']}: ${r['price']:.2f}")
