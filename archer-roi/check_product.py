#!/usr/bin/env python3
"""
Archer 产品状态检查
==================
使用 /check_product 接口检查 ASIN 是否在 Archer 联盟目录中仍然有效

用法:
    # 单个 ASIN
    python3 check_product.py --asin B082LV2VH6

    # 多个 ASIN
    python3 check_product.py --asin B082LV2VH6 B004EWLCUW B08DL8WH9V

    # 从文件读取（每行一个 ASIN）
    python3 check_product.py --asin-file asins.txt

    # 输出 JSON
    python3 check_product.py --asin B082LV2VH6 --json
"""

import os
import sys
import json
import argparse
import requests
from typing import List, Dict

ARCHER_API_BASE = "https://api.archeraffiliates.com"


def get_token() -> str:
    """获取 Access Token"""
    username = os.environ.get("ARCHER_USERNAME")
    password = os.environ.get("ARCHER_PASSWORD")

    if not username or not password:
        raise ValueError("请先设置环境变量 ARCHER_USERNAME 和 ARCHER_PASSWORD")

    resp = requests.post(
        f"{ARCHER_API_BASE}/token",
        data={"username": username, "password": password, "grant_type": "password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )

    if resp.status_code != 200:
        raise ValueError(f"认证失败: HTTP {resp.status_code}")

    return resp.json()["access_token"]


def check_asins(asins: List[str], token: str) -> Dict[str, Dict]:
    """
    批量检查 ASIN 状态

    Returns:
        {asin: {"status": "available"|"unavailable"|"error", "response": ...}}
    """
    headers = {"Authorization": f"Bearer {token}"}
    results = {}

    for asin in asins:
        asin = asin.strip()
        if not asin:
            continue

        try:
            resp = requests.get(
                f"{ARCHER_API_BASE}/check_product",
                params={"asin": asin},
                headers=headers,
                timeout=30
            )

            body = resp.json()

            if resp.status_code == 200:
                if "success" in body:
                    results[asin] = {"status": "available", "response": body}
                elif "detail" in body:
                    results[asin] = {"status": "unavailable", "response": body}
                else:
                    results[asin] = {"status": "unknown", "response": body}
            else:
                results[asin] = {"status": "error", "response": body}

        except Exception as e:
            results[asin] = {"status": "error", "response": str(e)}

    return results


def print_results(results: Dict[str, Dict], json_output: bool = False):
    """打印结果"""
    if json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    available = []
    unavailable = []

    for asin, result in results.items():
        if result["status"] == "available":
            available.append(asin)
        else:
            unavailable.append(asin)

    print("\n" + "=" * 60)
    print("  Archer 产品状态检查")
    print("=" * 60)
    print(f"  总计: {len(results)} 个 ASIN")
    print(f"  ✅ 有效:   {len(available)}")
    print(f"  ❌ 无效:   {len(unavailable)}")
    print("=" * 60)

    if unavailable:
        print("\n  ❌ 无效/已下架产品:")
        for asin in unavailable:
            resp = results[asin]["response"]
            detail = resp.get("detail", "未知原因")
            print(f"    - {asin}: {detail}")

    if available:
        print("\n  ✅ 有效产品:")
        for asin in available:
            resp = results[asin]["response"]
            print(f"    - {asin}: {resp.get('success', '')}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Archer 产品状态检查")
    parser.add_argument("--asin", nargs="+", help="要检查的 ASIN")
    parser.add_argument("--asin-file", type=str, help="ASIN 列表文件（每行一个）")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    # 收集 ASIN
    asins = []
    if args.asin:
        asins.extend(args.asin)
    if args.asin_file:
        with open(args.asin_file, "r") as f:
            asins.extend([line.strip() for line in f if line.strip()])

    if not asins:
        parser.print_help()
        sys.exit(1)

    print(f"正在检查 {len(asins)} 个 ASIN...")

    try:
        token = get_token()
        results = check_asins(asins, token)
        print_results(results, args.json)

        # 返回退出码：有任何无效的 ASIN 则返回 1
        unavailable = [a for a, r in results.items() if r["status"] != "available"]
        sys.exit(1 if unavailable else 0)

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
