#!/usr/bin/env python3
"""
Archer ROI 计算器
================
计算 Google Ads 广告系列在 Archer 联盟平台上的收益率

用法:
    # 设置凭证（只需设置一次）
    export ARCHER_USERNAME=你的用户名
    export ARCHER_PASSWORD=你的密码
    
    # 查看帮助
    python3 main.py --help
    
    # 生成报告（最近30天）
    python3 main.py --report
    
    # 指定日期范围
    python3 main.py --report --start 20260301 --end 20260331
    
    # 输出 JSON 格式
    python3 main.py --report --format json --output /root/.openclaw/workspace/logs/archer_roi_report.json
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.archer_client import ArcherClient, ArcherAuthError, ArcherAPIError
from src.google_ads_data import GoogleAdsDataFetcher
from src.roi_calculator import ROICalculator

# ─────────────────────────────────────────────
# 日志配置
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("archer_roi")


# ─────────────────────────────────────────────
# 凭证管理（安全：不存储在任何文件）
# ─────────────────────────────────────────────
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials", "archer.env")

def load_credentials():
    """从环境变量或 credentials 文件加载凭证（不存储密码）"""
    username = os.environ.get("ARCHER_USERNAME")
    password = os.environ.get("ARCHER_PASSWORD")
    
    if username and password:
        logger.info("从环境变量加载 Archer 凭证")
        return username, password
    
    # 尝试从 credentials 文件加载（仅存储用户名）
    cred_dir = os.path.dirname(CREDENTIALS_FILE)
    os.makedirs(cred_dir, exist_ok=True)
    
    username_file = CREDENTIALS_FILE.replace(".env", "_username.txt")
    if os.path.exists(username_file):
        with open(username_file, "r") as f:
            username = f.read().strip()
        logger.info(f"Archer 用户名已配置: {username}")
    else:
        username = None
    
    # password 不存储，只提示
    return username, None


def save_username(username: str):
    """安全保存用户名（不保存密码）"""
    cred_dir = os.path.dirname(CREDENTIALS_FILE)
    os.makedirs(cred_dir, exist_ok=True)
    username_file = CREDENTIALS_FILE.replace(".env", "_username.txt")
    with open(username_file, "w") as f:
        f.write(username)
    logger.info(f"Archer 用户名已保存到 {username_file}")


def interactive_configure():
    """交互式配置凭证"""
    print("\n" + "=" * 50)
    print("  Archer API 凭证配置")
    print("=" * 50)
    print("\n安全说明：")
    print("  - 密码仅临时用于获取 Access Token")
    print("  - 密码不会存储在任何文件中")
    print("  - Access Token 有效期约1小时")
    print()
    
    username = input("Archer 用户名/邮箱: ").strip()
    if not username:
        print("用户名不能为空")
        sys.exit(1)
    
    import getpass
    password = getpass.getpass("Archer 密码: ")
    if not password:
        print("密码不能为空")
        sys.exit(1)
    
    # 验证凭证
    print("\n正在验证凭证...")
    os.environ["ARCHER_USERNAME"] = username
    os.environ["ARCHER_PASSWORD"] = password
    
    client = ArcherClient()
    try:
        client.authenticate()
        save_username(username)
        print("\n✅ 凭证验证成功！")
        print(f"   Affiliate ID: {client.get_affiliate_id()}")
    except ArcherAuthError as e:
        print(f"\n❌ 认证失败: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# Google Ads 客户端初始化
# ─────────────────────────────────────────────
def init_google_ads_client():
    """初始化 Google Ads 客户端"""
    # 复用 autoads 项目中的 Google Ads 配置
    autoads_config = "/root/.openclaw/workspace/autoads/awesome-ridge-478918-t7-bc818468b332.json"
    
    if not os.path.exists(autoads_config):
        raise FileNotFoundError(f"Google Ads 配置不存在: {autoads_config}")
    
    # 动态导入以避免不必要的依赖
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "google_ads_client", 
        "/root/.openclaw/workspace/autoads/src/google_ads_client.py"
    )
    google_ads_module = importlib.util.module_from_spec(spec)
    
    # 需要先设置路径
    sys.path.insert(0, "/root/.openclaw/workspace/autoads/src")
    spec.loader.exec_module(google_ads_module)
    
    GoogleAdsClient = google_ads_module.GoogleAdsClient
    config_path = autoads_config
    
    return GoogleAdsClient(config_path=config_path)


# ─────────────────────────────────────────────
# 主命令
# ─────────────────────────────────────────────
def cmd_report(args):
    """生成 ROI 报告"""
    
    # 加载凭证
    username, password = load_credentials()
    
    if not username or not password:
        print("\n❌ 缺少 Archer 凭证")
        print(f"   请先配置：python3 {__file__} --configure")
        print("   或设置环境变量：")
        print("     export ARCHER_USERNAME=你的用户名")
        print("     export ARCHER_PASSWORD=你的密码")
        sys.exit(1)
    
    os.environ["ARCHER_USERNAME"] = username
    os.environ["ARCHER_PASSWORD"] = password
    
    # 初始化客户端
    logger.info("初始化 Archer 客户端...")
    archer = ArcherClient()
    
    try:
        archer.authenticate()
        aff_id = archer.get_affiliate_id()
        logger.info(f"Archer Affiliate ID: {aff_id}")
    except ArcherAuthError as e:
        logger.error(f"认证失败: {e}")
        sys.exit(1)
    
    # 初始化 Google Ads
    logger.info("初始化 Google Ads 客户端...")
    try:
        gads_client = init_google_ads_client()
    except Exception as e:
        logger.error(f"Google Ads 客户端初始化失败: {e}")
        sys.exit(1)
    
    gads_fetcher = GoogleAdsDataFetcher(gads_client)
    calculator = ROICalculator(archer, gads_fetcher)
    
    # 生成报告
    report = calculator.calculate(
        start_date=args.start,
        end_date=args.end,
        min_archer_clicks=args.min_clicks,
        output_format=args.format
    )
    
    # 保存 JSON 输出
    if args.output:
        output_data = report.to_dict()
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"报告已保存到: {args.output}")
    
    return report


def cmd_test_connection(args):
    """测试 API 连接"""
    username, password = load_credentials()
    
    if not username or not password:
        print("❌ 缺少凭证，请先运行 --configure")
        sys.exit(1)
    
    os.environ["ARCHER_USERNAME"] = username
    os.environ["ARCHER_PASSWORD"] = password
    
    archer = ArcherClient()
    
    print("\n测试 Archer API 连接...")
    try:
        archer.authenticate()
        print("  ✅ OAuth2 认证成功")
        
        aff_id = archer.get_affiliate_id()
        print(f"  ✅ Affiliate ID: {aff_id}")
        
        # 测试获取链接数据
        today = datetime.now()
        start = (today - timedelta(days=7)).strftime("%Y%m%d")
        end = today.strftime("%Y%m%d")
        
        data = archer.get_link_data(
            start_date=start,
            end_date=end,
            sort_order=False,
            min_clicks=0,
            limit=5
        )
        print(f"  ✅ link_data API 正常，返回 {len(data.get('links', [])) if isinstance(data, dict) else '?'} 条记录")
        
        # 打印样例数据
        if isinstance(data, dict) and data.get("links"):
            print("\n  样例数据字段:")
            sample = data["links"][0]
            for key in list(sample.keys())[:10]:
                print(f"    - {key}")
        
        print("\n✅ 所有连接测试通过!")
        
    except ArcherAuthError as e:
        print(f"  ❌ 认证失败: {e}")
        sys.exit(1)
    except ArcherAPIError as e:
        print(f"  ❌ API 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ❌ 未知错误: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Archer × Google Ads ROI 计算器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 首次配置
  python3 main.py configure
  
  # 测试连接
  python3 main.py test
  
  # 生成报告（最近30天）
  python3 main.py report
  
  # 指定日期范围
  python3 main.py report --start 20260301 --end 20260331
  
  # 输出 JSON
  python3 main.py report --format json --output /root/.openclaw/workspace/logs/archer_roi.json
        """
    )
    
    # 支持 python3 main.py --report 格式（无需输入 report positional）
    parser.add_argument("--report", dest="use_report", action="store_true", 
                       help="生成 ROI 报告（可与 --start/--end/--format/--output 组合）")
    parser.add_argument("--start", dest="start", default=None, help="开始日期 YYYYMMDD")
    parser.add_argument("--end", dest="end", default=None, help="结束日期 YYYYMMDD")
    parser.add_argument("--min-clicks", type=int, default=0)
    parser.add_argument("--format", choices=["print", "json", "both"], default="print")
    parser.add_argument("--output", type=str, default=None)
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # configure 命令
    subparsers.add_parser("configure", help="交互式配置 Archer 凭证")
    
    # test 命令
    subparsers.add_parser("test", help="测试 API 连接")
    
    # report 命令
    report_parser = subparsers.add_parser("report", help="生成 ROI 报告")
    report_parser.add_argument("--start", default=None, help="开始日期 YYYYMMDD（默认：30天前）")
    report_parser.add_argument("--end", default=None, help="结束日期 YYYYMMDD（默认：昨天）")
    report_parser.add_argument("--min-clicks", type=int, default=0, help="Archer 数据最少点击数")
    report_parser.add_argument("--format", choices=["print", "json", "both"], default="print", help="输出格式")
    report_parser.add_argument("--output", type=str, default=None, help="JSON 输出文件路径")
    
    # 默认命令是 report（运行 main.py 不带参数时）
    args = parser.parse_args()
    
    # 如果用了 --report flag，转为 report 命令
    if args.use_report and not args.command:
        args.command = "report"
        # 设置默认日期
        today = datetime.now()
        if not args.start:
            args.start = (today - timedelta(days=30)).strftime("%Y%m%d")
        if not args.end:
            args.end = (today - timedelta(days=1)).strftime("%Y%m%d")
        args.format = "print"
        args.output = None
        args.min_clicks = 0
        del args.use_report  # 清理临时 flag
    
    # 如果既没有 command 也没有 --report，默认 report
    if not args.command and not getattr(args, 'use_report', False):
        args.command = "report"
        today = datetime.now()
        if not args.start:
            args.start = (today - timedelta(days=30)).strftime("%Y%m%d")
        if not args.end:
            args.end = (today - timedelta(days=1)).strftime("%Y%m%d")
        args.format = "print"
        args.output = None
        args.min_clicks = 0
    
    return args


def main():
    args = parse_args()
    
    if args.command == "configure":
        interactive_configure()
    elif args.command == "test":
        cmd_test_connection(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        logger.error(f"未知命令: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
