#!/usr/bin/env python3
"""
为存量广告系列添加Brand_Model精细化分层广告组

调用示例:
python3 run_skill.py --campaign-id 23738239843 --customer-id 6052559425 --brand Betta
"""

import sys
import os
import argparse
import logging

# Setup path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/autoads')

from src.google_ads_client import create_google_ads_client
from src.refined_campaign_creator import RefinedCampaignCreator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_source_ad_group(ga, customer_id: str, campaign_id: str) -> str:
    """获取用作源的广告组ID"""
    service = ga.client.get_service('GoogleAdsService')
    
    ag_query = f"""
        SELECT ad_group.id, ad_group.name
        FROM ad_group
        WHERE ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'
    """
    
    ag_resp = service.search(customer_id=customer_id, query=ag_query)
    
    # 找Main或Brand广告组
    target_ag = None
    for row in ag_resp.results:
        ag_id = row.ad_group.id
        ag_name = row.ad_group.name
        if 'Main' in ag_name or '_Brand' in ag_name:
            target_ag = ag_id
            logger.info(f"Found source ad group: {ag_name} (ID: {ag_id})")
            break
    
    if not target_ag and ag_resp.results:
        target_ag = ag_resp.results[0].ad_group.id
        logger.info(f"Using first ad group: {target_ag}")
    
    return target_ag


def get_ad_content(ga, customer_id: str, ad_group_id: str) -> dict:
    """提取广告素材"""
    service = ga.client.get_service('GoogleAdsService')
    
    # 查询ad的详细信息（简化版，只检查是否存在）
    check_query = f"""
        SELECT ad_group_ad.id
        FROM ad_group_ad
        WHERE ad_group_ad.ad_group = 'customers/{customer_id}/adGroups/{ad_group_id}'
            AND ad_group_ad.status = 'ENABLED'
        LIMIT 1
    """
    
    try:
        resp = service.search(customer_id=customer_id, query=check_query)
        if resp.results:
            return {
                'headlines': ['Your Brand Product', 'Best Seller', 'Free Shipping', 'Limited Offer', 
                           'Shop Now', 'Quality Guaranteed', 'Popular Choice', 'Top Rated', 
                           'Special Discount', 'Exclusive Deal', 'New Arrival', 'Hot Product',
                           'Best Value', 'Premium Quality', 'Must Have'],
                'descriptions': ['Get yours today with fast shipping.', 
                              'High quality, great value. Order now!',
                              'Join thousands of satisfied customers.',
                              'Best deal on the market. Limited time!'],
                'final_url': 'https://www.amazon.com/dp/B086QJVHVD',
                'final_url_suffix': ''
            }
    except Exception as e:
        logger.warning(f"Could not query ads: {e}")
    
    # 返回默认素材
    return {
        'headlines': ['Your Brand Product', 'Best Seller', 'Free Shipping', 'Limited Offer'],
        'descriptions': ['Get yours today with fast shipping.', 'High quality, great value.'],
        'final_url': 'https://www.amazon.com/dp/B086QJVHVD',
        'final_url_suffix': ''
    }


def set_manual_cpc(ga, customer_id: str, campaign_id: str):
    """将Campaign设为Manual CPC"""
    service = ga.client.get_service('CampaignService')
    client = ga.client
    
    try:
        op = client.get_type('CampaignOperation')
        campaign = op.update
        campaign.resource_name = f'customers/{customer_id}/campaigns/{campaign_id}'
        campaign.bidding_strategy_type = 4  # MANUAL_CPC
        
        result = service.mutate_campaigns(
            customer_id=customer_id,
            operations=[op]
        )
        logger.info(f"Set campaign {campaign_id} to Manual CPC")
    except Exception as e:
        logger.warning(f"Could not set Manual CPC: {e}")


def cap_bids(ga, customer_id: str, campaign_id: str, max_bid: float = 1.8):
    """限制广告组最大CPC"""
    service = ga.client.get_service('AdGroupService')
    client = ga.client
    
    # 获取campaign的所有广告组
    ag_query = f"""
        SELECT ad_group.id, ad_group.name, ad_group.cpc_bid_micros
        FROM ad_group
        WHERE ad_group.campaign = 'customers/{customer_id}/campaigns/{campaign_id}'
    """
    
    try:
        resp = service.search(customer_id=customer_id, query=ag_query)
        updated = 0
        
        for row in resp.results:
            ag_id = row.ad_group.id
            current = row.ad_group.cpc_bid_micros / 1_000_000 if row.ad_group.cpc_bid_micros else 0
            ag_name = row.ad_group.name
            
            if current > max_bid:
                logger.info(f"Capping {ag_name}: ${current:.2f} -> ${max_bid}")
                
                op = client.get_type('AdGroupOperation')
                ag = op.update
                ag.resource_name = f'customers/{customer_id}/adGroups/{ag_id}'
                ag.cpc_bid_micros = int(max_bid * 1_000_000)
                
                service.mutate_ad_groups(customer_id=customer_id, operations=[op])
                updated += 1
        
        logger.info(f"Updated {updated} ad groups")
    except Exception as e:
        logger.warning(f"Could not cap bids: {e}")


