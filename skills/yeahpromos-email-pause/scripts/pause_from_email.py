#!/usr/bin/env python3
"""
YeahPromos 邮件暂停处理脚本
===========================

输入: 邮件正文内容
输出: 需要暂停的ASIN列表和确认

用法:
    python3 pause_from_email.py --email "邮件正文..."
"""

import sys
import os
import re
import json
from pathlib import Path

# Add paths
WORKDIR = Path(__file__).parent.parent.parent / "autoads" / "archer-roi"
sys.path.insert(0, str(WORKDIR))
sys.path.insert(0, str(WORKDIR.parent))
sys.path.insert(0, str(WORKDIR.parent / "src"))

MID_ASIN_DB = WORKDIR / "logs" / "mid_asin_mapping.json"


def load_mid_asin_mapping():
    """Load MID→ASIN mapping from file."""
    if MID_ASIN_DB.exists():
        with open(MID_ASIN_DB) as f:
            return json.load(f)
    return {}


def parse_asins_from_email(body):
    """从邮件正文中提取ASIN和MID。"""
    asins_direct = []
    mids_only = []
    
    # 格式1: ASIN:B0C7JCXX7K 或 ASIN: B0C7JCXX7K
    pattern_asin = r'ASIN:?\s*([A-Z0-9]{10})'
    asins_found = re.findall(pattern_asin, body, re.IGNORECASE)
    asins_direct.extend(asins_found)
    
    # 格式2: (MID:380763)
    pattern_mid = r'\(MID:\s*(\d+)\)'
    mids_found = re.findall(pattern_mid, body)
    mids_only.extend(mids_found)
    
    return list(set(asins_direct)), list(set(mids_only))


def get_asins_from_mids(mids, mapping):
    """通过MID查找对应的ASIN列表。"""
    asins_from_mid = []
    for mid in mids:
        mid_str = str(mid)
        if mid_str in mapping:
            asins_from_mid.extend(mapping[mid_str]['asins'])
    return list(set(asins_from_mid))


def analyze_email(body):
    """分析邮件内容，返回需要暂停的ASIN。"""
    asins_direct, mids_only = parse_asins_from_email(body)
    
    mapping = load_mid_asin_mapping()
    
    all_asins = list(set(asins_direct))
    asins_from_mid = get_asins_from_mids(mids_only, mapping)
    all_asins.extend(asins_from_mid)
    all_asins = list(set(all_asins))
    
    return {
        'asins_direct': asins_direct,
        'mids_only': mids_only,
        'asins_from_mid': asins_from_mid,
        'all_asins': all_asins,
        'mapping_found': {mid: mapping.get(mid, {}).get('asins', []) for mid in mids_only}
    }


def pause_asins(asins, dry_run=True):
    """暂停ASIN对应的广告。"""
    sys.path.insert(0, str(WORKDIR))
    from runner import load_google_ads_credentials, pause_campaigns_for_asins
    
    results = {'paused': [], 'failed': [], 'not_found': []}
    
    gads_client, gads_config = load_google_ads_credentials()
    
    for asin in asins:
        result = pause_campaigns_for_asins(
            gads_client,
            '6052559425',
            [asin],
            reason="YeahPromos邮件通知暂停",
            note="来自邮件解析"
        )
        
        if result['paused'] > 0:
            results['paused'].append(asin)
        elif result['found'] > 0:
            results['failed'].append(asin)
        else:
            results['not_found'].append(asin)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='YeahPromos邮件暂停处理')
    parser.add_argument('--email', required=True, help='邮件正文内容')
    parser.add_argument('--confirm', action='store_true', help='确认执行暂停')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟不实际暂停')
    
    args = parser.parse_args()
    
    print("=== 邮件解析结果 ===\n")
    
    result = analyze_email(args.email)
    
    print(f"直接ASIN: {result['asins_direct']}")
    print(f"仅MID: {result['mids_only']}")
    
    if result['mids_only']:
        print("\nMID→ASIN映射:")
        for mid, asins in result['mapping_found'].items():
            if asins:
                print(f"  MID {mid}: {len(asins)} 个ASIN")
            else:
                print(f"  MID {mid}: ⚠️ 映射中未找到")
    
    print(f"\n需要暂停的ASIN ({len(result['all_asins'])}个):")
    for asin in sorted(result['all_asins']):
        print(f"  - {asin}")
    
    if args.confirm and not args.dry_run:
        print("\n正在暂停...")
        pause_result = pause_asins(result['all_asins'], dry_run=False)
        print(f"\n已暂停: {pause_result['paused']}")
        print(f"失败: {pause_result['failed']}")
        print(f"未找到广告: {pause_result['not_found']}")
    elif args.dry_run:
        print("\n[DRY RUN] 未实际执行暂停")
    else:
        print("\n使用 --confirm 执行暂停，或 --dry-run 仅模拟")
