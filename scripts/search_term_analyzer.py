#!/usr/bin/env python3
"""
搜索词质量分析脚本 - 完整版
============================
支持:
1. 分析指定广告系列
2. 分析所有有花费的广告系列  
3. 每2小时定时任务模式
4. 发送飞书通知

Usage:
    python3 search_term_analyzer.py --campaign-id 23792756828 --customer-id 4772859239
    python3 search_term_analyzer.py --all-spending --dry-run
    python3 search_term_analyzer.py --cron  # 定时任务模式
"""

import sys
import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Setup paths
SCRIPT_DIR = Path(__file__).parent
AUTOADS_DIR = SCRIPT_DIR.parent / 'autoads'
sys.path.insert(0, str(AUTOADS_DIR))
sys.path.insert(0, str(AUTOADS_DIR / 'src'))

from src.google_ads_client import GoogleAdsClientWrapper


# ============================================================
# 分析规则
# ============================================================

# ============================================================
# 分析规则
# 
# 判断逻辑：
#   1. 强购买意图词（amazon + 产品词）→ 加价购买，不是否定
#   2. 产品类型完全不匹配 → 加否定（OFFICE_PRINTER, WRONG_TYPE）
#   3. 价格/购物意图词 → 要结合产品上下文，不是简单否定
#   4. 竞品品牌 → 区分是本品类竞品还是跨品类
# ============================================================

# 核心关键词识别（这些产品词如果出现在搜索中，应该识别为相关而非否定）
# 格式：(产品词, 产品分类)
PRODUCT_KEYWORDS = {
    'AIR_FRYER': ['air fryer', 'airfryer', 'air fryer oven', 'crisper', 'deep fryer'],
    'DASH_CAM': ['dash cam', 'dashcam', 'dashboard camera', 'car camera', 'dash camera', 'car dash camera'],
    'FOOT_MASSAGER': ['foot massager', 'foot massager electric', 'foot spa', 'foot massage machine'],
    'PHOTO_PRINTER': ['photo printer', 'picture printer', 'portable printer', 'mini printer', 'phone printer'],
    'ROBOT_VACUUM': ['robot vacuum', 'robot cleaner', 'roborock', 'roomba', 'vacuum robot'],
    'POOL_CLEANER': ['pool cleaner', 'pool vacuum', 'swimming pool cleaner', 'robot pool cleaner', 'ipper', ' AIPER'],
    'MATTRESS': ['mattress', 'mattress topper', 'memory foam mattress'],
    'BLUETOOTH_SPEAKER': ['bluetooth speaker', 'wireless speaker', 'portable speaker', 'waterproof speaker'],
    'HEADPHONES': ['headphones', 'earphones', 'wireless headphones', 'bluetooth headphones'],
    'SMART_WATCH': ['smart watch', 'fitness tracker', 'wearable', 'watch band'],
}

# 强购买意图平台词 → 应该加价购买，不是否定
STRONG_BUYING_INTENT_PATTERNS = [
    (r'\bamazon\s+(air fryer|airfryer|dash cam|dashcam|foot massager|photo printer|printer|lamp|headphones|speaker)\b', 'STRONG_BUYING'),
    (r'\b(air fryer|dash cam|foot massager|photo printer|mattress|headphones|speaker)\s+amazon\b', 'STRONG_BUYING'),
    (r'\bwalmart\s+(air fryer|dash cam|foot massager|photo printer|printer)\b', 'STRONG_BUYING'),
    (r'\b(best buy|costco|target)\s+(air fryer|dash cam|foot massager|photo printer|printer)\b', 'STRONG_BUYING'),
]

