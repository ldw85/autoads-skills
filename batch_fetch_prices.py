#!/usr/bin/env python3
"""Batch fetch Amazon product prices using Decodo skill's fetch.py"""

import subprocess
import json
import time
import sys
from pathlib import Path

FETCH_SCRIPT = Path("/root/.openclaw/workspace/skills/amazon-product-fetcher/scripts/fetch.py")

def fetch_asin(asin):
    """Fetch single ASIN price"""
    try:
        result = subprocess.run(
            ["python3", str(FETCH_SCRIPT), "--asin", asin, "--json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            price_str = data.get("price", "0").replace("$", "").replace(",", "")
            return {
                "asin": asin,
                "price": float(price_str) if price_str else 0,
                "title": data.get("title", "")[:60],
                "status": "success"
            }
        else:
            return {"asin": asin, "price": 0, "title": "", "status": "error", "error": result.stderr[:100]}
    except Exception as e:
        return {"asin": asin, "price": 0, "title": "", "status": "error", "error": str(e)[:100]}

def main():
    # Read ASINs from stdin or file
    asins = []
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            asins = [line.strip() for line in f if line.strip()]
    else:
        asins = [line.strip() for line in sys.stdin if line.strip()]
    
    print(f"Fetching prices for {len(asins)} ASINs...", flush=True)
    
    results = []
    for i, asin in enumerate(asins):
        print(f"[{i+1}/{len(asins)}] Fetching {asin}...", end=" ", flush=True)
        r = fetch_asin(asin)
        if r["status"] == "success":
            print(f"${r['price']:.2f} - {r['title'][:40]}")
        else:
            print(f"ERROR: {r.get('error', 'unknown')}")
        results.append(r)
        time.sleep(0.5)  # Rate limit
    
    # Save results
    output_file = Path(__file__).parent / "decodo_fetch_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to {output_file}")
    
    # Print summary
    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]
    print(f"\nSummary: {len(success)} success, {len(failed)} failed")
    
    return results

if __name__ == "__main__":
    main()