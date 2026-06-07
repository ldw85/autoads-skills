#!/usr/bin/env python3
"""
Archer Product Status Monitor
==========================
Check Amazon product status via Archer affiliate API.
Pause ads for products that are unavailable.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

# Add archer-roi to path
sys.path.insert(0, '/root/.openclaw/workspace/autoads/archer-roi')

from networks.archer import ArcherClient
import sys
sys.path.insert(0, '/root/.openclaw/workspace/autoads/archer-roi')
from runner import cred_agent_get

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LOG_DIR = Path('/root/.openclaw/workspace/autoads/archer-roi/logs')
PROCESSED_FILE = LOG_DIR / 'processed_archer_products.json'


def load_processed_asins() -> set:
    """Load previously processed ASINs"""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            data = json.load(f)
            return set(data.get('processed_asins', []))
    return set()


def save_processed_asins(asins: set):
    """Save processed ASINs"""
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump({'processed_asins': list(asins)}, f)


def get_archer_campaigns() -> List[Dict]:
    """Get all Archer campaigns from ad_campaigns_db"""
    db_file = Path('/root/.openclaw/workspace/autoads/logs/ad_campaigns_db.json')
    if not db_file.exists():
        logger.warning(f"Campaign DB not found: {db_file}")
        return []
    
    with open(db_file) as f:
        data = json.load(f)
    
    # Filter for archer campaigns (account_id: 6660356395)
    archer_campaigns = [
        c for c in data.get('campaigns', [])
        if c.get('account_id') == '6660356395' and c.get('status') == 'ENABLED'
    ]
    return archer_campaigns


def check_product_status(client: ArcherClient, asin: str) -> Tuple[str, Dict]:
    """Check single product status via Archer API"""
    return client.check_product(asin)


def main():
    logger.info("=== Archer Product Status Monitor ===")
    
    # Load credentials
    username = cred_agent_get("ARCHER_USERNAME")
    password = cred_agent_get("ARCHER_PASSWORD")
    
    if not username or not password:
        logger.error("Missing Archer credentials")
        return
    
    # Initialize client
    client = ArcherClient(username, password)
    if not client.authenticate():
        logger.error("Failed to authenticate with Archer")
        return
    
    # Get all active Archer campaigns
    campaigns = get_archer_campaigns()
    logger.info(f"Found {len(campaigns)} active Archer campaigns")
    
    if not campaigns:
        logger.info("No campaigns to check")
        return
    
    # Get unique ASINs from campaigns
    asins_to_check = set(c.get('asin', '') for c in campaigns if c.get('asin'))
    asins_to_check.discard('')
    logger.info(f"Unique ASINs to check: {len(asins_to_check)}")
    
    # Load processed ASINs (last checked)
    processed = load_processed_asins()
    
    # Check each ASIN
    results = {
        'available': [],
        'unavailable': [],
        'unknown': [],
    }
    
    for asin in asins_to_check:
        if asin in processed:
            logger.info(f"Skipping {asin} (already checked recently)")
            continue
        
        status, details = check_product_status(client, asin)
        logger.info(f"ASIN {asin}: {status}")
        
        results[status].append({
            'asin': asin,
            'details': details
        })
        
        # Mark as processed
        processed.add(asin)
    
    # Save processed ASINs
    save_processed_asins(processed)
    
    # Generate report
    report_lines = ["📦 **Archer 商品状态监控报告**", f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    
    if results['available']:
        report_lines.append(f"✅ **有货 ({len(results['available'])})**:")
        for item in results['available']:
            report_lines.append(f"  - {item['asin']}")
    
    if results['unavailable']:
        report_lines.append(f"❌ **缺货/下架 ({len(results['unavailable'])})**:")
        for item in results['unavailable']:
            report_lines.append(f"  - {item['asin']}")
    
    if results['unknown']:
        report_lines.append(f"⚠️ **未知 ({len(results['unknown'])})**:")
        for item in results['unknown']:
            report_lines.append(f"  - {item['asin']}")
    
    report = "\n".join(report_lines)
    
    # Save report
    report_file = LOG_DIR / f'archer_product_status_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    report_file.write_text(report)
    
    print(report)
    print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    main()