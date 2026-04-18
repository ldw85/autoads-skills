#!/usr/bin/env python3
"""
Amazon Promotion Calendar Reminder
提前提醒重要促销节点，以便准备广告素材和库存
"""

import sys
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# 美国主要节日/事件 (月份, 日期或计算规则)
PROMOTION_EVENTS = [
    # 格式: (名称, 月, 日或计算规则, 提前提醒天数, 热销品类)
    
    # Q1
    ("超级碗", 2, "first_sunday", 21, "电视/派对用品/零食/运动器材"),
    ("超级碗", 2, "first_sunday", 7, "电视/派对用品/零食/运动器材"),
    ("情人节", 2, 14, 21, "珠宝/礼品/巧克力/浪漫礼品"),
    ("情人节", 2, 14, 7, "珠宝/礼品/巧克力/浪漫礼品"),
    ("总统日", 2, 19, 14, "电子产品/家电/床上用品"),
    
    # Q2
    ("复活节", 4, "easter", 28, "糖果/礼品/春季装饰/童装"),
    ("复活节", 4, "easter", 14, "糖果/礼品/春季装饰/童装"),
    ("母亲节", 5, "second_sunday", 28, "珠宝/美容/服装/家居用品"),
    ("母亲节", 5, "second_sunday", 14, "珠宝/美容/服装/家居用品"),
    ("阵亡将士纪念日", 5, "last_monday", 21, "户外家具/BBQ/泳池用品"),
    
    # Q3
    ("父亲节", 6, "third_sunday", 28, "工具/电子产品/运动/户外"),
    ("父亲节", 6, "third_sunday", 14, "工具/电子产品/运动/户外"),
    ("Prime Day", 7, "mid_july", 42, "电子产品/家居/Amazon设备/生活用品"),
    ("Prime Day", 7, "mid_july", 21, "电子产品/家居/Amazon设备/生活用品"),
    ("Prime Day", 7, "mid_july", 7, "电子产品/家居/Amazon设备/生活用品"),
    ("独立日", 7, 4, 21, "烟花/爱国用品/BBQ/户外"),
    
    # Q4
    ("劳动节", 9, "first_monday", 28, "家具/家电/办公用品"),
    ("返校季", 8, "august_start", 42, "学习用品/电子设备/服装/箱包"),
    ("返校季", 8, "august_start", 21, "学习用品/电子设备/服装/箱包"),
    ("万圣节", 10, 31, 56, "Cosplay/糖果/装饰/派对用品"),
    ("万圣节", 10, 31, 28, "Cosplay/糖果/装饰/派对用品"),
    ("万圣节", 10, 31, 14, "Cosplay/糖果/装饰/派对用品"),
    ("感恩节", 11, "fourth_thursday", 42, "厨房用品/家居/礼品"),
    ("黑色星期五", 11, "fourth_friday", 42, "电子产品/玩具/家电/所有品类"),
    ("黑色星期五", 11, "fourth_friday", 21, "电子产品/玩具/家电/所有品类"),
    ("黑色星期五", 11, "fourth_friday", 7, "电子产品/玩具/家电/所有品类"),
    ("网络星期一", 12, "first_monday_dec", 42, "电子产品/在线服务/服装"),
    ("网络星期一", 12, "first_monday_dec", 21, "电子产品/在线服务/服装"),
    ("圣诞节", 12, 25, 56, "玩具/礼品/装饰/食品"),
    ("圣诞节", 12, 25, 28, "玩具/礼品/装饰/食品"),
    ("圣诞节", 12, 25, 14, "玩具/礼品/装饰/食品"),
    ("新年", 1, 1, 28, "健身器材/减肥产品/派对用品"),
]

