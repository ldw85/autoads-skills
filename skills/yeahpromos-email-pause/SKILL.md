---
name: yeahpromos-email-pause
description: 处理YeahPromos邮件通知，暂停对应的Google Ads广告系列。当用户发送"YeahPromos暂停"、"暂停广告"、"邮件暂停"、或转发YeahPromos的ASIN/MID终止通知邮件时激活。
---

# YeahPromos 邮件暂停技能

收到YeahPromos终止通知邮件时，解析邮件内容并暂停对应的广告系列。

## 邮件格式支持

### 格式1：直接有ASIN
```
ASIN:B0C7JCXX7K , Tub Works (MID:380763)
```
→ 直接提取ASIN

### 格式2：只有MID
```
Tub Works (MID:380763)
```
→ 通过MID→ASIN映射查找关联的ASIN

## 处理流程

1. 解析邮件，提取ASIN和MID
2. 查询MID→ASIN映射数据库
3. 汇总需要暂停的ASIN
4. 用户确认后执行暂停
5. 发送暂停结果通知

## 使用方式

将邮件内容发送给AI，AI会自动：
1. 解析ASIN和MID
2. 查询MID映射
3. 列出需要暂停的ASIN
4. 请求确认后暂停

## MID→ASIN映射数据库

路径：`/root/.openclaw/workspace/autoads/archer-roi/logs/mid_asin_mapping.json`

每次有订单时会自动更新，记录MID与ASIN的对应关系。

## 暂停记录

暂停日志：`/root/.openclaw/workspace/autoads/archer-roi/logs/paused_campaigns.json`

## 脚本位置

`scripts/pause_from_email.py` - 邮件解析和暂停处理脚本
