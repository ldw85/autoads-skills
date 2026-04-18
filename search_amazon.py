#!/usr/bin/env python3
import sys
import json
import subprocess

def search_amazon(query):
    result = subprocess.run(
        ['python3', 'tools/scrape.py', '--target', 'amazon_search', '--query', query],
        capture_output=True, text=True, cwd='/root/.openclaw/workspace/skills/decodo-scraper'
    )
    try:
        data = json.loads(result.stdout)
        products = data.get('results', {}).get('products', [])
        return products
    except:
        return []

print("=== Satin Sandals ===")
products = search_amazon("satin sandals women")
for p in products[:8]:
    print(f"Title: {p.get('title','')}")
    print(f"Price: {p.get('price','')}")
    print(f"ASIN: {p.get('asin','')}")
    print(f"Link: {p.get('link','')}")
    print(f"Rating: {p.get('rating','')}")
    print("---")

print("\n=== Blue Satin Shoes ===")
products = search_amazon("blue satin shoes women")
for p in products[:8]:
    print(f"Title: {p.get('title','')}")
    print(f"Price: {p.get('price','')}")
    print(f"ASIN: {p.get('asin','')}")
    print(f"Link: {p.get('link','')}")
    print(f"Rating: {p.get('rating','')}")
    print("---")
