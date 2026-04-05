#!/bin/bash
# 获取凭证的便捷脚本
# 用法: source get-cred.sh ARCHER_USERNAME ARCHER_PASSWORD

SOCKET_PATH="/tmp/openclaw-cred-agent.sock"
CRED_AGENT_DIR="$(dirname "$(readlink -f "$0")")"

get_credential() {
    local name="$1"
    echo "GET $name" | socat -T 2 UNIX-CONNECT:"$SOCKET_PATH" 2>/dev/null
}

# 检查守护进程是否运行
if [ ! -S "$SOCKET_PATH" ]; then
    echo "错误: Credential Agent 未运行" >&2
    echo "请先启动: python3 $CRED_AGENT_DIR/cred-agent.py --daemon" >&2
    return 1
fi

# 获取所有请求的凭证
for cred_name in "$@"; do
    value=$(get_credential "$cred_name")
    if [ -n "$value" ]; then
        export "$cred_name"="$value"
    else
        echo "警告: 凭证 $cred_name 不存在" >&2
    fi
done
