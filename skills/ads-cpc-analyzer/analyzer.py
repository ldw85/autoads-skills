#!/usr/bin/env python3
"""
Google Ads CPC Analyzer Skill
=============================

Analyzes Google Ads campaigns to determine:
1. Which campaigns should have CPC increased
2. Which campaigns should have CPC decreased
3. Which campaigns should have daily budget increased

Usage:
    python3 analyzer.py --account 6052559425
    python3 analyzer.py --all
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("cpc_analyzer")

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "autoads"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "autoads" / "archer-roi"))


def load_price_cache() -> Dict[str, dict]:
    """Load ASIN price cache"""
    cache_file = Path("/root/.openclaw/workspace/autoads/asin_prices.json")
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load price cache: {e}")
    return {}


def calculate_max_cpc(price: float, commission_rate: float = 0.075) -> float:
    """Calculate max CPC: price × commission_rate / 50 × 6.8 × 0.9"""
    return price * commission_rate / 50 * 6.8 * 0.9


def get_network_from_campaign_name(name: str) -> str:
    """Determine network from campaign name"""
    name_lower = name.lower()
    if "yeahpromos" in name_lower or name_lower.startswith("y"):
        return "yeahpromos"
    elif "archer" in name_lower or "betta" in name_lower or "bcan" in name_lower or "midland" in name_lower:
        return "archer"
    return "unknown"


def get_asin_from_url(url: str) -> Optional[str]:
    """Extract ASIN from URL"""
    import re
    match = re.search(r'/dp/([A-Z0-9]{10})', url, re.IGNORECASE)
    return match.group(1) if match else None


def analyze_account(customer_id: str) -> Dict:
    """Analyze a single Google Ads account"""
    from runner import load_google_ads_credentials, load_credentials
    from networks.yeahpromos import YeahPromosClient
    from networks.archer import ArcherClient
    
    logger.info(f"Analyzing account: {customer_id}")
    
    # Load Google Ads client
    gads_client, config = load_google_ads_credentials()
    if not gads_client:
        logger.error("Failed to load Google Ads client")
        return {}
    
    ga_service = gads_client.client.get_service("GoogleAdsService")
    
    # Get campaign data with costs
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.target_spend.cpc_bid_ceiling_micros,
            metrics.cost_micros,
            metrics.clicks,
            metrics.impressions,
            ad_group_ad.ad.id,
            ad_group_ad.ad.final_urls
        FROM ad_group_ad
        WHERE campaign.status = 'ENABLED'
        AND metrics.cost_micros > 0
    """
    
    try:
        results = gads_client.search(query, customer_id)
    except Exception as e:
        logger.error(f"Google Ads query failed: {e}")
        return {}
    
    # Aggregate campaign data
    campaign_data = {}
    for row in results:
        campaign_id = str(row.campaign.id)
        cost = row.metrics.cost_micros / 1000000
        clicks = row.metrics.clicks
        cpc_ceiling = (row.campaign.target_spend.cpc_bid_ceiling_micros or 0) / 1000000
        final_urls = list(row.ad_group_ad.ad.final_urls) if row.ad_group_ad.ad.final_urls else []
        
        asins = set()
        for url in final_urls:
            asin = get_asin_from_url(url)
            if asin:
                asins.add(asin)
        
        if campaign_id not in campaign_data:
            campaign_data[campaign_id] = {
                'name': row.campaign.name,
                'cost': cost,
                'clicks': clicks,
                'cpc_ceiling': cpc_ceiling,
                'asins': asins
            }
        else:
            campaign_data[campaign_id]['cost'] += cost
            campaign_data[campaign_id]['clicks'] += clicks
            campaign_data[campaign_id]['asins'].update(asins)
    
    # Load price cache
    price_cache = load_price_cache()
    logger.info(f"Loaded {len(price_cache)} prices from cache")
    
    # Get affiliate orders for price and sales data
    creds = load_credentials()
    affiliate_data = {}  # asin -> {orders, sales, confirmed_sales, confirmed_orders}
    
    # Archer
    try:
        if creds.get("archer", {}).get("username"):
            client = ArcherClient(creds["archer"]["username"], creds["archer"]["password"])
            if client.authenticate():
                orders = client.fetch_orders(days=30)
                for o in orders:
                    if o.asin not in affiliate_data:
                        affiliate_data[o.asin] = {'orders': 0, 'sales': 0, 'confirmed_orders': 0, 'confirmed_sales': 0}
                    affiliate_data[o.asin]['orders'] += 1
                    if o.amount > 0:
                        affiliate_data[o.asin]['sales'] += o.amount
                        affiliate_data[o.asin]['confirmed_orders'] += 1
                        affiliate_data[o.asin]['confirmed_sales'] += o.amount
    except Exception as e:
        logger.warning(f"Archer fetch error: {e}")
    
    # YeahPromos
    try:
        if creds.get("yeahpromos", {}).get("token"):
            client = YeahPromosClient(creds["yeahpromos"]["token"], creds["yeahpromos"]["site_id"])
            if client.authenticate():
                orders = client.fetch_orders(days=30)
                for o in orders:
                    if o.asin not in affiliate_data:
                        affiliate_data[o.asin] = {'orders': 0, 'sales': 0, 'confirmed_orders': 0, 'confirmed_sales': 0}
                    affiliate_data[o.asin]['orders'] += 1
                    if o.amount > 0:
                        affiliate_data[o.asin]['sales'] += o.amount
                        affiliate_data[o.asin]['confirmed_orders'] += 1
                        affiliate_data[o.asin]['confirmed_sales'] += o.amount
    except Exception as e:
        logger.warning(f"YeahPromos fetch error: {e}")
    
    # Analyze each campaign
    cpc_increase = []  # Should increase CPC
    cpc_decrease = []  # Should decrease CPC
    budget_increase = []  # Should increase daily budget
    should_pause = []  # Should pause
    
    for cid, data in sorted(campaign_data.items(), key=lambda x: -x[1]['cost']):
        if data['cost'] < 1:  # Skip low spend
            continue
        
        asins = list(data['asins'])
        if not asins:
            continue
        
        asin = asins[0]  # Primary ASIN
        network = get_network_from_campaign_name(data['name'])
        
        # Get price - priority: cache > affiliate confirmed orders
        price = None
        if asin in price_cache:
            price = price_cache[asin].get('price')
        elif asin in affiliate_data:
            ad = affiliate_data[asin]
            # Use confirmed sales to calculate average price
            if ad.get('confirmed_orders', 0) > 0 and ad.get('confirmed_sales', 0) > 0:
                price = ad['confirmed_sales'] / ad['confirmed_orders']
        
        # Get affiliate metrics
        ad_data = affiliate_data.get(asin, {'orders': 0, 'sales': 0, 'confirmed_orders': 0, 'confirmed_sales': 0})
        orders = ad_data.get('orders', 0)
        sales = ad_data.get('sales', 0)
        confirmed_orders = ad_data.get('confirmed_orders', 0)
        confirmed_sales = ad_data.get('confirmed_sales', 0)
        
        current_cpc = data['cpc_ceiling']
        cost_usd = data['cost'] / 6.8  # Convert CNY to USD
        
        # Calculate max CPC if we have price
        max_cpc = calculate_max_cpc(price) if price else None
        
        # Determine recommendations
        entry = {
            'campaign_id': cid,
            'campaign_name': data['name'][:60],
            'asin': asin,
            'network': network,
            'cost': data['cost'],
            'cost_usd': cost_usd,
            'clicks': data['clicks'],
            'current_cpc': current_cpc,
            'max_cpc': max_cpc,
            'price': price,
            'orders': orders,
            'confirmed_orders': confirmed_orders,
            'sales': sales,
            'confirmed_sales': confirmed_sales
        }
        
        if max_cpc and max_cpc > 0:
            # CPC analysis
            if current_cpc < max_cpc * 0.9:
                entry['gap'] = max_cpc - current_cpc
                entry['gap_pct'] = (max_cpc - current_cpc) / max_cpc * 100
                cpc_increase.append(entry)
            elif current_cpc > max_cpc * 1.2:
                entry['gap'] = current_cpc - max_cpc
                entry['gap_pct'] = (current_cpc - max_cpc) / max_cpc * 100
                cpc_decrease.append(entry)
        
        # Budget analysis (if has orders - confirmed OR pending - and positive ROI)
        # For pending orders: estimate sales = pending_orders * avg_price (from confirmed orders)
        if orders > 0 and confirmed_sales > 0 and cost_usd > 0:
            # Calculate avg price from confirmed orders
            avg_price = confirmed_sales / confirmed_orders if confirmed_orders > 0 else 0
            
            # Estimate sales from pending orders
            pending_orders = orders - confirmed_orders
            estimated_pending_sales = pending_orders * avg_price
            
            # Total estimated sales
            total_estimated_sales = confirmed_sales + estimated_pending_sales
            
            commission = total_estimated_sales * 0.075
            roi = commission / cost_usd * 100
            entry['roi'] = roi
            entry['estimated_total_sales'] = total_estimated_sales
            entry['pending_orders_est'] = pending_orders
            entry['avg_price'] = avg_price
            
            if roi > 100:
                budget_increase.append(entry)
        elif confirmed_orders > 0 and confirmed_sales > 0 and cost_usd > 0:
            # Only confirmed orders
            commission = confirmed_sales * 0.075
            roi = commission / cost_usd * 100
            entry['roi'] = roi
            entry['estimated_total_sales'] = confirmed_sales
            if roi > 100:
                budget_increase.append(entry)
        
        # Pause analysis (no confirmed orders with high spend)
        if confirmed_orders == 0 and orders > 0 and cost_usd > 30:
            entry['reason'] = f"{orders}个订单(全Pending), 花费${cost_usd:.2f}"
            should_pause.append(entry)
        elif confirmed_orders == 0 and orders == 0 and cost_usd > 5:
            entry['reason'] = f"0订单, 花费${cost_usd:.2f}"
            should_pause.append(entry)
    
    return {
        'account_id': customer_id,
        'cpc_increase': cpc_increase,
        'cpc_decrease': cpc_decrease,
        'budget_increase': budget_increase,
        'should_pause': should_pause
    }


