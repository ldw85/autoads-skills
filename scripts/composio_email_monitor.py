#!/usr/bin/env python3
"""
Composio Outlook 邮件监控 - YeahPromos 暂停处理
==========================================

功能:
1. 使用 Composio 读取 Outlook 邮件
2. 过滤 yeahpromos.com 发来的邮件
3. 提取 ASIN/MID 并暂停对应的广告

用法:
    python3 composio_email_monitor.py --check          # 检查并报告
    python3 composio_email_monitor.py --pause   # 检查并自动暂停
"""

import sys
import os
import re
import json
import argparse
import httpx
import subprocess
from pathlib import Path
from datetime import datetime

# Composio 配置
API_KEY = 'ak_e198_UxBGEs3ILVwWji7'
MCP_SERVER_URL = 'https://backend.composio.dev/v3/mcp/42fe4c7e-d7f3-418d-9183-9c58821e8988/mcp'
CONNECTED_ACCOUNT_ID = 'ca_k0c6yTjlB6sg'
USER_ID = 'pb_asin_stt_mon@outlook.com'

# 日志目录
LOG_DIR = Path('/root/.openclaw/workspace/autoads/archer-roi/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 数据库路径
PAUSED_LOG = LOG_DIR / 'paused_campaigns.json'
PROCESSED_EMAILS_LOG = LOG_DIR / 'processed_emails.json'

# 加载运行时模块
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'autoads' / 'archer-roi'))
sys.path.insert(0, str(Path(__file__).parent / 'autoads'))


def load_processed_emails():
    if PROCESSED_EMAILS_LOG.exists():
        with open(PROCESSED_EMAILS_LOG) as f:
            return json.load(f)
    return []


def save_processed_emails(email_ids):
    with open(PROCESSED_EMAILS_LOG, 'w') as f:
        json.dump(email_ids, f, indent=2)


def parse_asins_from_email(body):
    asins = []
    mids = []
    pattern_asin = r'ASIN:?\s*([A-Z0-9]{10})'
    asins = re.findall(pattern_asin, body, re.IGNORECASE)
    pattern_mid = r'\(MID:\s*(\d+)\)'
    mids = re.findall(pattern_mid, body)
    return list(set(asins)), list(set(mids))


def load_mid_asin_mapping():
    mid_asin_file = LOG_DIR / 'mid_asin_mapping.json'
    if mid_asin_file.exists():
        with open(mid_asin_file) as f:
            return json.load(f)
    return {}


def get_asins_from_mids(mids, mapping):
    asins = []
    for mid in mids:
        if str(mid) in mapping:
            asins.extend(mapping[str(mid)]['asins'])
    return list(set(asins))


def call_mcp_tool(tool_name, arguments):
    mcp_url = f'{MCP_SERVER_URL}?user_id={USER_ID}&connected_account_id={CONNECTED_ACCOUNT_ID}'
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream'
    }
    
    def send_request(method, params=None, req_id=1):
        payload = {'jsonrpc': '2.0', 'method': method, 'params': params or {}, 'id': req_id}
        response = httpx.post(mcp_url, json=payload, headers=headers, timeout=60, follow_redirects=True)
        return response
    
    send_request('initialize', {
        'protocolVersion': '2024-11-05',
        'capabilities': {},
        'clientInfo': {'name': 'email-monitor', 'version': '1.0'}
    })
    
    response = send_request('tools/call', {'name': tool_name, 'arguments': arguments})
    content = response.text
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('data:'):
            data = line[5:].strip()
            try:
                result = json.loads(data)
                if 'result' in result:
                    return result['result']
            except:
                pass
    return None


def list_emails(limit=20):
    result = call_mcp_tool('OUTLOOK_LIST_MESSAGES', {'limit': limit, 'response_detail': 'full'})
    if result and 'content' in result:
        content = result['content']
        if isinstance(content, list) and len(content) > 0:
            text_content = content[0].get('text', '')
            if text_content:
                data = json.loads(text_content)
                return data.get('data', {}).get('value', [])
    return []



