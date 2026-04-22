#!/usr/bin/env python3
"""
Autoads Skill - Parameter Validator and Executor

This script is called by AI after it has parsed the user's natural language input.
It validates all required parameters and executes the autoads program.

AI should call this script with explicit parameters, not rely on regex parsing.
"""

import sys
import os
import subprocess
import argparse

# Change to autoads directory
os.chdir('/root/.openclaw/workspace/autoads')


def validate_params(args) -> tuple:
    """Validate all parameters before execution.
    
    Returns: (is_valid, error_message)
    """
    # URL is required
    if not args.url:
        return False, "URL is required (--url)"
    
    url_lower = args.url.lower()
    
    # Amazon URL validation
    if 'amazon.' in url_lower:
        if '?' not in args.url:
            return False, "Amazon URL must include tracking parameters (?maas=...&tag=...)"
        query = args.url.split('?', 1)[1]
        tracking_keys = ['maas', 'tag', 'ref_', 'camp', 'adgroup', 'creative']
        has_tracking = any(k in query.lower() for k in tracking_keys)
        if not has_tracking:
            return False, "Amazon URL missing tracking parameters"
    
    # Commission rate is required
    if not args.commission_rate:
        return False, "Commission rate is required (--commission-rate)"
    
    if args.commission_rate <= 0 or args.commission_rate > 1:
        return False, f"Commission rate must be between 0 and 1 (got {args.commission_rate})"
    
    # Product price is required
    if not args.product_price:
        return False, "Product price is required (--product-price)"
    
    if args.product_price <= 0:
        return False, f"Product price must be positive (got {args.product_price})"
    
    # Customer ID validation
    if args.customer_id:
        if not args.customer_id.isdigit():
            return False, f"Customer ID must be numeric (got {args.customer_id})"
    
    return True, ""


def build_command(args) -> list:
    """Build autoads command from validated arguments."""
    cmd = [
        'python3', '-m', 'src.main',
        '--command', 'create',
        '--url', args.url,
        '--commission-rate', str(args.commission_rate),
        '--product-price', str(args.product_price),
        '--country', args.country or 'US',
    ]
    
    if args.customer_id:
        cmd.extend(['--customer-id', args.customer_id])
    
    if args.affiliate_name:
        cmd.extend(['--affiliate-name', args.affiliate_name])
    
    if args.name:
        cmd.extend(['--name', args.name])
    
    if args.product_description:
        cmd.extend(['--product-description', args.product_description])
    
    # Always use AI research
    cmd.append('--use-ai-research')
    
    return cmd


def main():
    parser = argparse.ArgumentParser(
        description='Autoads Skill - Validate and Execute',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Amazon product
  python3 run_skill.py \\
    --url "https://www.amazon.com/dp/B0DYJKWLV8?maas=xxx&tag=xxx" \\
    --customer-id 3674729801 \\
    --affiliate-name yeahpromos \\
    --product-price 29.99 \\
    --commission-rate 0.0375 \\
    --product-description "Amazon product B0DYJKWLV8, Mother's Day Gift theme"
  
  # Non-Amazon product with custom material
  python3 run_skill.py \\
    --url "https://example.com/product" \\
    --customer-id 3674729801 \\
    --affiliate-name myaffiliate \\
    --product-price 99.99 \\
    --commission-rate 0.10 \\
    --product-description "Smart home device with HD camera, remote monitoring, easy installation"
        '''
    )
    
    parser.add_argument('--url', required=True, help='Product URL (Amazon must include tracking params)')
    parser.add_argument('--customer-id', help='Google Ads Customer ID')
    parser.add_argument('--affiliate-name', help='Affiliate name')
    parser.add_argument('--product-price', type=float, required=True, help='Product price in USD')
    parser.add_argument('--commission-rate', type=float, required=True, help='Commission rate (0.05 = 5%%)')
    parser.add_argument('--country', default='US', help='Country code (default: US)')
    parser.add_argument('--name', help='Campaign name')
    parser.add_argument('--product-description', help='Product description for AI research')
    parser.add_argument('--use-ai-research', action='store_true', help='Use AI research (default: true)')
    
    args = parser.parse_args()
    
    # Validate
    is_valid, error = validate_params(args)
    if not is_valid:
        print(f"❌ Validation Error: {error}")
        sys.exit(1)
    
    # Build command
    cmd = build_command(args)
    
    print(f"🚀 Executing autoads...")
    print(f"   URL: {args.url}")
    print(f"   Price: ${args.product_price}, Commission: {args.commission_rate*100:.2f}%")
    if args.affiliate_name:
        print(f"   Affiliate: {args.affiliate_name}")
    if args.customer_id:
        print(f"   Customer ID: {args.customer_id}")
    print()
    
    # Execute
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()