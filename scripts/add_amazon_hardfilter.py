#!/usr/bin/env python3
"""
add_amazon_hardfilter.py - 把 Amazon 平台词硬过滤清单加到账号级共享否定词列表

【2026-06-13 创建 (David 拍板)】

背景:
- 搜索词分析硬过滤清单(12 个 Amazon 平台词,EXACT 匹配)
- 这些词只防"100% 错误"的 Amazon 平台词(用户搜 amazon prime / amazon gift card / amazon 地区词)
- 来源: 3 个 Amazon 联盟账号 (PB/Yeah/Archer) 当前账号级共享否定词列表

用法:
  # 加 12 个硬过滤词到默认 3 账号
  python3 scripts/add_amazon_hardfilter.py

  # 加到指定账号
  python3 scripts/add_amazon_hardfilter.py --customer-ids 4772859239,6052559425,6660356395

  # dry-run (只显示不实际加)
  python3 scripts/add_amazon_hardfilter.py --dry-run

  # 自定义词清单 (覆盖默认)
  python3 scripts/add_amazon_hardfilter.py --terms "amazon prime" "amazon gift card"

硬过滤清单 HARDFILTER_AMAZON_PLATFORM_TERMS 在 scripts/search_term_negatives.py 里定义
两边保持同步 (修改时改一处即可)
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = '/root/.openclaw/workspace/autoads'
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, f'{PROJECT_ROOT}/src')

from google.ads.googleads.v23.enums.types.keyword_match_type import KeywordMatchTypeEnum
from google.ads.googleads.v23.enums.types.criterion_type import CriterionTypeEnum
from src.google_ads_client import GoogleAdsClientWrapper

env_path = Path(PROJECT_ROOT) / 'archer-roi' / '.env'
if env_path.exists():
    load_dotenv(env_path)

# 加载硬过滤清单 (来自 search_term_negatives.py 的权威定义)
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('stn', '/root/.openclaw/workspace/scripts/search_term_negatives.py')
stn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stn)
DEFAULT_TERMS = stn.HARDFILTER_AMAZON_PLATFORM_TERMS

# 3 个 Amazon 联盟账号的 account-level 共享列表 (默认目标)
DEFAULT_ACCOUNTS = [
    ('4772859239', 'PB'),
    ('6052559425', 'Yeah'),
    ('6660356395', 'Archer'),
]
ACCOUNT_LEVEL_LIST_NAME = 'account-level negative keywords list'


def find_account_level_shared_set(underlying, customer_id: str) -> str:
    """动态查找账号的 'account-level negative keywords list' 共享列表 ID"""
    query = f'''
    SELECT
      shared_set.resource_name,
      shared_set.name
    FROM shared_set
    WHERE shared_set.name = "{ACCOUNT_LEVEL_LIST_NAME}"
    '''
    req = underlying.get_type('SearchGoogleAdsStreamRequest')
    req.customer_id = customer_id
    req.query = query
    ga_service = underlying.get_service('GoogleAdsService')
    stream = ga_service.search_stream(request=req)
    for batch in stream:
        for row in batch.results:
            return row.shared_set.resource_name
    return None


def list_existing_amazon_words(underlying, customer_id: str) -> set:
    """查账号当前已有的 Amazon 相关词 (避免重复)"""
    query = f'''
    SELECT
      shared_criterion.keyword.text
    FROM shared_criterion
    WHERE shared_set.name = "{ACCOUNT_LEVEL_LIST_NAME}"
    '''
    req = underlying.get_type('SearchGoogleAdsStreamRequest')
    req.customer_id = customer_id
    req.query = query
    ga_service = underlying.get_service('GoogleAdsService')
    stream = ga_service.search_stream(request=req)
    existing = set()
    for batch in stream:
        for row in batch.results:
            existing.add(row.shared_criterion.keyword.text.lower())
    return existing


def add_hardfilter_to_account(underlying, customer_id: str, name: str,
                                terms: list, dry_run: bool = False) -> dict:
    """把硬过滤词加到指定账号的 account-level 共享列表
    
    Returns: dict with 'added', 'skipped', 'failed' counts
    """
    service = underlying.get_service('SharedCriterionService')
    
    # 1. 找共享列表
    shared_set_resource = find_account_level_shared_set(underlying, customer_id)
    if not shared_set_resource:
        return {'error': f'账号 {name} ({customer_id}) 没有 "{ACCOUNT_LEVEL_LIST_NAME}" 共享列表'}
    
    # 2. 查现有词,过滤重复
    existing = list_existing_amazon_words(underlying, customer_id)
    to_add = [t for t in terms if t.lower() not in existing]
    skipped = [t for t in terms if t.lower() in existing]
    
    if not to_add:
        return {'added': 0, 'skipped': len(skipped), 'failed': 0,
                'shared_set': shared_set_resource}
    
    # 3. 构造操作
    operations = []
    for term in to_add:
        op = underlying.get_type('SharedCriterionOperation')
        criterion = op.create
        criterion.shared_set = shared_set_resource
        criterion.keyword.text = term
        criterion.keyword.match_type = KeywordMatchTypeEnum.KeywordMatchType.EXACT
        criterion.type_ = CriterionTypeEnum.CriterionType.KEYWORD
        # 不设 negative - shared_set 类型 (NEGATIVE_KEYWORD_LIST) 本身就是 negative
        operations.append(op)
    
    if dry_run:
        return {'added': 0, 'to_add': to_add, 'skipped': len(skipped),
                'shared_set': shared_set_resource, 'dry_run': True}
    
    # 4. 执行
    try:
        response = service.mutate_shared_criteria(
            customer_id=customer_id,
            operations=operations
        )
        return {'added': len(response.results), 'skipped': len(skipped),
                'failed': 0, 'shared_set': shared_set_resource}
    except Exception as e:
        return {'added': 0, 'skipped': len(skipped), 'failed': len(to_add),
                'error': str(e), 'shared_set': shared_set_resource}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='添加 Amazon 平台词硬过滤到账号级共享列表')
    parser.add_argument('--customer-ids', type=str, default=None,
                      help='逗号分隔的 customer_id 列表 (默认: 3 个联盟账号)')
    parser.add_argument('--terms', nargs='+', default=None,
                      help='自定义词清单 (默认: HARDFILTER_AMAZON_PLATFORM_TERMS)')
    parser.add_argument('--dry-run', action='store_true', help='只显示不实际加')
    args = parser.parse_args()
    
    # 解析账号
    if args.customer_ids:
        accounts = [(cid.strip(), f'Custom-{cid.strip()}') for cid in args.customer_ids.split(',')]
    else:
        accounts = DEFAULT_ACCOUNTS
    
    # 解析词
    terms = args.terms if args.terms else DEFAULT_TERMS
    
    print(f'=== 添加 Amazon 平台词硬过滤 (EXACT) 到账号级共享列表 ===')
    print(f'账号: {[c[1] for c in accounts]}')
    print(f'词数: {len(terms)}')
    print(f'模式: {"dry-run" if args.dry_run else "实际执行"}')
    print()
    
    client = GoogleAdsClientWrapper()
    underlying = client.client
    
    summary = []
    for CID, name in accounts:
        print(f'--- {name} ({CID}) ---')
        result = add_hardfilter_to_account(underlying, CID, name, terms, dry_run=args.dry_run)
        
        if result.get('error') and 'shared_set' not in result:
            print(f'  ❌ {result["error"]}')
            summary.append((name, CID, 'FAILED', result))
            continue
        
        if result.get('dry_run'):
            print(f'  [DRY-RUN] shared_set: {result["shared_set"]}')
            print(f'  [DRY-RUN] 将添加 {len(result["to_add"])} 词, 跳过 {result["skipped"]} 已存在')
            for t in result['to_add']:
                print(f'    + {t}')
            summary.append((name, CID, 'DRY-RUN', result))
        else:
            print(f'  shared_set: {result.get("shared_set", "?")}')
            print(f'  添加: {result["added"]}, 跳过: {result["skipped"]}, 失败: {result["failed"]}')
            if result.get('error'):
                print(f'  ❌ 错误: {result["error"]}')
            summary.append((name, CID, 'OK' if result['added'] > 0 else 'SKIP', result))
        print()
    
    print('=== 总结 ===')
    for name, CID, status, _ in summary:
        print(f'  {name} ({CID}): {status}')


if __name__ == '__main__':
    main()
