#!/usr/bin/env python3
"""点击 PartnerBoost 链接"""
import time
import random
import requests
import sys

url = "https://pboost.me/W1kKIgZ0"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
}

print(f"开始点击 {url}\n")

for i in range(5):
    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        print(f"第{i+1}/5次: status={resp.status_code}")
    except Exception as e:
        print(f"第{i+1}/5次: 失败 - {e}")
    
    if i < 4:
        delay = random.randint(60, 300)
        print(f"  等待 {delay}秒...\n")
        time.sleep(delay)

print("\n✓ 点击完成!")