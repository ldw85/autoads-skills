#!/usr/bin/env python3
import os
import sys
import json
import requests

env_path = "/root/.openclaw/workspace/skills/decodo-scraper/.env"
with open(env_path) as f:
    for line in f:
        if line.startswith("DECODO_AUTH_TOKEN="):
            token = line.strip().split("=", 1)[1]
            break

headers = {"Content-Type": "application/json", "Authorization": f"Basic {token}", "x-integration": "openclaw"}

def check_asin_stock(asin):
    url = "https://scraper-api.decodo.com/v2/scrape"
    payload = {"target": "amazon", "url": f"https://www.amazon.com/dp/{asin}", "parse": True}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            content = results[0].get("content", {})
            inner = content.get("results", {}) if isinstance(content, dict) else {}
            stock = inner.get("stock", "N/A")
            print(f"ASIN: {asin} | stock={stock} | title={inner.get('title','N/A')[:60]}")
            return stock
        return None
    except Exception as e:
        print(f"ASIN {asin}: Error - {e}")
        return None

check_asin_stock("B07DNYSJ8W")
check_asin_stock("B09NN1NHHN")