# 应该加否定的产品类型完全不匹配词（针对打印机类产品）
# 注意：对于空气炸锅/行车记录仪产品，这些词可能完全相关
IRRELEVANT_PATTERNS = [
    # 办公打印机类型（仅针对PHOTO_PRINTER类产品）
    (r'\b(laser|laserjet|inkjet|officejet|deskjet|envy|pageside)\b', 'OFFICE_PRINTER', '办公打印机'),
    (r'\b(brother|mfc|dcp|intellifax)\b', 'OFFICE_PRINTER', 'Brother办公打印机'),
    (r'\b(canonselphy|canon pixma|canon g\d|canon tr|canon ts|canon imageclass|canon mf|canon cp\d|canon ivy)\b', 'OFFICE_PRINTER', 'Canon办公打印机'),
    (r'\b(epson ecotank|epson et|epson l\d|epson wf|epson xp|epson expression|epson stylus|epson surecolor|epson workforce)\b', 'OFFICE_PRINTER', 'Epson办公打印机'),
    (r'\b(hp printer|hp deskjet|hp envy|hp officejet|hp laserjet|hp photosmart|hp pagewide)\b', 'OFFICE_PRINTER', 'HP办公打印机'),
    
    # 办公功能词（仅针对PHOTO_PRINTER）
    (r'\b(all in one|all-in-one|multifunction|copier|scanner|fax|automatic document feeder)\b', 'OFFICE_PRINTER', '办公多功能一体机'),
    
    # 错误产品类型（针对打印机类产品）
    (r'\b(sublimat|dtf|sublimation printer)\b', 'WRONG_TYPE', '热转印设备'),
    (r'\b(ecotank|megatank|smart tank)\b', 'OFFICE_PRINTER', '墨仓式打印机'),
]

# 跨品类竞品品牌（需要否定）
COMPETITOR_BRANDS = {
    'PHOTO_PRINTER': ['canon selphy', 'polaroid printer', 'kodak photo printer', 'hp sprocket', 'fujifilm instax'],
    'AIR_FRYER': [],  # 空气炸锅品类竞品暂不列
    'DASH_CAM': ['garmin dash cam', 'nextbase', 'thinkware'],
    'FOOT_MASSAGER': [],
    'ROBOT_VACUUM': ['roomba', 'neato', 'ecovacs', 'shark iq'],
    'POOL_CLEANER': [],
}

CATEGORY_NAMES = {
    'OFFICE_PRINTER': '🏢 办公打印机',
    'SHOPPING': '🛒 价格比价（需人工判断）',
    'PLATFORM': '🛍️ 购物平台搜索',
    'WRONG_TYPE': '❌ 错误类型',
    'BRAND': '❌ 竞品品牌',
    'STRONG_BUYING': '✅ 强购买意图（加价购买）',
}

# ============================================================
# 账户配置
# ============================================================

ACCOUNTS = [
    ('6052559425', 'YeahPromos'),
    ('4772859239', 'PartnerBoost'),
    ('3674729801', 'Archer-Yang'),
    ('6660356395', 'Archer'),
]


# ============================================================
# 核心函数
# ============================================================

def get_campaigns_with_spending(client, customer_id, days=7, min_cost=1):
    """获取过去N天有花费的广告系列"""
    query = f'''
    SELECT campaign.id, campaign.name, campaign.status,
           metrics.cost_micros, metrics.clicks, metrics.impressions
    FROM campaign
    WHERE campaign.status = 'ENABLED'
    AND metrics.cost_micros > {min_cost * 1000000}
    AND segments.date DURING LAST_{days}_DAYS
    ORDER BY metrics.cost_micros DESC
    LIMIT 50
    '''
    gaas = client.client.get_service('GoogleAdsService')
    try:
        response = gaas.search(customer_id=customer_id, query=query)
        campaigns = []
        for row in response:
            cost = row.metrics.cost_micros / 1000000 if row.metrics else 0
            clicks = row.metrics.clicks if row.metrics else 0
            campaigns.append({
                'id': row.campaign.id,
                'name': row.campaign.name,
                'status': row.campaign.status,
                'cost': cost,
                'clicks': clicks,
            })
        return campaigns
    except Exception as e:
        print(f"Error getting campaigns for {customer_id}: {e}")
        return []


