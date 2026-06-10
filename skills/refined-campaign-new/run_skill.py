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
    parser.add_argument('--rating', help='Product rating (e.g., "4.6")')
    parser.add_argument('--reviews-count', type=int, dest='reviews_count', help='Number of reviews (e.g., 21000)')
    parser.add_argument('--network', default=None, help='Affiliate network name (e.g. archer, yeahpromos, partnerboost). Default: from creator init')
    parser.add_argument('--seed-keywords', dest='seed_keywords', default=None,
                        help='Comma-separated seed keywords (OPTIONAL). When provided, these '
                             'are GUARANTEED to be in core_keywords. Typical content: brand name, '
                             'product model, important variants. AI-extracted keywords added on top. '
                             'Example: --seed-keywords "ROVE,R2-4K,ROVE R2-4K DUAL"')
    parser.add_argument('--product-model', dest='product_model', default=None,
                        help='Comma-separated L0 product_model keywords (OPTIONAL, 2026-06-08 L0/L1 '
                             'optimization). L0 (Brand_Model_Strict) requires brand + at least one of '
                             'these model keywords. AI expands with same-semantic variants only '
                             '(spelling/case/spacing), never other brand product lines. '
                             'Example: --product-model "X431 PROS V 5.0,X431 PROS,X431,creader"')
    parser.add_argument('--dry-run', action='store_true', dest='dry_run',
                        help='Dry run: only generate AI keywords + filter via ad_prevalidator. '
                             'Do NOT create any Google Ads campaign. Print filtered keywords for review.')
    
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
    print(f"📋 Network: {args.network or 'partnerboost (default)'}")
    
    # Create campaign
    creator = RefinedCampaignCreator(network=args.network)
    
    campaign_name = args.campaign_name
    if not campaign_name:
        campaign_name = f"{args.brand} {args.product_name[:30]} - {args.country}"
    
    product_description = args.product_description
    if not product_description:
        product_description = f"{args.brand} {args.product_name}"
    
    # Parse seed keywords (comma-separated string → list)
    seed_keywords = None
    if args.seed_keywords:
        seed_keywords = [s.strip() for s in args.seed_keywords.split(',') if s.strip()]
        logger.info(f"User-provided seed keywords ({len(seed_keywords)}): {seed_keywords[:5]}...")
    
    # Parse product_model keywords (comma-separated string → list)
    product_model = None
    if args.product_model:
        product_model = [s.strip() for s in args.product_model.split(',') if s.strip()]
        logger.info(f"User-provided L0 product_model keywords ({len(product_model)}): {product_model}")

    # Create campaign
    creator = RefinedCampaignCreator(network=args.network)

    # ===== DRY-RUN MODE: 仅生成 + 过滤, 不创建 Campaign =====
    if args.dry_run:
        print("\n" + "="*70)
        print("🧪 DRY-RUN MODE: 仅生成 + 过滤, 不创建 Google Ads Campaign")
        print("="*70)
        ad_creative = creator.generate_ad_creative(
            product_description=product_description,
            product_url=args.url,
            brand=args.brand,
            product_name=args.product_name,
            price=args.price,
            commission_rate=args.commission_rate,
            product_rating=args.rating,
            product_reviews_count=args.reviews_count,
            seed_keywords=seed_keywords
        )
        core = ad_creative.get('core_keywords', [])
        long_tail = ad_creative.get('long_tail_keywords', [])
        all_kws = core + long_tail
        print(f"\n📝 AI Generated: {len(core)} core + {len(long_tail)} long-tail = {len(all_kws)} total")
        print(f"\n🔧 Running validate_and_filter_keywords (ad_prevalidator 201 AMAZON_PLATFORM_TOKENS)...")
        from src.ad_prevalidator import validate_and_filter_keywords
        valid, filtered = validate_and_filter_keywords([{'text': k} for k in all_kws])
        print(f"\n{'='*70}")
        print(f"❌ FILTERED (DROP): {len(filtered)}")
        print("="*70)
        for f in filtered:
            print(f"  - {f['text']!r}: {f['reason']}")
        print(f"\n{'='*70}")
        print(f"✅ KEPT (KEEP): {len(valid)}")
        print("="*70)
        for v in valid:
            print(f"  - {v['text']!r}")
        print(f"\n🧪 DRY-RUN COMPLETE: {len(all_kws)} → {len(valid)} ({len(filtered)} filtered)")
        sys.exit(0)

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
        budget=args.budget,
        product_rating=args.rating,
        product_reviews_count=args.reviews_count,
        network=args.network,
        seed_keywords=seed_keywords,
        product_model=product_model
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