def get_date_for_event(year: int, month: int, day_rule: str) -> datetime:
    """计算具体节日日期"""
    if isinstance(day_rule, int):
        return datetime(year, month, day_rule)
    
    from datetime import timedelta
    
    if day_rule == "first_sunday":
        # 2月第一个星期日 (超级碗通常在2月第一个周日)
        d = datetime(year, month, 1)
        return d + timedelta(days=(6 - d.weekday()) % 7)
    
    elif day_rule == "second_sunday":
        # 5月第二个星期日 (母亲节)
        d = datetime(year, month, 1)
        first_sunday = d + timedelta(days=(6 - d.weekday()) % 7)
        return first_sunday + timedelta(days=7)
    
    elif day_rule == "third_sunday":
        # 6月第三个星期日 (父亲节)
        d = datetime(year, month, 1)
        first_sunday = d + timedelta(days=(6 - d.weekday()) % 7)
        return first_sunday + timedelta(days=14)
    
    elif day_rule == "first_monday":
        # 9月第一个星期一 (劳动节)
        d = datetime(year, month, 1)
        return d + timedelta(days=(0 - d.weekday()) % 7)
    
    elif day_rule == "first_monday_dec":
        # 12月第一个星期一 (网络星期一)
        d = datetime(year, month, 1)
        return d + timedelta(days=(0 - d.weekday()) % 7)
    
    elif day_rule == "last_monday":
        # 5月最后一个星期一 (阵亡将士纪念日)
        if month == 5:
            # 最后一天
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            # 往前找到周一
            return last_day - timedelta(days=(last_day.weekday() - 0) % 7)
        return datetime(year, month, 1)
    
    elif day_rule == "easter":
        # 复活节计算 (简化版 - 使用已知规律)
        # 2024: 3/31, 2025: 4/20, 2026: 4/5, 2027: 3/28
        easter_dates = {
            2024: (3, 31), 2025: (4, 20), 2026: (4, 5), 2027: (3, 28),
            2028: (4, 16), 2029: (4, 1), 2030: (4, 21), 2031: (4, 13)
        }
        if year in easter_dates:
            m, d = easter_dates[year]
            return datetime(year, m, d)
        return datetime(year, 4, 15)  # 默认
    
    elif day_rule == "mid_july":
        # Prime Day 通常在7月中旬 (15号左右)
        return datetime(year, 7, 15)
    
    elif day_rule == "fourth_thursday":
        # 11月第四个星期四 (感恩节)
        d = datetime(year, month, 1)
        first_day = d.weekday()
        # 第一个星期四
        first_thursday = d + timedelta(days=(3 - first_day) % 7)
        # 第四个星期四
        return first_thursday + timedelta(days=21)
    
    elif day_rule == "fourth_friday":
        # 黑色星期五是感恩节后一天
        d = datetime(year, 11, 1)
        first_day = d.weekday()
        first_thursday = d + timedelta(days=(3 - first_day) % 7)
        fourth_thursday = first_thursday + timedelta(days=21)
        return fourth_thursday + timedelta(days=1)  # Friday
    
    elif day_rule == "august_start":
        # 返校季通常8月开始
        return datetime(year, 8, 1)
    
    return datetime(year, month, 1)


def get_upcoming_reminders(days_ahead: int = 90) -> List[Dict]:
    """获取未来N天内的提醒"""
    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    
    reminders = []
    
    # 检查今年和明年的事件
    for event_name, month, day_rule, advance_days, categories in PROMOTION_EVENTS:
        for year in [current_year, next_year]:
            try:
                event_date = get_date_for_event(year, month, day_rule)
                
                # 计算提醒日期
                reminder_date = event_date - timedelta(days=advance_days)
                
                # 如果提醒日期在过去，跳过
                if reminder_date < today - timedelta(days=1):
                    continue
                
                # 如果事件已过但接近年底，检查下一年
                if event_date < today - timedelta(days=30) and month < 12:
                    continue
                
                # 如果在N天内
                if 0 <= (reminder_date - today).days <= days_ahead:
                    days_until = (reminder_date - today).days
                    reminders.append({
                        "event": event_name,
                        "event_date": event_date.strftime("%Y-%m-%d"),
                        "reminder_date": reminder_date.strftime("%Y-%m-%d"),
                        "days_until": days_until,
                        "advance_days": advance_days,
                        "categories": categories,
                        "urgency": "🔥 紧急" if days_until <= 7 else ("⏰ 即将到来" if days_until <= 21 else "📅 提前规划")
                    })
            except Exception as e:
                continue
    
    # 去重并排序
    seen = set()
    unique = []
    for r in reminders:
        key = (r["event"], r["advance_days"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    unique.sort(key=lambda x: (x["days_until"], -x["advance_days"]))
    return unique


def format_reminder_message(reminders: List[Dict]) -> str:
    """格式化提醒消息"""
    if not reminders:
        return "📅 未来90天内没有需要提醒的促销节点。"
    
    msg = "🇺🇸 **亚马逊促销提醒**\n\n"
    msg += "=" * 50 + "\n\n"
    
    current_event = None
    for r in reminders[:15]:  # 最多显示15条
        if r["event"] != current_event:
            current_event = r["event"]
            msg += f"\n🎯 **{current_event}** (活动日: {r['event_date']})\n"
        
        msg += f"{r['urgency']} · 提前{r['advance_days']}天提醒\n"
        msg += f"   📦 热销品类: {r['categories']}\n"
        msg += f"   📆 提醒日期: {r['reminder_date']} ({r['days_until']}天后)\n\n"
    
    msg += "=" * 50 + "\n"
    msg += "💡 建议: 根据提醒时间提前准备好广告素材和库存！\n"
    
    return msg


if __name__ == "__main__":
    reminders = get_upcoming_reminders(90)
    print(format_reminder_message(reminders))
