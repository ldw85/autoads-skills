#!/usr/bin/env python3
"""
批量搜索词否定词分析脚本

分析所有账户所有活跃（有花费）广告系列的搜索词报告，
输出到飞书文档

用法：
    python3 scripts/search_term_all.py [--days 7] [--min-cost 1]
"""

import sys
import os
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

# Import analyze_with_rules from single script
import importlib.util
spec = importlib.util.spec_from_file_location(
    "search_term_negatives", 
    "/root/.openclaw/workspace/scripts/search_term_negatives.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
analyze_with_rules = module.analyze_with_rules

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger()


ACCOUNTS = {
    '6660356395': {'name': 'Archer'},
    '6052559425': {'name': 'YeahPromos'},
    '4772859239': {'name': 'PartnerBoost'}
}


def get_gads_client():
    """Initialize Google Ads client"""
    from dotenv import load_dotenv
    from src.google_ads_client import GoogleAdsClientWrapper
    
    env_path = Path(PROJECT_ROOT) / 'archer-roi' / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    return GoogleAdsClientWrapper()


def get_active_campaigns_with_spend(client, customer_id: str, days: int = 7, min_cost: float = 1.0) -> List[Dict]:
    """获取有花费的活跃广告系列"""
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    query = f"""
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            metrics.cost_micros
        FROM campaign
        WHERE campaign.status IN ('ENABLED', 'PAUSED')
            AND segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.cost_micros DESC
        LIMIT 100
    """
    
    try:
        results = client.search(query, customer_id)
        campaigns = []
        for row in results:
            cost = row.metrics.cost_micros / 1_000_000 if row.metrics.cost_micros else 0
            if cost >= min_cost:
                campaigns.append({
                    'id': row.campaign.id,
                    'name': row.campaign.name,
                    'status': row.campaign.status,
                    'cost': cost
                })
        return campaigns
    except Exception as e:
        logger.warning(f'Failed to get campaigns for {customer_id}: {e}')
        return []


def get_search_terms(client, customer_id: str, campaign_id: str, 
                start_date: str, end_date: str) -> List[Dict]:
    """获取广告系列的搜索词报告"""
    
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
        results = client.search(query, customer_id)
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


def main():
    parser = argparse.ArgumentParser(description='批量搜索词否定词分析')
    parser.add_argument('--days', type=int, default=7, help='分析天数 (default: 7)')
    parser.add_argument('--min-cost', type=float, default=1.0, help='最小花费 USD (default: 1)')
    parser.add_argument('--output', type=str, default='/tmp/search_terms_all.json', help='输出文件')
    parser.add_argument('--account', type=str, default=None, help='只分析指定账户')
    
    args = parser.parse_args()
    
    logger.info('=' * 60)
    logger.info('批量搜索词分析工具')
    logger.info('=' * 60)
    
    client = get_gads_client()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    logger.info(f'分析范围: {start_date} ~ {end_date}')
    logger.info(f'最小花费: ${args.min_cost}')
    logger.info('')
    
    all_results = {
        'date_range': {'start': start_date, 'end': end_date},
        'accounts': []
    }
    
    accounts_to_check = {args.account: ACCOUNTS[args.account]} if args.account else ACCOUNTS
    
    total_campaigns = 0
    
    for customer_id, account_info in accounts_to_check.items():
        logger.info(f'▶ 检查账户: {account_info["name"]} ({customer_id})')
        
        # 获取有花费的campaigns
        campaigns = get_active_campaigns_with_spend(client, customer_id, args.days, args.min_cost)
        
        if not campaigns:
            logger.info(f'  无有花费的campaign')
            continue
        
        logger.info(f'  发现 {len(campaigns)} 个有花费的campaign')
        
        account_result = {
            'account_id': customer_id,
            'account_name': account_info['name'],
            'campaigns': []
        }
        
        for camp in campaigns:
            campaign_id = str(camp['id'])
            campaign_name = camp['name']
            spend = camp['cost']
            
            logger.info(f'    ▶ {campaign_name[:50]}...')
            
            # 获取搜索词
            search_terms = get_search_terms(client, customer_id, campaign_id, start_date, end_date)
            
            if not search_terms:
                logger.info(f'      无搜索词')
                continue
            
            logger.info(f'      获取到 {len(search_terms)} 个搜索词')
            
            # 分析
            analysis = analyze_with_rules(campaign_name, search_terms)
            
            irrelevant = analysis.get('irrelevant', [])
            suggested_negatives = [item['term'] for item in irrelevant]
            
            # 输出
            logger.info(f'      相关: {len(analysis.get("relevant", []))}, 不相关: {len(irrelevant)}')
            
            if suggested_negatives:
                logger.info(f'      建议否定: {suggested_negatives[:3]}')
            
            campaign_result = {
                'campaign_id': campaign_id,
                'campaign_name': campaign_name,
                'spend': round(spend, 2),
                'total_terms': len(search_terms),
                'relevant': analysis.get('relevant', []),
                'irrelevant': irrelevant,
                'suggested_negatives': suggested_negatives,
                'summary': analysis.get('summary', '')
            }
            
            account_result['campaigns'].append(campaign_result)
            total_campaigns += 1
        
        all_results['accounts'].append(account_result)
    
    # 保存
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    logger.info('')
    logger.info('=' * 60)
    logger.info(f'完成! 共分析了 {total_campaigns} 个广告系列')
    logger.info(f'结果保存到: {args.output}')
    
    # 生成飞书markdown
    generate_feishu_doc(all_results)
    
    return all_results


def generate_feishu_doc(results: Dict):
    """生成飞书文档格式"""
    
    md_lines = []
    md_lines.append(f"# 📊 搜索词报告分析\n")
    md_lines.append(f"**时间范围**: {results['date_range']['start']} ~ {results['date_range']['end']}\n")
    md_lines.append(f"**更新于**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    md_lines.append("")
    
    total_negatives = 0
    
    for account in results['accounts']:
        md_lines.append(f"## 📁 {account['account_name']}\n")
        
        if not account['campaigns']:
            md_lines.append("*无有花费的广告系列*\n")
            continue
        
        for camp in account['campaigns']:
            camp_name = camp['campaign_name']
            negatives = camp.get('suggested_negatives', [])
            
            md_lines.append(f"### {camp_name[:60]}...")
            md_lines.append(f"- Campaign ID: `{camp['campaign_id']}`")
            md_lines.append(f"- 花费: ${camp['spend']:.2f}")
            md_lines.append(f"- 搜索词数: {camp['total_terms']}")
            md_lines.append(f"- 相关: {len(camp.get('relevant', []))}, 不相关: {len(negatives)}")
            
            if negatives:
                md_lines.append("**⚠️ 建议否定:**")
                for neg in negatives[:5]:
                    if isinstance(neg, dict):
                        md_lines.append(f"- `{neg['term']}` - {neg['reason']}")
                    else:
                        md_lines.append(f"- `{neg}`")
            
            md_lines.append("")
            total_negatives += len(negatives)
    
    md_lines.append(f"---\n")
    md_lines.append(f"*共 {total_negatives} 个搜索词需要添加否定词*")
    
    md_content = '\n'.join(md_lines)
    
    # 保存md
    md_path = '/tmp/search_terms_all.md'
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    logger.info(f'飞书文档预览: {md_path}')
    print('')
    print(md_content)