def send_feishu_notification(message):
    """Send Feishu notification via OpenClaw CLI"""
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
        print(f"   ⚠️ 飞书通知发送失败: {e}")
        return False

def check_emails_and_pause(dry_run=True):
    print("📧 读取 Outlook 邮件...")
    emails = list_emails(limit=20)
    print(f"   获取到 {len(emails)} 封邮件")
    
    # 过滤 yeahpromos 邮件
    yeahpromos_emails = []
    for email in emails:
        subject = email.get('subject', '')
        from_addr = email.get('from', {}).get('emailAddress', {}).get('address', '')
        if 'yeahpromos.com' in from_addr.lower() or 'yeahpromos' in subject.lower():
            yeahpromos_emails.append(email)
    
    print(f"   发现 {len(yeahpromos_emails)} 封 yeahpromos 邮件")
    
    if not yeahpromos_emails:
        print("✅ 没有需要处理的 yeahpromos 邮件")
        return
    
    # 加载已处理的邮件
    processed_ids = load_processed_emails()
    
    # 处理每封邮件
    asins_to_pause = []
    mids_to_lookup = []
    
    for email in yeahpromos_emails:
        msg_id = email.get('id', '')
        subject = email.get('subject', '')
        
        if msg_id in processed_ids:
            print(f"   ⏭️ 跳过已处理: {subject[:50]}")
            continue
        
        print(f"   📧 处理: {subject[:50]}")
        
        body = email.get('bodyPreview', '') or email.get('body', {}).get('content', '')
        asins, mids = parse_asins_from_email(body)
        
        print(f"      ASIN: {asins}, MID: {mids}")
        
        asins_to_pause.extend(asins)
        mids_to_lookup.extend(mids)
        processed_ids.append(msg_id)
    
    # 通过 MID 查找 ASIN
    if mids_to_lookup:
        mapping = load_mid_asin_mapping()
        asins_from_mid = get_asins_from_mids(mids_to_lookup, mapping)
        asins_to_pause.extend(asins_from_mid)
        print(f"   MID→ASIN 映射找到: {asins_from_mid}")
    
    asins_to_pause = list(set(asins_to_pause))
    
    if not asins_to_pause:
        print("✅ 没有需要暂停的 ASIN")
        save_processed_emails(processed_ids)
        return
    
    print(f"\n🛑 需要暂停的 ASIN: {asins_to_pause}")
    
    if dry_run:
        print("\n[DRY RUN] 模拟暂停 (使用 --pause 执行实际暂停)")
    else:
        print("\n⏸️ 暂停广告...")
        try:
            from runner import pause_campaigns_for_asins
            for asin in asins_to_pause:
                try:
                    result = pause_campaigns_for_asins(
                        None, '6052559425', [asin],
                        reason="YeahPromos邮件通知暂停",
                        note="来自Composio邮件监控"
                    )
                    print(f"   ✅ 已暂停 {asin}")
                except Exception as e:
                    print(f"   ❌ 暂停失败 {asin}: {e}")
        except Exception as e:
            print(f"   ❌ 导入失败: {e}")
    
    save_processed_emails(processed_ids)
    
    # 发送飞书通知
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    notification = f"📧 **Composio邮件监控** - {timestamp}\n\n"
    notification += f"🛑 已暂停 {len(asins_to_pause)} 个ASIN: {asins_to_pause}"
    send_feishu_notification(notification)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Composio Outlook 邮件监控')
    parser.add_argument('--check', action='store_true', help='检查并报告')
    parser.add_argument('--pause', action='store_true', help='检查并自动暂停')
    args = parser.parse_args()
    
    if args.check or args.pause:
        check_emails_and_pause(dry_run=not args.pause)
    else:
        print(__doc__)
