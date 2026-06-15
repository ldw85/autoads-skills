#!/usr/bin/env python3
"""
搜索词否定词分析CLI工具

工作流程：
1. 获取指定广告系列的搜索词
2. 输出搜索词列表（在会话中用AI分析）
3. 用户确认后执行添加

用法：
    python3 scripts/search_term_negatives.py --campaign-id <CAMPAIGN_ID> [--customer-id <CID>]
    python3 scripts/search_term_negatives.py --campaign "DC HOUSE"
"""

import sys
import os
import re
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Setup path
PROJECT_ROOT = '/root/.openclaw/workspace/autoads'
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, f'{PROJECT_ROOT}/src')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger()


# ============================================================
# 否定词输入解析 - 统一规则(生成/添加两侧共用)
# ============================================================
# 明确禁止: 不再用空格作为分隔符(多词短语内部会冲突)
# 仅支持 2 种分隔符: 逗号(,) / 换行(\n)
# 同一个解析函数同时服务于:
#   1. CLI 参数 --add (用户从 shell 传入)
#   2. AI 在会话中生成的否定词列表 (粘贴到 --add)
#   3. 文件 --add-from-file (每行一个, # 开头为注释)
# ============================================================

_NEG_DELIMITERS = re.compile(r'[,\n]+')