def get_search_terms(client, customer_id, campaign_id, days=7):
    """获取广告系列的搜索词"""
    query = f'''
    SELECT 
        search_term_view.search_term,
        search_term_view.status,
        ad_group.id,
        ad_group.name,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        metrics.conversions
    FROM search_term_view
    WHERE campaign.id = {campaign_id}
    AND metrics.cost_micros > 0
    AND segments.date DURING LAST_{days}_DAYS
    ORDER BY metrics.cost_micros DESC
    LIMIT 5000
    '''
    gaas = client.client.get_service('GoogleAdsService')
    try:
        response = gaas.search(customer_id=customer_id, query=query)
        terms = []
        for row in response:
            term = row.search_term_view.search_term if row.search_term_view else ''
            if not term:
                continue
            terms.append({
                'term': term.lower().strip(),
                'ad_group_name': row.ad_group.name if row.ad_group else '',
                'impressions': row.metrics.impressions if row.metrics else 0,
                'clicks': row.metrics.clicks if row.metrics else 0,
                'cost': row.metrics.cost_micros / 1000000 if row.metrics else 0,
                'conversions': row.metrics.conversions if row.metrics else 0,
            })
        return terms
    except Exception as e:
        print(f"Error getting search terms for campaign {campaign_id}: {e}")
        return []


def detect_product_category(campaign_name):
    """从广告系列名称检测产品类别"""
    name_lower = campaign_name.lower()
    
    if 'photo printer' in name_lower or 'printer' in name_lower or 'liene' in name_lower:
        return 'PHOTO_PRINTER'
    if 'air fryer' in name_lower or 'chefman' in name_lower:
        return 'AIR_FRYER'
    if 'dash cam' in name_lower or 'rove' in name_lower:
        return 'DASH_CAM'
    if 'foot massager' in name_lower:
        return 'FOOT_MASSAGER'
    if 'robot vacuum' in name_lower or 'roborock' in name_lower or 'vacuum' in name_lower:
        return 'ROBOT_VACUUM'
    if 'pool cleaner' in name_lower or 'ipper' in name_lower:
        return 'POOL_CLEANER'
    if 'mattress' in name_lower:
        return 'MATTRESS'
    if 'speaker' in name_lower or 'bluetooth' in name_lower:
        return 'BLUETOOTH_SPEAKER'
    if 'headphone' in name_lower or 'earphone' in name_lower:
        return 'HEADPHONES'
    
    return 'GENERIC'


def analyze_search_term(term, campaign_name=''):
    """分析单个搜索词，考虑产品类别和购买意图"""
    term_lower = term.lower()
    product_category = detect_product_category(campaign_name)
    
    matched_issues = []
    recommendations = []  # 存储建议（加价购买 vs 加否定）
    
    # Step 1: 检查强购买意图平台词 → 应该加价购买，不是否定
    for pattern, category in STRONG_BUYING_INTENT_PATTERNS:
        match = re.search(pattern, term_lower, re.IGNORECASE)
        if match:
            matched_issues.append({
                'category': 'STRONG_BUYING',
                'description': '强购买意图平台搜索',
                'matched': match.group(),
            })
            recommendations.append({
                'action': 'BID_UP',
                'reason': '强购买意图（Amazon/Walmart搜索），应加价购买',
                'term': term,
            })
    
    # Step 2: 检查核心产品词 → 应该是相关词，不是否定
    product_keywords = PRODUCT_KEYWORDS.get(product_category, [])
    if product_keywords:
        for kw in product_keywords:
            if kw.lower() in term_lower:
                # 检查是否有明确的负面意图（如价格比价、错误类型）
                has_negative = False
                for pattern, category, desc in IRRELEVANT_PATTERNS:
                    if re.search(pattern, term_lower, re.IGNORECASE):
                        has_negative = True
                        matched_issues.append({
                            'category': category,
                            'description': desc,
                            'matched': re.search(pattern, term_lower, re.IGNORECASE).group(),
                        })
                        
                if not has_negative:
                    # 核心产品词匹配，但没有负面意图 → 标记为相关
                    recommendations.append({
                        'action': 'KEEP',
                        'reason': f'核心产品词"{kw}"匹配，相关',
                        'term': term,
                    })
    
    # Step 3: 检查应该否定的模式（产品类型完全不匹配）
    for pattern, category, description in IRRELEVANT_PATTERNS:
        match = re.search(pattern, term_lower, re.IGNORECASE)
        if match:
            # 检查这个类别是否与当前产品相关
            should_negate = False
            
            if category == 'OFFICE_PRINTER':
                # 办公打印机类型 → 对PHOTO_PRINTER才否定，其他品类可能相关
                if product_category == 'PHOTO_PRINTER':
                    should_negate = True
            elif category == 'WRONG_TYPE':
                # 错误产品类型 → 大多数品类都应否定
                should_negate = True
            
            if should_negate:
                matched_issues.append({
                    'category': category,
                    'description': description,
                    'matched': match.group(),
                })
                recommendations.append({
                    'action': 'NEGATIVE',
                    'reason': f'{description}，产品类型不匹配',
                    'term': term,
                })
    
    # Step 4: 检查跨品类竞品品牌
    competitor_brands = COMPETITOR_BRANDS.get(product_category, [])
    for brand in competitor_brands:
        if brand.lower() in term_lower:
            matched_issues.append({
                'category': 'BRAND',
                'description': '竞品品牌',
                'matched': brand,
            })
            recommendations.append({
                'action': 'NEGATIVE',
                'reason': f'竞品品牌"{brand}"：',
                'term': term,
            })
    
    # 判断结果
    # 如果有NEGATIVE建议，则标记为高风险
    has_negative = any(r['action'] == 'NEGATIVE' for r in recommendations)
    has_buying_intent = any(r['action'] == 'BID_UP' for r in recommendations)
    
    return {
        'term': term,
        'campaign_name': campaign_name,
        'product_category': product_category,
        'issues': matched_issues,
        'recommendations': recommendations,
        'is_high_risk': has_negative,
        'has_buying_intent': has_buying_intent,
        'action': 'NEGATIVE' if has_negative else ('BID_UP' if has_buying_intent else 'KEEP'),
    }


