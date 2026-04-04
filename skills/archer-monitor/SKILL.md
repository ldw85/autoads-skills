---
name: archer-monitor
description: Archer 联盟平台监控技能。检查产品状态、计算广告 ROI、监控被删产品并自动暂停广告。触发词：检查产品状态、计算广告收益、运行产品监控、archer 监控、暂停已删产品。
credentials:
  - Archer API 凭证（环境变量 ARCHER_USERNAME, ARCHER_PASSWORD）
  - Google Ads API 凭证（via autoads 配置）
env:
  required:
    - ARCHER_USERNAME
    - ARCHER_PASSWORD
  autoads_config: true
---

# Archer Monitor Skill

Archer 联盟平台的监控中心，支持：
1. **检查产品状态** — 用 `/check_product` 验证 ASIN 是否在 Archer 目录中仍然有效
2. **计算广告 ROI** — 合并 Google Ads 花费 + Archer 佣金，计算每个链接的收益率
3. **产品监控** — 每2小时自动检测被删产品，自动暂停对应 Google Ads 广告系列

## 核心脚本

### 1. 产品状态检查
```bash
python3 /root/.openclaw/workspace/archer-roi/check_product.py --asin ASIN
# 或批量检查
python3 /root/.openclaw/workspace/archer-roi/check_product.py --asin-file /path/to/asins.txt
```

### 2. ROI 报告
```bash
# 最近30天
python3 /root/.openclaw/workspace/archer-roi/main.py --report

# 指定日期范围
python3 /root/.openclaw/workspace/archer-roi/main.py --report --start 20260301 --end 20260331
```

### 3. 产品监控（检测被删产品并暂停广告）
```bash
# 执行一次监控
python3 /root/.openclaw/workspace/archer-roi/monitor_main.py --run

# 查看状态
python3 /root/.openclaw/workspace/archer-roi/monitor_main.py --status

# 列出所有被删产品
python3 /root/.openclaw/workspace/archer-roi/monitor_main.py --list-removed

# 手动暂停指定 ASIN
python3 /root/.openclaw/workspace/archer-roi/monitor_main.py --pause-asin B08DL8WH9V
```

## `/check_product` API 响应

| 状态 | 响应 |
|------|------|
| 有效 | `{"success":"ASIN passed all checks"}` |
| 无效 | `{"detail":"ASIN not available for advertising"}` |

## 定时任务

产品监控已配置为每2小时自动运行：
```
0 */2 * * * cd /root/.openclaw/workspace/archer-roi && bash scripts/run-monitor.sh
```

## 触发方式

- "检查 ASIN B082LV2VH6 的状态"
- "帮我检查一下这个产品的广告状态"
- "计算最近7天的广告 ROI"
- "运行一次产品监控"
- "哪些产品从 Archer 下架了"