def parse_negatives_input(text: str) -> List[str]:
    """解析否定词输入 - 统一规则(逗号/换行分隔，不拆分空格)

    关键规则: 多词短语(如 "zevo flying insect trap")必须用换行或逗号
    在两个短语之间,不能仅靠空格区隔,否则会拆成多个单词。

    Examples:
        >>> parse_negatives_input('zevo,raid,fly')
        ['zevo', 'raid', 'fly']
        >>> parse_negatives_input('zevo flying insect trap\\nraid fogger')
        ['zevo flying insect trap', 'raid fogger']
        >>> parse_negatives_input('zevo flying insect trap,raid fogger')
        ['zevo flying insect trap', 'raid fogger']
        >>> parse_negatives_input('zevo\\nraid\\nwondercide')
        ['zevo', 'raid', 'wondercide']
        >>> parse_negatives_input('  zevo  ,  raid  \\n  wondercide  ')
        ['zevo', 'raid', 'wondercide']
        >>> parse_negatives_input('')
        []
    """
    if not text or not text.strip():
        return []
    # 仅按逗号/换行拆分(连续多个分隔符合并)
    items = _NEG_DELIMITERS.split(text.strip())
    # 去空、去重、保序
    seen = set()
    result = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def load_negatives_from_file(filepath: str) -> List[str]:
    """从文件加载否定词 - 每行一个, # 开头为注释

    AI 在会话中输出否定词时,统一采用这种格式(每行一个),
    用户可直接保存为 .txt 文件后用 --add-from-file 传入
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f'文件不存在: {filepath}')
    result = []
    with open(path, 'r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            result.append(stripped)
    return result


def format_negatives_for_ai(negatives: List[str]) -> str:
    """AI 会话中输出否定词 - 统一为每行一个的代码块格式

    这样用户可以直接:
        1. 复制粘贴到 --add "..." (每行一个)
        2. 或保存为文件用 --add-from-file
    """
    return '\n'.join(negatives)


def get_gads_client():
    """Initialize Google Ads client"""
    from dotenv import load_dotenv
    from src.google_ads_client import GoogleAdsClientWrapper
    
    env_path = Path(PROJECT_ROOT) / 'archer-roi' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        
    return GoogleAdsClientWrapper()


def get_search_terms(client, customer_id: str, campaign_id: str, 
                start_date: str = None, end_date: str = None) -> List[Dict]:
    """获取广告系列的搜索词报告"""
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    query = f"""
        SELECT 
            search_term_view.search_term,
            campaign.id,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM search_term_view
        WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{start_date}' AND '{end_date}'
            AND metrics.clicks >= 1
        ORDER BY metrics.clicks DESC
    """
    
    try:
        ga_service = client.client.get_service("GoogleAdsService")
        search_request = client.client.get_type("SearchGoogleAdsRequest")
        search_request.query = query
        search_request.customer_id = customer_id
        
        results = ga_service.search(request=search_request)
        terms = []
        for row in results:
            terms.append({
                'term': row.search_term_view.search_term,
                'clicks': row.metrics.clicks,
                'impressions': row.metrics.impressions,
                'cost': row.metrics.cost_micros / 1_000_000 if row.metrics.cost_micros else 0,
                'conversions': row.metrics.conversions if row.metrics.conversions else 0
            })
        return terms
    except Exception as e:
        logger.error(f'Failed to get search terms: {e}')
        return []


def get_campaign_info(client, customer_id: str, campaign_id: str) -> Optional[Dict]:
    """获取广告系列信息"""
    
    query = f"""
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.id = {campaign_id}
    """
    
    try:
        results = client.search(query, customer_id)
        for row in results:
            return {
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status
            }
    except Exception as e:
        logger.error(f'Failed to get campaign info: {e}')
    return None


# ============================================================
# 硬过滤 (Hard Filter) - 只防 100% 错误的搜索词
# ============================================================
# 【2026-06-13 架构重写 (David 拍板)】
# 背景:
#   1. 之前 analyze_with_rules 是"if-then 字符串匹配",在 9 个产品 / 217 词实证中
#      - 误伤 9 个 (C3 Anker Laptop Power Bank 误判 "laptop power bank" 不相关)
#      - 漏标 25 个 (竞品/同品牌不同产品线/品牌误拼/品类漂移)
#   2. David 决定规则降级为"硬过滤" (只防 100% 错误的词),语义判断由 AI 100% 复审
#   3. 硬过滤清单来自: 3 个 Amazon 联盟账号 (PB/Yeah/Archer) 当前账号级否定词里
#      含 amazon 但不含产品类型的纯平台词
#   4. 架构简化: 手动触发,不考虑 Cron 场景
#
# 设计原则 (David 明确):
#   - 硬过滤只能用于「亚马逊平台词」
#   - 12 个 Amazon 平台词 EXACT 精确匹配 (因为"amazon"单独看可能是产品修饰词)
#   - 硬过滤命中的标"不相关 - Amazon 平台词",AI 不用再看
#   - 硬过滤未命中的全部归"待 AI 复审" (原 'relevant'),AI 100% 判断
#   - 不再做: 产品类型漂移 / 竞品品牌 / 单字过宽 / 同品牌不同产品线
#     (全部由主对话 AI 100% 复审,符合第十一铁律: 工具不带 AI 推理)
# ============================================================

# Amazon 平台词硬过滤清单 (EXACT 精确匹配)
# 来源: 3 个 Amazon 联盟账号 (PB/Yeah/Archer) 当前账号级共享否定词列表
# 筛选标准: 含 amazon/prime 但不含产品类型
# 同步状态: 已加到 3 账号的 "account-level negative keywords list" 共享列表 (12 × 3 = 36)
HARDFILTER_AMAZON_PLATFORM_TERMS = [
    # Amazon 平台活动/支付词
    'amazon prime',
    'amazon gift card',

    # Amazon + 国家/地区词 (用户在找特定地区 Amazon)
    'amazone com usa',
    'amazon estados unidos',
    'amazon eeuu',
    'amazon eua',
    'amazon amerika',
    'amazone us',
    'amazon in usa',
    'amazon eua site',
    'eua amazon',

    # Amazon 拼写错误
    'amazoni',
]


def analyze_with_rules(search_terms: List[Dict]) -> Dict:
    """使用硬过滤规则分析搜索词 (降级版, 2026-06-13)
    
    职责: 只做"硬过滤" - 只防 100% 错误的 Amazon 平台词
    - 命中 HARDFILTER_AMAZON_PLATFORM_TERMS → 标"不相关 - Amazon 平台词"
    - 未命中 → 标"待 AI 复审" (即 relevant 列表, 等主对话 AI 100% 判断)
    
    注: campaign_name 参数已删除 (硬过滤只看 Amazon 平台词, 不需要产品上下文)
    
    不再做 (这些由 AI 在主对话做):
    - 产品类型漂移 (printer/laptop/tv)
    - 竞品品牌检测
    - 单字过宽词
    - 同品牌不同产品线
    
    Args:
        search_terms: List of dicts with keys 'term', 'clicks', 'impressions', etc.
    
    Returns:
        Dict with 'relevant' (待 AI 复审) and 'irrelevant' (硬过滤命中)
    """
    relevant = []  # 待 AI 复审
    irrelevant = []  # 硬过滤命中 (Amazon 平台词)
    
    # 归一化硬过滤词到小写集合 (O(1) 查询)
    hardfilter_set = {w.lower() for w in HARDFILTER_AMAZON_PLATFORM_TERMS}
    
    for term_data in search_terms:
        term = term_data['term']
        term_lower = term.lower()
        clicks = term_data.get('clicks', 0)
        
        # 硬过滤: EXACT 精确匹配 (小写归一化)
        if term_lower in hardfilter_set:
            irrelevant.append({
                'term': term,
                'clicks': clicks,
                'reason': 'Amazon 平台词 (硬过滤 EXACT 匹配)'
            })
        else:
            # 其他全部归为"待 AI 复审"
            relevant.append({
                'term': term,
                'clicks': clicks,
                'reason': '待 AI 复审'
            })
    
    return {
        'relevant': relevant,
        'irrelevant': irrelevant,
        'summary': (
            f'硬过滤分析。Amazon 平台词命中: {len(irrelevant)}个, '
            f'待 AI 复审: {len(relevant)}个'
        )
    }


def add_negative_keywords(customer_id: str, campaign_id: str, 
                       negatives: List[str], match_type: str = 'BROAD') -> bool:
    """添加否定关键词到广告系列"""
    
    from dotenv import load_dotenv
    load_dotenv(Path(PROJECT_ROOT) / 'archer-roi' / '.env')
    
    from src.refined_bid_optimizer import RefinedBidOptimizer
    
    optimizer = RefinedBidOptimizer()
    
    try:
        result = optimizer._add_negative_keywords_to_campaign(
            customer_id, campaign_id, negatives, match_type
        )
        logger.info(f'Added {result} negative keywords')
        return True
    except Exception as e:
        logger.error(f'Failed to add: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description='搜索词否定词分析CLI工具')
    parser.add_argument('--campaign-id', type=str, help='广告系列ID')
    parser.add_argument('--campaign', type=str, help='广告系列名称（模糊匹配）')
    parser.add_argument('--customer-id', type=str, default='6660356395',
                      help='Google Ads Customer ID (default: 6660356395)')
    parser.add_argument('--days', type=int, default=30,
                      help='分析最近N天的数据 (default: 30)')
    parser.add_argument('--output', type=str, 
                      default='/tmp/search_term_negatives_output.json',
                      help='输出文件路径')
    parser.add_argument('--add', type=str, default=None,
                      help='添加否定词（逗号/换行 分隔；空格是多词短语内部字符,不用作分隔符）')
    parser.add_argument('--add-from-file', type=str, default=None,
                      help='从文件读取否定词（每行一个，# 开头为注释）')
    parser.add_argument('--match-type', type=str, default='PHRASE',
                      help='匹��类型: BROAD, PHRASE, EXACT')
    
    parser.add_argument('--auto-ai', action='store_true',
                      help='自动调用AI语义分析')
    args = parser.parse_args()
    
    # 先处理添加否定词的请求
    negatives_to_add = []
    if args.add:
        negatives_to_add.extend(parse_negatives_input(args.add))
    if args.add_from_file:
        negatives_to_add.extend(load_negatives_from_file(args.add_from_file))

    if negatives_to_add and args.campaign_id:
        logger.info(f'Adding {len(negatives_to_add)} negatives: {negatives_to_add}')
        result = add_negative_keywords(args.customer_id, args.campaign_id, negatives_to_add, args.match_type)
        if result:
            print(f'✅ 已添加 {len(negatives_to_add)} 个否定词')
            for n in negatives_to_add:
                print(f'   - {n}')
        else:
            print('❌ 添加失败')
        return
    
    # 参数校验
    if not args.campaign_id and not args.campaign:
        parser.error('需要 --campaign-id 或 --campaign')
    
    logger.info('搜索词否定词分析工具')
    logger.info('=' * 50)
    
    client = get_gads_client()
    
    target_campaigns = []
    
    if args.campaign_id:
        info = get_campaign_info(client, args.customer_id, args.campaign_id)
        if info:
            target_campaigns.append(info)
        else:
            logger.error(f'找不到广告系列: {args.campaign_id}')
            return
    else:
        query = """
            SELECT campaign.id, campaign.name, campaign.status
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            LIMIT 200
        """
        try:
            results = client.search(query, args.customer_id)
            search_pattern = args.campaign.lower().replace(' ', '')
            for row in results:
                camp_name = row.campaign.name.lower().replace(' ', '')
                if search_pattern in camp_name:
                    target_campaigns.append({
                        'id': row.campaign.id,
                        'name': row.campaign.name,
                        'status': row.campaign.status
                    })
        except Exception as e:
            logger.error(f'Search failed: {e}')
            return
    
    if not target_campaigns:
        logger.error('没有找到匹配的 广告系列')
        return
    
    logger.info(f'找到 {len(target_campaigns)} 个广告系列')
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    logger.info(f'分析范围: {start_date} ~ {end_date}')
    
    all_results = {'campaigns': [], 'date_range': {'start': start_date, 'end': end_date}}
    
    for camp in target_campaigns:
        campaign_id = str(camp['id'])
        campaign_name = camp['name']
        
        logger.info(f'分析: {campaign_name[:50]}...')
        
        search_terms = get_search_terms(client, args.customer_id, campaign_id, start_date, end_date)
        
        if not search_terms:
            logger.info(f'无搜索词数据')
            continue
        
        logger.info(f'获取到 {len(search_terms)} 个搜索词')
        
        # 格式化输出，供用户在会话中用AI分析
        terms_formatted = '\n'.join([
            f"{i+1}. {t['term']} ({t.get('clicks', 0)} clicks)"
            for i, t in enumerate(search_terms[:30])
        ])
        
        print('\n' + '=' * 50)
        print('📊 搜索词分析')
        print('=' * 50)
        print(f'广告系列: {campaign_name}')
        print(f'Campaign ID: {campaign_id}')
        print('')
        print('搜索词列表:')
        print(terms_formatted)
        print('=' * 50)
        
        # 如果开启自动AI分析
        if args.auto_ai:
            print('AI分析结果将在会话中返回')
        else:
            print('')
            print('请把上面的搜索词列表发给我，我会用AI帮你分析哪些是不相关的搜索词')
        
        # 同时用硬过滤分析 (Amazon 平台词)
        rule_analysis = analyze_with_rules(search_terms)
        logger.info(f'规则分析: {rule_analysis["summary"]}')
        
        campaign_result = {
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'customer_id': args.customer_id,
            'total_search_terms': len(search_terms),
            'relevant': rule_analysis.get('relevant', []),
            'irrelevant': rule_analysis.get('irrelevant', []),
            'summary': rule_analysis.get('summary', '')
        }
        
        all_results['campaigns'].append(campaign_result)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f'结果已保存到: {args.output}')
    
    # 如果有不相关的，显示建议
    if target_campaigns:
        negatives = [x['term'] for x in rule_analysis.get('irrelevant', [])]
        if negatives:
            print('')
            print('规则分析建议的否定词（供参考）:')
            for n in negatives[:5]:
                print(f'  - {n}')
            print('')
            print('如果确认添加，请说: 确认添加')
            print('')
            print('或直接用以下命令：')
            print(f'  --add "{",".join(negatives)}"')
            print(f'  --add-from-file <file>  # 每行一个')


if __name__ == '__main__':
    main()