def analyze_campaign(client, customer_id, campaign_id, days=7):
    """分析单个广告系列"""
    # Get campaign info
    query = f'''
    SELECT campaign.id, campaign.name
    FROM campaign
    WHERE campaign.id = {campaign_id}
    '''
    gaas = client.client.get_service('GoogleAdsService')
    response = gaas.search(customer_id=customer_id, query=query)
    campaign_name = ''
    for row in response:
        campaign_name = row.campaign.name
    
    # Get search terms
    search_terms = get_search_terms(client, customer_id, campaign_id, days)
    
    if not search_terms:
        return None
    
    # Analyze
    analyzed = []
    high_risk = []
    bid_up_terms = []  # 需要加价的词
    
    for term_data in search_terms:
        result = analyze_search_term(term_data['term'], campaign_name)
        result.update(term_data)
        
        if result['is_high_risk']:
            high_risk.append(result)
        elif result['has_buying_intent']:
            bid_up_terms.append(result)
        analyzed.append(result)
    
    # Sort by cost
    high_risk.sort(key=lambda x: x['cost'], reverse=True)
    
    total_cost = sum(t['cost'] for t in search_terms)
    high_risk_cost = sum(t['cost'] for t in high_risk)
    
    # Group by issue category
    grouped = defaultdict(list)
    for item in high_risk:
        for issue in item['issues']:
            grouped[issue['category']].append({
                'term': item['term'],
                'cost': item['cost'],
                'clicks': item['clicks'],
                'matched': issue['matched'],
            })
    
    return {
        'campaign_id': campaign_id,
        'campaign_name': campaign_name[:80],
        'customer_id': customer_id,
        'total_terms': len(search_terms),
        'total_cost': total_cost,
        'high_risk_count': len(high_risk),
        'high_risk_cost': high_risk_cost,
        'high_risk': high_risk[:30],
        'bid_up_terms': bid_up_terms[:20],  # 需要加价的词
        'grouped': dict(grouped),
        'timestamp': datetime.now().isoformat(),
    }


def format_report(report):
    """格式化单个广告系列报告"""
    if not report:
        return ""
    
    lines = []
    lines.append(f"\n📊 **{report['campaign_name'][:60]}**")
    lines.append(f"   ID: `{report['campaign_id']}` | 搜索词: {report['total_terms']} | 高风险: {report['high_risk_count']}个 (${report['high_risk_cost']:.2f})")
    
    # 显示需要加价的词
    bid_up = report.get('bid_up_terms', [])
    if bid_up:
        lines.append(f"   **✅ 强购买意图词（建议加价购买）:**")
        for item in bid_up[:5]:
            lines.append(f"   • `{item['term'][:40]}` (${item['cost']:.2f}, {item['clicks']}点击)")
    
    if report['grouped']:
        lines.append(f"   **🔴 建议添加否定:**")
        
        for category, items in sorted(report['grouped'].items()):
            cat_name = CATEGORY_NAMES.get(category, category)
            
            # Deduplicate
            seen = set()
            unique = []
            for item in items:
                if item['term'] not in seen:
                    seen.add(item['term'])
                    unique.append(item)
            
            for item in unique[:8]:
                lines.append(f"   • `{item['term'][:40]}` (${item['cost']:.2f}, {item['clicks']}点击)")
    
    return '\n'.join(lines)


