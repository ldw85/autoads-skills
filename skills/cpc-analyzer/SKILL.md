---
name: cpc-analyzer
description: Google Ads CPC 分析技能。根据亚马逊商品价格和联盟佣金率计算最大合理CPC，与当前出价对比，找出需要提价的广告。触发词：CPC分析、计算最大CPC、检查出价、cpc统计。
credentials:
  - Google Ads API 凭证（via autoads 配置）
env:
  required: []
  autoads_config: true
---

# CPC Analyzer Skill

分析 Google Ads 广告系列的 CPC 出价是否合理。

## 核心功能

1. **计算最大合理 CPC**
   - 公式：`价格 × 佣金率 / 50 × 6.9 × 0.9`
   - 数据来源：Decodo 获取亚马逊实时价格
   - 支持固定佣金率或从联盟提取

2. **对比分析**
   - 获取所有启用广告的当前 CPC 出价
   - 计算理论最大 CPC
   - 标识需要提价的广告（当前出价 < 最大 CPC）

## 使用方式

### 完整 CPC 分析（两个账号）
```bash
python3 /root/.openclaw/workspace/autoads/archer-roi/check_cpc.py --rate 0.06
```

### 指定账号分析
```bash
python3 /root/.openclaw/workspace/autoads/archer-roi/check_cpc.py --account 3674729801 --rate 0.06
```

### 从联盟提取佣金率
```bash
python3 /root/.openclaw/workspace/autoads/archer-roi/check_cpc.py --network yeahpromos --days 90
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--account` | Google Ads 客户ID（逗号分隔多账号） | 3674729801,6052559425 |
| `--rate` | 固定佣金率（如 0.06 表示 6%） | 从联盟获取 |
| `--network` | 联盟网络（yeahpromos/archer） | yeahpromos |
| `--days` | 从联盟获取佣金的最近天数 | 90 |

## 输出示例

```
====================================================================================================
 CPC Check - Calculate Maximum CPC vs Current Bid
====================================================================================================

Found 32 campaigns where max CPC > current CPC:

Campaign ID     Campaign Name                              Clicks  Current CPC    Max CPC
----------------------------------------------------------------------------------------------------
23737317993     DYNAMIC SAUNAS Barcelona                      0 $     1.2000 $  14.1587 (+12.9587)
23715941245     DC HOUSE Golf Cart Battery                 198 $     0.5600 $   6.3341 (+5.7741)
...

====================================================================================================
 Summary
====================================================================================================

Total ASINs processed: 106
Needs CPC increase: 32
Within range: 74
Errors: 0
```
