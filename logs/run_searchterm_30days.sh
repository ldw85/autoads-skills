#!/bin/bash
# 搜索词深度语义分析 - 时间范围改为过去30天（1个月）
# ==============================================

cd /root/.openclaw/workspace/autoads

python3 - <<'PYEOF'
import sys
import os
import logging
from datetime import datetime, timedelta
from google.ads.googleads.client lib import GoogleAdsClientWrapper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# 使用3个账号
CUSTOMER_IDS = ['6052559425', '6660356395', '4772859239']

# 时间范围：过去30天（1个月）
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=30)
START_DATE_STR = START_DATE.strftime('%Y-%m-%d')
END_DATE_STR = END_DATE.strftime('%Y-%m-%d')

logger.info(f"搜索词深度分析 - 时间范围: {START_DATE_STR} 到 {END_DATE_STR} (30天)")
logger.info(f"分析账号: {CUSTOMER_IDS}")

def main():
    client = GoogleAdsClientWrapper()
    
    # 收集所有广告系列
    all_campaigns = []
    
    for cust_id in CUSTOMER_IDS:
        logger.info(f"\n=== 查询账号 {cust_id} ===")
        query = """
            SELECT campaign.id, campaign.name 
            FROM campaign 
            WHERE campaign.status = 'ENABLED'
            ORDER BY campaign.name
        """
        try:
            results = client.search(query, customer_id=cust_id)
            campaigns = [{'id': r.campaign.id, 'name': r.campaign.name, 'customer_id': cust_id} for r in results]
            all_campaigns.extend(campaigns)
            logger.info(f"  找到 {len(campaigns)} 个启用广告系列")
        except Exception as e:
            logger.error(f"  查询失败: {e}")
    
    logger.info(f"\n总共 {len(all_campaigns)} 个广告系列待分析")
    
    # TODO: 逐个获取搜索词并分析
    # 这里需要调用搜索词分析和AI语义分析
    # 需要写入飞书文档

if __name__ == "__main__":
    main()
PYEOF

echo "Exit code: $?"