#!/bin/bash
# Archer ROI 报告定时任务包装脚本
# 每天运行一次，生成Google Ads广告系列ROI报告

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 加载环境变量（Archer 凭证）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 输出目录
OUTPUT_DIR="$PROJECT_DIR/logs"
mkdir -p "$OUTPUT_DIR"

# 执行ROI报告
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始生成ROI报告..."
python3 main.py --report --format json --output "$OUTPUT_DIR/roi_report_latest.json" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ROI报告生成完成"