def format_full_report(reports, all_spending=False):
    """格式化完整报告"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if all_spending:
        lines = [f"📊 **搜索词质量分析简报** - {timestamp}"]
        lines.append(f"\n分析 {len(reports)} 个有花费的广告系列:")
        
        total_high_risk = sum(r.get('high_risk_count', 0) for r in reports)
        total_high_cost = sum(r.get('high_risk_cost', 0) for r in reports)
        
        lines.append(f"\n汇总: 高风险搜索词 {total_high_risk} 个, 浪费花费 ${total_high_cost:.2f}")
        
        for r in reports:
            # 显示需要加价的词
            bid_up = r.get('bid_up_terms', [])
            if bid_up:
                lines.append(f"\n📊 **{r['campaign_name'][:60]}**")
                lines.append(f"   ID: `{r['campaign_id']}`")
                lines.append(f"   **✅ 强购买意图词（建议加价购买）:**")
                seen = set()
                for item in bid_up:
                    if item['term'] not in seen:
                        seen.add(item['term'])
                        lines.append(f"   • `{item['term'][:40]}` (${item['cost']:.2f}, {item['clicks']}点击)")
            
            if r.get('high_risk_count', 0) > 0:
                lines.append(format_report(r))
        
        return '\n'.join(lines)
    else:
        return format_report(reports[0]) if reports else ""


def send_feishu(message):
    """发送飞书通知"""
    try:
        cmd = [
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', 'chat:oc_f9f4c245ead297586f19ac9f31656564',
            '--message', message
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"飞书通知失败: {e}")
        return False


def save_report(reports, filepath=None):
    """保存报告到文件"""
    if not filepath:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f'/root/.openclaw/workspace/autoads/archer-roi/logs/search_term_report_{timestamp}.json'
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    return filepath


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='搜索词质量分析')
    parser.add_argument('--campaign-id', type=int, help='指定广告系列ID')
    parser.add_argument('--customer-id', type=str, help='Google Ads账户ID')
    parser.add_argument('--all-spending', action='store_true', help='分析所有有花费的广告系列')
    parser.add_argument('--cron', action='store_true', help='定时任务模式（发飞书通知）')
    parser.add_argument('--save', action='store_true', help='保存报告到文件')
    
    args = parser.parse_args()
    
    client = GoogleAdsClientWrapper()
    
    results = []
    
    if args.campaign_id:
        # 分析指定广告系列
        cid = args.customer_id or '4772859239'
        report = analyze_campaign(client, cid, args.campaign_id, days=7)
        if report:
            results.append(report)
            print(format_report(report))
    
    elif args.all_spending or args.cron:
        # 分析所有有花费的广告系列
        for acc_id, acc_name in ACCOUNTS:
            print(f"\n检查账户: {acc_name} ({acc_id})")
            campaigns = get_campaigns_with_spending(client, acc_id, days=7, min_cost=1)
            print(f"  有花费广告系列: {len(campaigns)}")
            
            for camp in campaigns[:15]:  # 最多15个
                if camp['cost'] < 1:
                    continue
                
                report = analyze_campaign(client, acc_id, camp['id'], days=7)
                if report and report.get('high_risk_count', 0) > 0:
                    results.append(report)
        
        if results:
            report_text = format_full_report(results, all_spending=True)
            print(report_text)
            
            if args.cron:
                # 发送飞书通知
                send_feishu(report_text)
                print("\n✅ 飞书通知已发送")
            
            if args.save:
                filepath = save_report(results)
                print(f"\n报告已保存: {filepath}")
        else:
            print("没有发现高风险搜索词")
    
    else:
        print("请指定 --campaign-id 或 --all-spending")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)