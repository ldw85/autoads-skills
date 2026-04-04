#!/bin/bash
# Archer 产品监控定时任务包装脚本
# 每2小时运行一次，检测被删产品并暂停对应广告系列

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 加载环境变量（Archer 凭证）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 执行监控
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始产品监控..."
python3 monitor_main.py --run

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 监控完成"
