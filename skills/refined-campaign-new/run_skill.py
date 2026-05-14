#!/usr/bin/env python3
"""
Refined Campaign New Skill - Create NEW Campaign from Scratch

Creates a brand NEW refined/layered keyword campaign in Google Ads.
Uses AI to generate new ad creative, does not rely on existing ads.

Usage:
    python3 run_skill.py --url "https://..." --brand ROVE --customer-id 6052559425 ...
"""

import sys
import os
import argparse
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

AUTOADS_DIR = '/root/.openclaw/workspace/autoads'
os.chdir(AUTOADS_DIR)
sys.path.insert(0, AUTOADS_DIR)

from src.refined_campaign_creator import RefinedCampaignCreator


def main():
    parser = argparse.ArgumentParser(
        description='Refined Campaign New Skill - Create NEW Layered Campaign',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required
    parser.add_argument('--url', required=True, help='Product URL (Amazon)')
    parser.add_argument('--brand', required=True, help='Brand name')
    parser.add_argument('--product-name', required=True, help='Product name')
    parser.add_argument('--customer-id', required=True, dest='customer_id', help='Google Ads customer ID')
    
    # Optional
    parser.add_argument('--campaign-name', help='Campaign name (auto-generated if not provided)')
    parser.add_argument('--product-description', default='', help='Product description for AI')
    parser.add_argument('--price', type=float, help='Product price (USD)')
    parser.add_argument('--commission-rate', type=float, dest='commission_rate', help='Commission rate (decimal)')
    parser.add_argument('--country', default='US', help='Target country (default: US)')
    parser.add_argument('--budget', type=float, default=20.0, help='Daily budget (default: 20)')
    
    args = parser.parse_args()
    
    # Validate
    if not args.price or args.price <= 0:
        logger.error("Price is required and must be > 0")
        sys.exit(1)
    if args.commission_rate is None:
        logger.error("Commission rate is required")
        sys.exit(1)
    
    print("="*70)
    print("🔧 Refined Campaign New Skill - Creating NEW Layered Campaign")
    print("="*70)
    print(f"\n📋 URL: {args.url}")
    print(f"📋 Brand: {args.brand}")
    print(f"📋 Product: {args.product_name}")
    print(f"📋 Price: ${args.price}")
    print(f"📋 Commission: {args.commission_rate * 100}%")
    print(f"📋 Budget: ${args.budget}/day")
    print(f"📋 Country: {args.country}")
    
    # Create campaign
    creator = RefinedCampaignCreator()
    
    campaign_name = args.campaign_name
    if not campaign_name:
        campaign_name = f"{args.brand} {args.product_name[:30]} - {args.country}"
    
    product_description = args.product_description
    if not product_description:
        product_description = f"{args.brand} {args.product_name}"
    
    result = creator.create_layered_campaign(
        customer_id=args.customer_id,
        campaign_name=campaign_name,
        product_url=args.url,
        product_description=product_description,
        brand=args.brand,
        product_name=args.product_name,
        price=args.price,
        commission_rate=args.commission_rate,
        country=args.country,
        budget=args.budget
    )
    
    print("\n" + "="*70)
    if result['success']:
        print("✅ SUCCESS: Campaign Created")
        print("="*70)
        print(f"\n📊 Campaign ID: {result['campaign_id']}")
        print(f"📊 Layers Created:")
        for layer, data in result.get('layers', {}).items():
            if isinstance(data, dict):
                status = '✅' if data.get('ad_group_id') else '❌'
                print(f"  {status} {layer}: {data.get('name')} - {data.get('keywords_added')} keywords")
    else:
        print("❌ FAILED")
        print(f"\nErrors: {result.get('errors', [])}")
        sys.exit(1)


if __name__ == '__main__':
    main()