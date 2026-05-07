#!/usr/bin/env python3
"""Decodo API price fetcher - serial calls with rate limiting"""

import json
import time
import sys
import random
import urllib.request
import urllib.error
from pathlib import Path

DECODO_API_URL = "https://scraper-api.decodo.com/v2/scrape"
DECODO_AUTH = "VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"

def fetch_asin_price(asin):
    """Fetch single ASIN price via Decodo API"""
    payload = json.dumps({
        "target": "amazon_pricing",
        "query": asin,
        "headless": "html",
        "page_from": "1",
        "parse": True
    }).encode('utf-8')
    
    req = urllib.request.Request(
        DECODO_API_URL,
        data=payload,
        headers={
            'Accept': 'application/json',
            'Authorization': f'Basic {DECODO_AUTH}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            results = data.get('results', [])
            if not results:
                return {"asin": asin, "price": 0, "title": "", "status": "error", "error": "No results"}
            
            content = results[0].get('content', {})
            inner = content.get('results', {})
            
            parse_code = inner.get('parse_status_code', 0)
            pricing = inner.get('pricing', [])
            
            if parse_code == 12000 and pricing:
                # Success with pricing data
                first_price = pricing[0].get('price', 0)
                return {
                    "asin": asin,
                    "price": float(first_price),
                    "condition": pricing[0].get('condition', ''),
                    "seller": pricing[0].get('seller', ''),
                    "parse_status": parse_code,
                    "status": "success"
                }
            elif parse_code == 12000 and not pricing:
                # Parse ok but no pricing
                return {"asin": asin, "price": 0, "title": "", "status": "error", "error": f"Parse OK but no pricing data (code {parse_code})"}
            else:
                return {"asin": asin, "price": 0, "title": "", "status": "error", "error": f"Parse code {parse_code}"}
            
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')[:200] if e.fp else str(e)
        return {"asin": asin, "price": 0, "title": "", "status": "error", "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"asin": asin, "price": 0, "title": "", "status": "error", "error": str(e)[:100]}

def main():
    asins = []
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            asins = [line.strip() for line in f if line.strip()]
    else:
        asins = [line.strip() for line in sys.stdin if line.strip()]
    
    print(f"Fetching {len(asins)} ASINs via Decodo API (serial, ~5 req/s)...", flush=True)
    
    results = []
    for i, asin in enumerate(asins):
        print(f"[{i+1}/{len(asins)}] {asin}...", end=" ", flush=True)
        r = fetch_asin_price(asin)
        if r["status"] == "success":
            print(f"${r['price']:.2f} [{r.get('condition', '')}]")
        else:
            print(f"ERROR: {r.get('error', 'unknown')}")
        results.append(r)
        
        delay = random.uniform(0.1, 0.3)
        time.sleep(delay)
    
    output_file = Path(__file__).parent / "decodo_api_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output_file}")
    
    valid = [r for r in results if r["status"] == "success" and r["price"] > 0]
    errors = [r for r in results if r["status"] == "error"]
    print(f"Summary: {len(valid)} valid prices, {len(errors)} errors")
    
    for r in valid:
        print(f"  {r['asin']}: ${r['price']:.2f}")

if __name__ == "__main__":
    main()
