#!/usr/bin/env python3
"""
YeahPromos 邮件暂停监控
=======================

功能:
1. 读取Gmail邮箱中的YeahPromos终止通知邮件
2. 解析ASIN或MID
3. 通过MID→ASIN映射找到关联的ASIN
4. 自动暂停对应的Google Ads广告系列

邮件格式:
格式1 (有ASIN):
    ASIN:B0C7JCXX7K , Tub Works (MID:380763)

格式2 (只有MID):
    Tub Works (MID:380763)
"""

import sys
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 配置文件
MID_ASIN_DB = Path(__file__).parent / "logs" / "mid_asin_mapping.json"
PAUSED_EMAILS_LOG = Path(__file__).parent / "logs" / "paused_by_email.json"


def load_mid_asin_mapping():
    """Load MID→ASIN mapping from file."""
    if MID_ASIN_DB.exists():
        with open(MID_ASIN_DB) as f:
            return json.load(f)
    return {}


def save_mid_asin_mapping(mapping):
    """Save MID→ASIN mapping to file."""
    MID_ASIN_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(MID_ASIN_DB, 'w') as f:
        json.dump(mapping, f, indent=2)


def update_mid_asin_from_orders(orders):
    """
    Update MID→ASIN mapping from recent orders.
    Call this after fetching new orders.
    """
    mapping = load_mid_asin_mapping()
    
    for order in orders:
        if not order.advert_id or not order.asin:
            continue
        
        mid = str(order.advert_id)
        asin = order.asin
        
        if mid not in mapping:
            mapping[mid] = {'asins': [], 'last_seen': None, 'name': ''}
        
        # Add ASIN if not already in list
        if asin not in mapping[mid]['asins']:
            mapping[mid]['asins'].append(asin)
        
        # Update last seen
        last_seen = mapping[mid].get('last_seen')
        if last_seen is None or order.transaction_date.isoformat() > last_seen:
            mapping[mid]['last_seen'] = order.transaction_date.isoformat()
    
    save_mid_asin_mapping(mapping)
    return mapping


def parse_asins_from_email(body):
    """
    从邮件正文中提取ASIN。
    返回格式1（有ASIN）和格式2（只有MID）的ASIN列表。
    """
    asins_direct = []  # 格式1：直接从邮件中提取的ASIN
    mids_only = []     # 格式2：只有MID，需要通过映射查找
    
    # 格式1匹配: ASIN:B0C7JCXX7K 或 ASIN: B0C7JCXX7K
    pattern_asin = r'ASIN:?\s*([A-Z0-9]{10})'
    asins_found = re.findall(pattern_asin, body, re.IGNORECASE)
    asins_direct.extend(asins_found)
    
    # 格式2匹配: (MID:380763)
    pattern_mid = r'\(MID:\s*(\d+)\)'
    mids_found = re.findall(pattern_mid, body)
    
    # 去重
    asins_direct = list(set(asins_direct))
    mids_only = list(set(mids_found))
    
    return asins_direct, mids_only


def get_asins_from_mids(mids, mapping):
    """
    通过MID查找对应的ASIN列表。
    """
    asins_from_mid = []
    
    for mid in mids:
        mid_str = str(mid)
        if mid_str in mapping:
            asins_from_mid.extend(mapping[mid_str]['asins'])
    
    return list(set(asins_from_mid))


