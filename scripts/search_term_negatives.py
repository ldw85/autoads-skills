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


def analyze_with_rules(campaign_name: str, search_terms: List[Dict]) -> Dict:
    """使用规则分析搜索词（备选方案）"""
    
    campaign_lower = campaign_name.lower()
    
    core_words = []
    if 'kodak' in campaign_lower:
        core_words = ['kodak', 'luma']
    elif 'dash cam' in campaign_lower:
        core_words = ['dash cam', 'dashcam']
    else:
        words = campaign_lower.split()
        core_words = [w for w in words if len(w) > 2][:2]
    
    # 产品型号检测（字母+数字组合如spx3000）
    import re
    
    relevant = []
    irrelevant = []
    
    for term_data in search_terms:
        term = term_data['term'].lower()
        clicks = term_data.get('clicks', 0)
        
        is_irrelevant = False
        reason = ""
        
        # 1. 完全是其他产品类型
        if 'printer' in term or 'print' in term:
            is_irrelevant = True
            reason = "办公打印机"
        elif 'laptop' in term or 'computer' in term or 'pc ' in term:
            is_irrelevant = True
            reason = "电脑产品"
        elif 'tv' in term or 'television' in term:
            is_irrelevant = True
            reason = "电视产品"
        
        # 2. 竞争对手品牌
        elif any(brand in term for brand in ['zebronics', 'epson', 'sony', 'benq', 'viewsonic', 'optoma']):
            is_irrelevant = True
            reason = "竞争对手品牌"
        
        # 3. 产品型号（字母+数字）是相关的
        elif re.match(r'^[a-zA-Z]+\d+$', term):
            is_irrelevant = False
        
        # 4. 太宽泛的词
        elif len(term.split()) == 1 and term not in ['projector', 'projectors']:
            is_irrelevant = True
            reason = "太宽泛的单词"
        
        if is_irrelevant:
            irrelevant.append({'term': term_data['term'], 'clicks': clicks, 'reason': reason})
        else:
            relevant.append({'term': term_data['term'], 'clicks': clicks, 'reason': '相关'})
    
    return {
        'relevant': relevant,
        'irrelevant': irrelevant,
        'summary': f'规则分析。核心词: {core_words}。不相关: {len(irrelevant)}个'
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
        
        # 同时用规则分析作为备选
        rule_analysis = analyze_with_rules(campaign_name, search_terms)
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