#!/bin/bash
# Archer Product Selector - Shell Wrapper
# 用法: bash run_skill.sh [--skip-feishu]

SKILL_DIR="$(dirname "$0")"
SKIP_FEISHU=false

# Parse args
for arg in "$@"; do
    case $arg in
        --skip-feishu)
            SKIP_FEISHU=true
            ;;
    esac
done

echo "Running Archer Product Selector..."

cd "$SKILL_DIR"

# Run Python script
python3 main.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Archer选品完成！"
    echo "CSV: /root/.openclaw/workspace/logs/archer_selected_products.csv"
    echo "飞书文档: https://feishu.cn/docx/Ly7XdBWptoNWxVxMha3cwhLbn7f"
else
    echo "❌ 选品失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE