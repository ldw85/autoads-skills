---
name: pause-asin-campaigns
description: |
  按 ASIN 列表批量暂停 Google Ads 广告系列，并把暂停原因追加到广告系列名称末尾。

  **功能**：
  - 输入一组 ASIN（逗号分隔）+ 一个暂停原因（reason）
  - 自动从 Google Ads 中找出所有 final_url 匹配这些 ASIN 的 ENABLED 广告系列
  - 批量改为 PAUSED 状态
  - 在广告系列名末尾追加 `[PAUSED:{reason}-YYYYMMDD]` 标签（幂等，不会重复贴）
  - 默认 dry-run，加 `--execute` 才真正暂停

  **使用场景**：
  - 当 ROI 报告发现某些 ASIN 高花费 0 佣金、需要批量止损时
  - 当库存监控/链接监控等流程发现需要暂停某 ASIN 的所有系列时
  - 任何"按 ASIN 暂停广告系列"的需求

  **支持的账号**（customer_id）：
  - Archer: 6660356395 (默认)
  - YeahPromos: 6052559425
  - PartnerBoost: 4772859239

  **铁律**：
  - 默认 dry-run，必须 `--execute` 才真暂停
  - 命名标签包含日期，便于事后追溯（与库存监控 v6 的 `[PAUSED:xxx]` 双池一致风格）
  - 已经 PAUSED 的系列不会被再处理
triggers:
  - 暂停 ASIN
  - 暂停广告系列
  - 暂停 asin
  - pause asin
  - 按 ASIN 暂停
  - 批量暂停广告系列
  - zero-roi 暂停
  - 高花费零转化暂停
---

# pause-asin-campaigns 技能

## 用途

按 ASIN 批量暂停 Google Ads 广告系列，并把暂停原因永久记录在广告系列名称里。

## 输入参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `--asins` | ✅ | 逗号分隔的 ASIN 列表，如 `B0CLS8B1BK,B086QJVHVD` |
| `--reason` | ✅ | 暂停原因短标签，如 `zero-roi` / `low-cvr` / `out-of-stock` / `link-broken` |
| `--customer-id` | ⬜ | Google Ads 客户 ID（默认 `6660356395` Archer） |
| `--execute` | ⬜ | 默认 dry-run；带此参数才真正暂停 |

## 调用方式（CLI）

```bash
bash /root/.openclaw/workspace/autoads/archer-roi/scripts/run_pause_zero_roi.sh \
  --asins B0CLS8B1BK,B086QJVHVD,B0G363HM2K \
  --reason zero-roi
```

dry-run 输出会列出所有匹配的 ENABLED 广告系列。**确认无误后**加 `--execute`：

```bash
bash /root/.openclaw/workspace/autoads/archer-roi/scripts/run_pause_zero_roi.sh \
  --asins B0CLS8B1BK,B086QJVHVD,B0G363HM2K \
  --reason zero-roi \
  --execute
```

## 三账号示例

```bash
# Archer (默认)
bash run_pause_zero_roi.sh --asins B0XXX,B0YYY --reason zero-roi --execute

# YeahPromos
bash run_pause_zero_roi.sh --asins B0XXX --reason out-of-stock \
  --customer-id 6052559425 --execute

# PartnerBoost
bash run_pause_zero_roi.sh --asins B0XXX --reason low-cvr \
  --customer-id 4772859239 --execute
```

## 输出

- ✅ `paused. new name: <旧名> [PAUSED:<reason>-<YYYYMMDD>]`
- 已是 PAUSED 状态的会被自动跳过（不会再贴标签）
- 失败时打印 `❌ <campaign_id> FAILED: <error>`，其他系列继续执行

## 调用协议（David 拍板流程）

1. **AI 先 dry-run**，列出待暂停 Campaign 列表 + 名字 + 关联 ASIN
2. **David 在飞书拍板**（可剔除部分 ASIN）
3. **AI 加 `--execute` 真执行**
4. **AI 反查**：必要时 `python3 monitor_product_status.py` 或飞书报告里确认状态

与库存监控 v6 / Google Ads API 破坏性操作的「拍板+审计+反查」三阶段铁律一致。

## 工程实现

- 脚本：`autoads/archer-roi/scripts/pause_zero_roi_asins.py`
- 包装：`autoads/archer-roi/scripts/run_pause_zero_roi.sh`
- 用 GAQL 查 `ad_group_ad.ad.final_urls`（正则 `amazon\.com/dp/(B0[A-Z0-9]{8})` 抽 ASIN），与库存监控 v5 的 ASIN 抽取铁律完全一致
- 命名追加用 `[PAUSED:{reason}-{YYYYMMDD}]` 标签，与 `[PAUSED:price_zero]` / `[PAUSED:unavailable]` 等历史标签同源风格
- 用 `protobuf_helpers.field_mask(None, camp._pb)` 自动构造 update_mask，兼容 Google Ads API v23