def read_gmail_emails(service, user_id='me', query='', max_results=10):
    """
    使用Gmail API读取邮件。
    需要先配置OAuth2认证。
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("需要安装: pip install google-api-python-client google-auth")
        return []
    
    # This is a placeholder - actual implementation needs OAuth2 setup
    # For now, we'll use IMAP instead (see below)
    return []


def read_imap_emails(imap_server, email, password, folder='INBOX', search_query='UNSEEN', max_results=50):
    """
    通过IMAP读取邮件。
    
    Args:
        imap_server: IMAP服务器地址 (e.g., 'imap.gmail.com')
        email: 邮箱地址
        password: 密码或App密码
        folder: 文件夹 (默认INBOX)
        search_query: 搜索条件 (默认UNSEEN未读邮件)
        max_results: 最大返回数量
    
    Returns:
        邮件列表 [(subject, body, date), ...]
    """
    import imaplib
    import email
    from email.header import decode_header
    
    emails = []
    
    try:
        # 连接IMAP服务器
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email, password)
        mail.select(folder)
        
        # 搜索邮件
        status, messages = mail.search(None, search_query)
        
        if status != 'OK':
            print(f"IMAP搜索失败: {status}")
            return emails
        
        message_ids = messages[0].split()
        print(f"找到 {len(message_ids)} 封邮件")
        
        # 只处理最新的max_results封
        for msg_id in message_ids[-max_results:]:
            try:
                status, data = mail.fetch(msg_id, '(RFC822)')
                
                if status != 'OK':
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # 解码主题
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or 'utf-8', errors='replace')
                
                # 获取日期
                date_str = msg['Date']
                
                # 获取正文
                body = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == 'text/plain':
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                body = payload.decode('utf-8', errors='replace')
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode('utf-8', errors='replace')
                
                emails.append({
                    'subject': subject,
                    'body': body,
                    'date': date_str,
                    'from': msg.get('From', '')
                })
                
            except Exception as e:
                print(f"解析邮件失败: {e}")
                continue
        
        mail.logout()
        
    except Exception as e:
        print(f"IMAP连接失败: {e}")
        print("提示: Gmail需要使用App密码而非登录密码")
    
    return emails


def check_emails_for_pauses(imap_server=None, email=None, password=None, 
                             search_query='UNSEEN', update_mapping=True,
                             dry_run=True):
    """
    主函数: 检查邮件并返回需要暂停的ASIN列表。
    
    Args:
        imap_server: IMAP服务器
        email: 邮箱地址
        password: 密码
        search_query: 'UNSEEN'只检查未读, 'ALL'检查所有
        update_mapping: 是否从订单更新MID→ASIN映射
        dry_run: True=只报告不暂停, False=实际暂停
    """
    from runner import load_google_ads_credentials
    from runner import pause_campaigns_for_asins
    
    results = {
        'format1_asins': [],   # 直接从邮件提取的ASIN
        'format2_asins': [],   # 从MID映射查到的ASIN
        'paused': [],
        'failed': [],
        'emails_processed': 0
    }
    
    # 1. 读取邮件
    if imap_server and email and password:
        print(f"正在连接 {imap_server}...")
        emails = read_imap_emails(imap_server, email, password, search_query=search_query)
    else:
        print("未配置邮箱，将使用模拟数据演示")
        emails = []
    
    results['emails_processed'] = len(emails)
    
    # 2. 解析每封邮件
    all_asins_from_email = []
    all_mids_from_email = []
    
    for msg in emails:
        # 检查是否来自YeahPromos
        if 'yeahpromos' not in msg.get('from', '').lower() and 'yeahpromos' not in msg.get('subject', '').lower():
            continue
        
        print(f"处理邮件: {msg.get('subject', '')[:50]}...")
        
        body = msg.get('body', '')
        asins_direct, mids_only = parse_asins_from_email(body)
        
        all_asins_from_email.extend(asins_direct)
        all_mids_from_email.extend(mids_only)
        
        if asins_direct:
            print(f"  格式1 - 直接ASIN: {asins_direct}")
        if mids_only:
            print(f"  格式2 - MID: {mids_only}")
    
    results['format1_asins'] = list(set(all_asins_from_email))
    
    # 3. 通过MID查找ASIN
    if all_mids_from_email:
        mapping = load_mid_asin_mapping()
        asins_from_mid = get_asins_from_mids(all_mids_from_email, mapping)
        results['format2_asins'] = asins_from_mid
        
        if asins_from_mid:
            print(f"MID映射找到ASIN: {asins_from_mid}")
        else:
            print(f"警告: MID {all_mids_from_email} 在映射中未找到")
            print(f"提示: 请先运行 update_mid_mapping 命令收集数据")
    
    # 4. 合并所有需要暂停的ASIN
    all_asins_to_pause = list(set(results['format1_asins'] + results['format2_asins']))
    
    if not all_asins_to_pause:
        print("\n没有发现需要暂停的ASIN")
        return results
    
    print(f"\n需要暂停的ASIN: {all_asins_to_pause}")
    
    # 5. 暂停广告
    if dry_run:
        print("\n[DRY RUN] 模拟暂停 (使用 --no-dry-run 执行实际暂停)")
        results['paused'] = all_asins_to_pause
    else:
        print("\n正在暂停广告...")
        gads_client, gads_config = load_google_ads_credentials()
        
        for asin in all_asins_to_pause:
            try:
                result = pause_campaigns_for_asins(
                    gads_client,
                    '6052559425',
                    [asin],
                    reason="YeahPromos邮件通知暂停",
                    note=f"来自邮件: {results.get('emails_processed', 0)}封邮件"
                )
                if result['paused'] > 0:
                    results['paused'].append(asin)
                    print(f"  ✅ 已暂停 {asin}")
                else:
                    results['failed'].append(asin)
                    print(f"  ⚠️ 未找到对应的广告系列: {asin}")
            except Exception as e:
                results['failed'].append(asin)
                print(f"  ❌ 暂停失败 {asin}: {e}")
    
    # 6. 记录已处理的邮件（避免重复处理）
    # TODO: 实现已处理邮件的记录
    
    return results


def update_mapping_from_orders(days=30):
    """从YeahPromos订单更新MID→ASIN映射。"""
    from runner import load_credentials
    from networks.yeahpromos.client import YeahPromosClient
    
    creds = load_credentials().get('yeahpromos', {})
    client = YeahPromosClient(creds['token'], creds['site_id'])
    
    print(f"正在获取最近{days}天的订单...")
    orders = client.fetch_orders(days=days)
    
    print(f"获取到 {len(orders)} 个订单")
    
    mapping = update_mid_asin_from_orders(orders)
    
    print(f"\nMID→ASIN映射已更新:")
    print(f"总共 {len(mapping)} 个MID")
    
    for mid, data in list(mapping.items())[:5]:
        print(f"  MID {mid}: {len(data['asins'])} 个ASIN - {data['asins'][:3]}...")
    
    return mapping


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YeahPromos邮件暂停监控')
    parser.add_argument('--update-mapping', action='store_true', 
                        help='从订单更新MID→ASIN映射')
    parser.add_argument('--check-emails', action='store_true',
                        help='检查邮件并暂停')
    parser.add_argument('--imap-server', default='imap.gmail.com',
                        help='IMAP服务器地址')
    parser.add_argument('--email',
                        help='邮箱地址')
    parser.add_argument('--password',
                        help='邮箱密码或App密码')
    parser.add_argument('--search', default='UNSEEN',
                        help='邮件搜索条件: UNSEEN/ALL')
    parser.add_argument('--no-dry-run', action='store_true',
                        help='实际执行暂停(默认只报告)')
    
    args = parser.parse_args()
    
    if args.update_mapping:
        update_mapping_from_orders()
    
    if args.check_emails:
        results = check_emails_for_pauses(
            imap_server=args.imap_server,
            email=args.email,
            password=args.password,
            search_query=args.search,
            dry_run=not args.no_dry_run
        )
        
        print("\n=== 结果汇总 ===")
        print(f"处理邮件数: {results['emails_processed']}")
        print(f"格式1 ASIN: {results['format1_asins']}")
        print(f"格式2 ASIN (通过MID): {results['format2_asins']}")
        print(f"已暂停: {results['paused']}")
        print(f"失败: {results['failed']}")
