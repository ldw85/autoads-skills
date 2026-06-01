---
name: search-term-analyzer
description: 分析Google Ads广告系列的搜索词报告，判断语义相关性并生成否定词建议
trigger_on:
  - 搜索词报告分析
  - 搜索词分析
  - 否定词分析
  - analyze search terms
  - negative keyword analysis
  - 批量搜索词
  - batch analyze
---

# 搜索词分析Skill

用于分析Google Ads广告系列的搜索词报告，判断哪些搜索词不相关并建议添加为否定词。

## 使用方式

```
# 单个广告系列分析
分析搜索词报告 23888315496
分析这个广告系列的搜索词 DC HOUSE

# 批量分析（所有有效广告系列）
批量分析搜索词报告 PartnerBoost
```

## 工作流程

1. 获取广告系列的搜索词（过去30天，有点击的）
2. 输出搜索词列表给用户
3. 用户把搜索词发给你
4. 用AI语义分析判断不相关搜索词
5. 用户确认后添加否定词

## 参数说明

- `--campaign-id`: 广告系列ID（优先级高于--campaign）
- `--campaign`: 广告系列名称（模糊匹配）
- `--customer-id`: Google Ads账户ID，默认6660356395
- `--days`: 分析天数，默认30
- `--auto-ai`: 自动调用AI分析

## 支持的账户

- Archer: 6660356395
- YeahPromos: 6052559425
- PartnerBoost: 4772859239

## 脚本位置

- 单个分析: `/root/.openclaw/workspace/scripts/search_term_negatives.py`
- 批量分析: `/root/.openclaw/workspace/scripts/search_term_all.py`

## 示例

```bash
# 分析Archer账户的广告系列
python3 scripts/search_term_negatives.py --campaign-id 23888315496

# 批量分析PartnerBoost
python3 scripts/search_term_negatives.py --customer-id 4772859239 --campaign "" --days 30
```

## 添加否定词

```bash
python3 scripts/search_term_negatives.py --campaign-id 23888315496 --add "zebronics projector" --match-type PHRASE
```