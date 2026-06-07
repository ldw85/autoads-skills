#!/usr/bin/env python3
"""点击脚本: 访问 PartnerBoost 短链 10次，随机间隔1-5分钟"""
import asyncio
import random
import sys
from playwright.async_api import async_playwright

TARGET_URL = "https://pboost.me/s1iWggWg"
CLICK_COUNT = 10
MIN_INTERVAL = 60  # 1分钟
MAX_INTERVAL = 300  # 5分钟

async def click_link():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US"
        )
        
        for i in range(CLICK_COUNT):
            page = await context.new_page()
            try:
                await page.goto(TARGET_URL, timeout=15000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                print(f"[{i+1}/{CLICK_COUNT}] 访问成功: {TARGET_URL}")
            except Exception as e:
                print(f"[{i+1}/{CLICK_COUNT}] 访问失败: {e}")
            finally:
                await page.close()
            
            if i < CLICK_COUNT - 1:
                wait_time = random.randint(MIN_INTERVAL, MAX_INTERVAL)
                print(f"  等待 {wait_time} 秒...")
                await asyncio.sleep(wait_time)
        
        await browser.close()
        print("完成!")

if __name__ == "__main__":
    asyncio.run(click_link())
