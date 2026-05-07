#!/usr/bin/env python3
"""Check Amazon product availability via Decodo API"""
import json, time, random, urllib.request, urllib.error, sys

SCRAPE_URL = "https://scraper-api.decodo.com/v2/scrape"
AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"

def check_asin(asin):
    payload = json.dumps({
        "target": "amazon_pricing",
        "query": asin,
        "headless": "html",
        "page_from": "1",
        "parse": True
    }).encode("utf-8")
    req = urllib.request.Request(SCRAPE_URL, data=payload, headers={
        "Accept": "application/json",
        "Authorization": f"Basic {AUTH}",
        "Content-Type": "application/json"
    }, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return {"asin": asin, "status": "error", "msg": "no_results"}
            content = results[0].get("content", {})
            inner = content.get("results", {})
            parse_code = inner.get("parse_status_code", 0)
            pricing = inner.get("pricing", [])
            
            if parse_code == 12000 and pricing:
                first = pricing[0]
                condition = first.get("condition", "")
                seller = first.get("seller", "")
                delivery = first.get("delivery", "")
                price = first.get("price", 0)
                return {
                    "asin": asin,
                    "status": "valid",
                    "price": price,
                    "condition": condition,
                    "seller": seller,
                    "delivery": delivery,
                    "parse_code": parse_code
                }
            elif parse_code == 12000 and not pricing:
                return {"asin": asin, "status": "out_of_stock", "parse_code": parse_code}
            else:
                return {"asin": asin, "status": "error", "msg": f"parse_code_{parse_code}"}
    except urllib.error.HTTPError as e:
        return {"asin": asin, "status": "error", "msg": f"HTTP_{e.code}"}
    except Exception as e:
        return {"asin": asin, "status": "error", "msg": str(e)[:50]}

def main():
    asins = [a.strip() for a in sys.stdin if a.strip()] if not sys.argv[1:] else []
    if sys.argv[1:]:
        with open(sys.argv[1]) as f:
            asins = [l.strip() for l in f if l.strip()]
    
    print(f"Checking {len(asins)} ASINs...", flush=True)
    results = []
    for i, asin in enumerate(asins):
        print(f"[{i+1}/{len(asins)}] {asin}...", end=" ", flush=True)
        r = check_asin(asin)
        if r["status"] == "valid":
            print(f"✅ ${r['price']:.2f} [{r.get('condition','')}] - {r.get('seller','')[:20]}")
        elif r["status"] == "out_of_stock":
            print(f"❌ OUT OF STOCK")
        else:
            print(f"⚠️  {r.get('msg', 'unknown')}")
        results.append(r)
        time.sleep(random.uniform(0.1, 0.3))
    
    with open("/root/.openclaw/workspace/inventory_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    valid = [r for r in results if r["status"] == "valid"]
    oos = [r for r in results if r["status"] == "out_of_stock"]
    errors = [r for r in results if r["status"] == "error"]
    print(f"\n=== Summary ===")
    print(f"✅ Valid: {len(valid)}")
    print(f"❌ Out of stock: {len(oos)}")
    print(f"⚠️  Errors: {len(errors)}")
    if oos:
        print(f"\nOUT OF STOCK ASINs: {[r['asin'] for r in oos]}")

if __name__ == "__main__":
    main()
