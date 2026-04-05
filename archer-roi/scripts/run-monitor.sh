#!/bin/bash
# Archer 产品监控定时任务包装脚本
# 使用 cred-agent 获取加密存储的凭证

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOCKET_PATH="/tmp/openclaw-cred-agent.sock"

cd "$PROJECT_DIR"

# 从 cred-agent 获取凭证
if [ ! -S "$SOCKET_PATH" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: Credential Agent 未运行"
    echo "请先启动: python3 $PROJECT_DIR/cred-agent.py --daemon"
    exit 1
fi

export ARCHER_USERNAME=$(echo "GET ARCHER_USERNAME" | socat -T 2 UNIX-CONNECT:"$SOCKET_PATH" 2>/dev/null || echo "")
export ARCHER_PASSWORD=$(echo "GET ARCHER_PASSWORD" | socat -T 2 UNIX-CONNECT:"$SOCKET_PATH" 2>/dev/null || echo "")

if [ -z "$ARCHER_USERNAME" ] || [ -z "$ARCHER_PASSWORD" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: 无法从 cred-agent 获取凭证"
    exit 1
fi

# 执行监控
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始产品监控..."
python3 monitor_main.py --run

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 监控完成"
