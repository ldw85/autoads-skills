#!/usr/bin/env python3
"""
Archer 产品监控 CLI
==================
每2小时运行一次，检测被删产品并自动暂停对应广告系列

用法:
    python3 monitor_main.py --run          # 执行监控
    python3 monitor_main.py --status      # 查看监控状态
    python3 monitor_main.py --list-removed # 列出所有被删产品
    python3 monitor_main.py --pause-asin B08DL8WH9V  # 手动暂停指定 ASIN
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from src.product_monitor import ProductMonitor, REMOVED_LOG
from src.archer_client import ArcherClient, ArcherAuthError
from src.google_ads_data import GoogleAdsDataFetcher


def load_credentials():
    username = os.environ.get("ARCHER_USERNAME")
    password = os.environ.get("ARCHER_PASSWORD")
    return username, password


def init_clients():
    username, password = load_credentials()
    if not username or not password:
        print("❌ 缺少 Archer 凭证，请先配置：")
        print("   export ARCHER_USERNAME=你的用户名")
        print("   export ARCHER_PASSWORD=你的密码")
        sys.exit(1)

    os.environ["ARCHER_USERNAME"] = username
    os.environ["ARCHER_PASSWORD"] = password

    # 初始化 Archer
    archer = ArcherClient()
    try:
        archer.authenticate()
    except ArcherAuthError as e:
        print(f"❌ Archer 认证失败: {e}")
        sys.exit(1)

    # 初始化 Google Ads
    sys.path.insert(0, "/root/.openclaw/workspace")
    from autoads.src.google_ads_client import create_google_ads_client
    gads_client = create_google_ads_client()
    gads_fetcher = GoogleAdsDataFetcher(gads_client)

    return archer, gads_fetcher


def cmd_run():
    """执行监控"""
    print("\n🚀 启动产品监控...")
    archer, gads_fetcher = init_clients()
    monitor = ProductMonitor(archer, gads_fetcher)
    result = monitor.check_and_pause()
    return result


def cmd_status():
    """查看监控状态"""
    print("\n📊 监控状态")
    print("=" * 50)

    # 无效记录
    if os.path.exists(REMOVED_LOG):
        with open(REMOVED_LOG, "r") as f:
            removed = json.load(f)
        print(f"  累计无效产品数: {len(removed)}")
        for asin, info in list(removed.items())[:5]:
            print(f"    - {asin}: 检测于 {info['detected_at']}, "
                  f"关联广告 {len(info.get('linked_campaigns', []))} 个")
        if len(removed) > 5:
            print(f"    ... 还有 {len(removed) - 5} 个")
    else:
        print("  累计无效产品数: 0")

    print("=" * 50)


def cmd_list_removed():
    """列出所有被删除产品"""
    if not os.path.exists(REMOVED_LOG):
        print("暂无删除记录")
        return

    with open(REMOVED_LOG, "r") as f:
        removed = json.load(f)

    print(f"\n🚫 已删除产品列表（共 {len(removed)} 个）")
    print("-" * 70)
    print(f"  {'ASIN':<15} {'检测时间':<20} {'关联广告':<10}")
    print("-" * 70)

    for asin, info in removed.items():
        campaigns = info.get("linked_campaigns", [])
        print(f"  {asin:<15} {info['detected_at']:<20} {len(campaigns)} 个")


def cmd_pause_asin(asins: list):
    """手动暂停指定 ASIN 的广告"""
    if not asins:
        print("❌ 请指定要暂停的 ASIN")
        sys.exit(1)

    archer, gads_fetcher = init_clients()
    monitor = ProductMonitor(archer, gads_fetcher)

    all_paused = []
    for asin in asins:
        print(f"\n⏸️  手动暂停 ASIN={asin} 的广告...")
        paused = monitor._pause_campaigns_by_asin(asin)
        all_paused.extend(paused)

    print(f"\n✅ 共暂停 {len(all_paused)} 个广告系列")
    for c in all_paused:
        print(f"  - {c['campaign_name']} (ID: {c['campaign_id']})")


def main():
    parser = argparse.ArgumentParser(description="Archer 产品监控")
    parser.add_argument("--run", action="store_true", help="执行监控检测")
    parser.add_argument("--status", action="store_true", help="查看监控状态")
    parser.add_argument("--list-removed", action="store_true", help="列出所有被删产品")
    parser.add_argument("--pause-asin", nargs="+", help="手动暂停指定 ASIN 的广告")

    args = parser.parse_args()

    if args.run:
        cmd_run()
    elif args.status:
        cmd_status()
    elif args.list_removed:
        cmd_list_removed()
    elif args.pause_asin:
        cmd_pause_asin(args.pause_asin)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
