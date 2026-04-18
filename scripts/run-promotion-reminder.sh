#!/bin/bash
# 亚马逊促销提醒 - 每周运行
cd /root/.openclaw/workspace

# 生成提醒
REMINDER=$(python3 -c "
import sys
sys.path.insert(0, '.')
from scripts.amazon_promotion_reminder import get_upcoming_reminders, format_reminder_message

reminders = get_upcoming_reminders(90)
print(format_reminder_message(reminders))
" 2>/dev/null)

if [ -n "$REMINDER" ]; then
    echo "$REMINDER"
    # 发送到飞书 (如果有敏感信息则跳过)
    if echo "$REMINDER" | grep -q "紧急"; then
        echo "Sending urgent reminder via message..."
    fi
fi