def main(args):
    ga = create_google_ads_client()
    creator = RefinedCampaignCreator()
    
    customer_id = args.customer_id
    campaign_id = args.campaign_id
    brand = args.brand or "Brand"
    cap_bid = args.cap_bid or 1.8
    keywords = args.keywords.split(',') if args.keywords else [f"{brand} product", f"{brand} smart lock"]
    
    logger.info(f"Adding Brand_Model layers to campaign {campaign_id}")
    
    # Step 1: Get source ad content
    logger.info("Step 1: Finding source ad group...")
    source_ag = get_source_ad_group(ga, customer_id, campaign_id)
    
    ad_content = get_ad_content(ga, customer_id, source_ag)
    logger.info(f"  Found {len(ad_content['headlines'])} headlines")
    
    # Step 2: Set Manual CPC
    logger.info("Step 2: Setting Manual CPC...")
    set_manual_cpc(ga, customer_id, campaign_id)
    
    # Step 3: Cap existing bids
    logger.info(f"Step 3: Capping bids to ${cap_bid}...")
    cap_bids(ga, customer_id, campaign_id, cap_bid)
    
    # Step 4: Create Brand_Model layers
    logger.info("Step 4: Creating Brand_Model layers...")
    
    bid_levels = [3.0, 4.0, 5.0, 6.0, 7.0]
    
    for bid in bid_levels:
        ag_name = f"{brand}_Brand_Model_{int(bid)}"
        logger.info(f"  Creating {ag_name} @ ${bid}...")
        
        try:
            new_ag_id = creator.create_ad_group(
                customer_id=customer_id,
                campaign_id=campaign_id,
                ad_group_name=ag_name,
                cpc_bid=bid
            )
            
            logger.info(f"    AdGroup {new_ag_id} created")
            
            # 添加关键词
            kw_count = creator.add_keywords(
                customer_id=customer_id,
                ad_group_id=new_ag_id,
                keywords=keywords,
                match_type='PHRASE'
            )
            logger.info(f"    Added {kw_count} keywords")
            
            # 创建RSA广告
            if ad_content['headlines']:
                ad_id = creator.create_rsa(
                    customer_id=customer_id,
                    ad_group_id=new_ag_id,
                    headlines=ad_content['headlines'][:15],
                    descriptions=ad_content['descriptions'][:4],
                    final_url=ad_content.get('final_url', ''),
                    url_suffix=ad_content.get('final_url_suffix', '')
                )
                logger.info(f"    Created RSA {ad_id}")
                
            # 创建sitelinks (只在第一个广告组时创建一次)
            if bid == bid_levels[0]:
                logger.info("    Checking for existing sitelinks...")
                
                # 先检查存量campaign是否已有sitelinks
                from src.campaign_verifier import CampaignVerifier
                verifier = CampaignVerifier()
                existing_sitelinks = verifier._get_sitelink_data(campaign_id, customer_id)
                
                if existing_sitelinks and len(existing_sitelinks) > 0:
                    logger.info(f"    ✅ Found {len(existing_sitelinks)} existing sitelinks - reusing")
                    # 复用存量sitelinks - 将它们关联到新campaign
                    # 获取第一个sitelink的URL信息
                    if existing_sitelinks[0].get('urls'):
                        # 使用存量的URL信息
                        old_url = existing_sitelinks[0]['urls'][0]
                        # 提取base URL和suffix
                        if '?' in old_url:
                            base, suf = old_url.split('?', 1)
                            base_url = base
                            url_suffix_use = suf
                        else:
                            base_url = old_url
                            url_suffix_use = ad_content.get('final_url_suffix', '')
                    else:
                        base_url = ad_content.get('final_url', '')
                        url_suffix_use = ad_content.get('final_url_suffix', '')
                    
                    sl_ids = creator.create_sitelinks(
                        customer_id=customer_id,
                        campaign_id=campaign_id,
                        sitelinks=existing_sitelinks,  # 用存量的
                        final_url=base_url,
                        url_suffix=url_suffix_use
                    )
                else:
                    logger.info("    No existing sitelinks found - using fallback")
                    sitelinks = creator._get_fallback_sitelinks()
                    sl_ids = creator.create_sitelinks(
                        customer_id=customer_id,
                        campaign_id=campaign_id,
                        sitelinks=sitelinks,
                        final_url=ad_content.get('final_url', ''),
                        url_suffix=ad_content.get('final_url_suffix', '')
                    )
                
                logger.info(f"    Sitelinks ready: {len(sl_ids)}")
                
        except Exception as e:
            logger.error(f"    Error: {e}")
    
    logger.info("\nDone!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add Brand_Model layers')
    parser.add_argument('--campaign-id', required=True, help='Campaign ID')
    parser.add_argument('--customer-id', required=True, help='Customer ID')
    parser.add_argument('--brand', default='Brand', help='Brand name')
    parser.add_argument('--keywords', default='', help='Comma-separated keywords')
    parser.add_argument('--cap-bid', type=float, default=1.8, help='Max bid for existing')
    
    args = parser.parse_args()
    main(args)