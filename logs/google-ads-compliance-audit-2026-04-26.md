# Google Ads "不公平优势" 合规审计报告

**审计日期**: 2026-04-26
**审计账户数**: 4个

---

## 账户概览

| 账户ID | 账户名称 | 广告系列数 | 涉及ASIN数 | 主要投放域名 |
|--------|----------|-----------|-----------|-------------|
| 3674729801 | Archer | 174 | 166 | amazon.com, capcut.com, techruling.com |
| 3645726299 | Ads-Manuel-main | 7 | 3 | christ.de, techruling.com, amazon.com, crocs.de |
| 4772859239 | Partnerboost | 32 | 32 | amazon.com |
| 6052559425 | Yeahpromos | 138 | 138 | amazon.com |

---

## 1. 关键词分析

### 各账户关键词对比

| 账户 | 关键词特征 |
|------|-----------|
| **Archer** | 多品类混合: capcut.com(视频编辑), amazon.com(多品类), techruling.com(科技评测) |
| **Ads-Manuel-main** | 欧洲站点: christ.de(德国珠宝), crocs.de(德国洞洞鞋) |
| **Partnerboost** | 全Amazon联盟, ASIN直接对应 |
| **Yeahpromos** | 全Amazon联盟, ASIN直接对应 |

### 风险点
- ⚠️ **Archer** 和 **Yeahpromos** 都投放 amazon.com, 可能关键词重叠
- ⚠️ **Ads-Manuel-main** 的 techruling.com 与其他账户 techruling.com 域名重叠

---

## 2. 广告文案分析

### 命名模式

| 账户 | 命名模式 |
|------|----------|
| **Archer** | `Sales-Search-3-christde`, `Sales-Search-4-crocs` |
| **Ads-Manuel-main** | 多为第三方品牌域名直接投放 |
| **Partnerboost** | `yeahpromos - {ProductName}` |
| **Yeahpromos** | `yeahpromos - {ASIN} - {ProductName}` |

### 风险点
- ⚠️ **Partnerboost** 和 **Yeahpromos** 命名模式相似, 都包含 "yeahpromos"
- ⚠️ **Yeahpromos** 账户命名直接包含完整产品信息

---

## 3. 最终URL分析

### 域名分布

| 账户 | 主要域名 | 花费占比 |
|------|---------|----------|
| Archer | amazon.com | 1435.87/1627.09 (88%) |
| Archer | capcut.com | 132.10 (8%) |
| Archer | techruling.com | 49.12 (3%) |
| Ads-Manuel-main | christ.de | 76.90 (29%) |
| Ads-Manuel-main | techruling.com | 76.90 (29%) |
| Ads-Manuel-main | amazon.com | 59.88 (22%) |
| Ads-Manuel-main | crocs.de | 40.60 (15%) |
| Partnerboost | amazon.com | 201.66 (100%) |
| Yeahpromos | amazon.com | 2859.84 (100%) |

### 重叠域名
- ⚠️ **amazon.com**: Archer + Ads-Manuel-main + Partnerboost + Yeahpromos **全部4个账户都在投放**
- ⚠️ **techruling.com**: Archer + Ads-Manuel-main **2个账户投放**

### 风险评估
🚨 **高风险**: 4个账户都投放amazon.com, 可能被认定为同一主体控制的关联账户

---

## 4. 账户结构风格

| 账户 | 结构特征 |
|------|----------|
| **Archer** | 174个系列, 结构较乱, 多品类混合 |
| **Ads-Manuel-main** | 7个系列, 结构简洁 |
| **Partnerboost** | 32个系列, 命名规范: `yeahpromos - {ASIN}` |
| **Yeahpromos** | 138个系列, 命名最规范: `yeahpromos - {ASIN} - {Product}` |

---

## 5. 技术信号

### MCC管理关系
- ✅ 4个账户使用同一个Google Ads Service Account (`awesome-ridge-478918-t7`)
- ⚠️ **同一MCC下管理** - 这是最强的关联信号

### 登录IP
- 需要用户提供日常登录IP范围

### 支付方式
- 需要用户提供信用卡BIN码对比

---

## 6. 合规风险总结

### 🚨 高风险项

| 风险项 | 涉及账户 | 风险等级 |
|--------|---------|----------|
| 同一MCC管理 | 全部4个 | 🔴 严重 |
| 都投放amazon.com | 全部4个 | 🔴 严重 |
| 命名模式相似 | Partnerboost + Yeahpromos | 🟠 中等 |
| techruling.com重叠 | Archer + Ads-Manuel-main | 🟠 中等 |

### 🟡 中风险项

| 风险项 | 涉及账户 | 风险等级 |
|--------|---------|----------|
| 多账户amazon关联投放 | 全部4个 | 🟡 中等 |

---

## 7. 建议措施

### 短期缓解
1. **分离MCC管理**: 考虑将Yeahpromos和Partnerboost转移到不同MCC
2. **差异化URL**: 使用不同的追踪参数区分各账户
3. **分散登录IP**: 不同账户使用不同IP段登录

### 关键词隔离
1. 各账户投放不同品类, 减少关键词重叠
2. 避免同时投放同一品牌/产品关键词

### 长期策略
1. 评估是否真正需要4个独立账户
2. 考虑合并到2个账户(按联盟分组)
3. 建立清晰的账户隔离策略

---

## 8. 需要补充的信息

- [ ] 各账户登录IP范围
- [ ] 支付方式(BIN码)对比
- [ ] 浏览器/设备指纹使用情况
- [ ] 共享的GA/GTM资源
- [ ] 转化跟踪代码是否相同

---

**报告生成时间**: 2026-04-26 19:45
**数据来源**: Google Ads API