def format_report(results: Dict) -> str:
    """Format analysis results as readable report"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"📊 Google Ads 广告账户分析报告")
    lines.append(f"账户: {results['account_id']}")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    
    # CPC Increase
    lines.append("\n🔴 CPC应提升的广告系列 (当前CPC偏低，可能错失转化):")
    lines.append("-" * 80)
    if results['cpc_increase']:
        for e in sorted(results['cpc_increase'], key=lambda x: -x.get('gap', 0)):
            price_info = f", 均价${e['price']:.2f}" if e.get('price') else ""
            gap_info = f", 差距+${e['gap']:.2f} (+{e['gap_pct']:.1f}%)" if e.get('gap') else ""
            lines.append(f"  • {e['campaign_name']}")
            lines.append(f"    ASIN: {e['asin']}{price_info}")
            lines.append(f"    当前CPC: ${e['current_cpc']:.4f}, 最大合理: ${e['max_cpc']:.4f}{gap_info}")
    else:
        lines.append("  (无)")
    
    # CPC Decrease
    lines.append("\n🟢 CPC应降低的广告系列 (当前CPC偏高，建议优化):")
    lines.append("-" * 80)
    if results['cpc_decrease']:
        for e in sorted(results['cpc_decrease'], key=lambda x: -x.get('gap', 0)):
            price_info = f", 均价${e['price']:.2f}" if e.get('price') else ""
            gap_info = f", 差距-${e['gap']:.2f} (-{e['gap_pct']:.1f}%)" if e.get('gap') else ""
            lines.append(f"  • {e['campaign_name']}")
            lines.append(f"    ASIN: {e['asin']}{price_info}")
            lines.append(f"    当前CPC: ${e['current_cpc']:.4f}, 最大合理: ${e['max_cpc']:.4f}{gap_info}")
    else:
        lines.append("  (无)")
    
    # Budget Increase
    lines.append("\n💰 应扩大每日预算的广告系列 (ROI > 100%，可加大投入):")
    lines.append("-" * 80)
    if results['budget_increase']:
        for e in sorted(results['budget_increase'], key=lambda x: -x.get('roi', 0)):
            pending_info = f", Pending估算订单{e.get('pending_orders_est', 0)}个" if e.get('pending_orders_est', 0) > 0 else ""
            lines.append(f"  • {e['campaign_name']}")
            lines.append(f"    ASIN: {e['asin']}, ROI: {e['roi']:.1f}%")
            lines.append(f"    确认订单: {e.get('confirmed_orders', 0)}, 确认销售额: ${e.get('confirmed_sales', 0):.2f}{pending_info}")
    else:
        lines.append("  (无)")
    
    # Should Pause
    lines.append("\n⚠️ 应暂停/缩量的广告系列 (无确认订单或高花费):")
    lines.append("-" * 80)
    if results['should_pause']:
        for e in sorted(results['should_pause'], key=lambda x: -x.get('cost_usd', 0)):
            lines.append(f"  • {e['campaign_name']}")
            lines.append(f"    ASIN: {e['asin']}, {e.get('reason', '')}")
    else:
        lines.append("  (无)")
    
    lines.append("\n" + "=" * 80)
    lines.append("说明: 最大合理CPC = 商品价格 × 7.5%佣金率 / 50 / 6.8汇率 × 0.9安全系数")
    lines.append("      ROI = (确认销售额 + Pending估算销售额) × 7.5% / 广告花费 × 100%")
    lines.append("      Pending估算销售额 = Pending订单数 × 确认订单均价")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Google Ads CPC Analyzer")
    parser.add_argument("--account", "-a", help="Specific account ID to analyze")
    parser.add_argument("--accounts", nargs="+", default=["3674729801", "6052559425"], help="Account IDs")
    parser.add_argument("--output", "-o", help="Output file")
    
    args = parser.parse_args()
    
    accounts = [args.account] if args.account else args.accounts
    
    all_results = {}
    for account_id in accounts:
        results = analyze_account(account_id)
        if results:
            all_results[account_id] = results
    
    # Format and output
    reports = []
    for account_id, results in all_results.items():
        report = format_report(results)
        reports.append(report)
        print(report)
    
    # Save to file if specified
    if args.output:
        with open(args.output, 'w') as f:
            f.write("\n\n".join(reports))
        logger.info(f"Report saved to {args.output}")
    
    return all_results


if __name__ == "__main__":
    main()
