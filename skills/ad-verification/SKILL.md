# Ad Verification Skill

广告业务规则校验技能。检查 Google Ads 广告系列是否符合预设的业务规则。

## 功能

- 校验广告账号下所有广告系列
- 校验指定广告系列
- 生成详细的校验报告

## 业务规则

| 检查项 | 规则 |
|--------|------|
| Campaign Status | 必须为 `PAUSED` |
| Budget | 必须在 $10-$100 范围内 |
| Bidding Strategy | 必须为 `MAXIMIZE_CLICKS` |
| Network | SEARCH + PARTNER_SEARCH_NETWORK 启用，Content Network 禁用 |
| Geo/Language | US + English |
| Ad Type | 必须是 `RESPONSIVE_SEARCH_AD` |
| Final URL | `?` 前内容设为 Final URL，`?` 后内容设为 URL suffix |
| Tracking Template | 未提供时不设置；提供时自动添加 `url={lpurl}` |
| Sitelink 数量 | 必须 3 个 |
| Sitelink URLs | URL 规则同 Final URL |
| Sitelink 标题 | 不能为空 |

## 使用方式

### 校验所有广告系列

```
/ad-verify all
```

### 校验指定广告系列

```
/ad-verify campaign <campaign_id>
```

### 查看帮助

```
/ad-verify help
```

## 输出格式

校验结果以表格形式展示，包含：
- ✅ 通过的项目
- ❌ 未通过的项目及详情

---
本技能使用 `scripts/verify_ads.py` 脚本执行校验。
