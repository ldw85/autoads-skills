---
name: landing-page-amazon
description: 高转化Amazon联盟营销落地页构建技能。适用于"创建产品落地页"、"优化Affiliate页面"、"提升Amazon跳转转化率"。核心理念：减少摩擦力（认知摩擦、交互摩擦、信任摩擦），移动端拇指法则。触发场景：用户提到"落地页"、"landing page"、"Amazon跳转"、"affiliate page"、"产品销售页"。
---

# Landing Page Amazon - 高转化Amazon联盟落地页技能

> **第一性原理：减少摩擦。** 当用户购买动力大于页面摩擦力时，转化自然发生。

---

## 核心理念：摩擦力三层级

### 认知摩擦 — 大脑层面的阻力
用户点进页面，看不懂卖什么、文案晦涩、排版杂乱 → 本能反应：关掉。

**消除方法：**
- 广告语和落地页主标题完全一致
- 首屏即结论，不是问题（如 "$29.95 · Ready to Gift" 而非 "The Gift Dilemma"）
- 文案直白，小学生也能看懂
- 落地页只推1个核心产品，其他放"次选"

### 交互摩擦 — 操作层面的阻力
加载>3秒、手机端要缩放、结账表单复杂 → 筛掉购买意向客户。

**消除方法：**
- 首屏出现 CTA 按钮（不要让用户滚下去才看到）
- 移动端 sticky CTA，固定在拇指区（屏幕中下方）
- 图片 WebP 压缩，懒加载
- 按钮足够大（min 44px touch target）
- 一个页面只有一个核心目标按钮

### 信任摩擦 — 心理层面的阻力
页面看起来像钓鱼网站，没有退换政策，没有真实评价 → 支付前防备心强。

**消除方法：**
- 展示真实用户评价（带 "Verified Purchase" 标签）
- 明确 Prime 配送 / 30天退货 / 安全支付等信任元素
- Affiliate 披露改写为正面表述（"我们只推荐自己会买的产品"）
- 首屏出现星级评分（如果产品评分好）

---

## 大拇指法则（移动端优化）

1. **用手机预览** — 所有核心文案必须在第一屏完成展示
2. **字体够大** — 在户外强光下也能看清（最小 16px）
3. **CTA 在拇指区** — 固定在屏幕中下方，滚动到哪里都能点
4. **加载速度** — 删除多余代码，压缩大图，懒加载非首屏图片

---

## 落地页结构（新标准）

### 单一产品页（推荐） — 用于付费广告落地页

```
1. HERO          → 标题 + 价格 + 产品卡 + 4个Benefits + CTA（全在第一屏）
2. STICKY CTA    → 移动端固定底部按钮（拇指区），桌面端滚动后淡入
3. WHY THIS      → 4张卡片，解答"为什么选这个"
4. SOCIAL PROOF  → 精选1条 Verified Buyer 评价
5. OTHER PICKS   → 3~7个次选产品（小卡片，不抢主推）
6. FAQ           → 4个最常见问题（折叠式）
7. FINAL CTA     → 再次出现主CTA
8. TRUST BAR     → Prime / 退货 / 安全支付 / 佣金说明
```

### 对比类页（多产品推荐） — 用于 SEO 有机流量页

```
1. HERO          → 主标题 + 3产品并排卡片（全在第一屏）
2. WHY THESE     → 4个选择理由（对比表格区）
3. SOCIAL PROOF  → 2条精选评价
4. OTHER PICKS   → 其余产品（5~7个）
5. FAQ + FINAL CTA + TRUST BAR
```

---

## CTA 设计规范

| 维度 | 正确做法 | 错误做法 |
|------|---------|---------|
| 按钮颜色 | 高对比色（珊瑚红 #E8523A 或 Amazon黄渐变） | 随页面主色调 |
| 文案 | "See Price on Amazon →" / "Shop on Amazon →" | "Buy Now" / "Purchase" |
| 紧迫感 | "Prime delivery · Order today" | 无紧迫感 |
| 按钮大小 | 桌面端 padding 14px 32px / 移动端全宽 | 小按钮、窄按钮 |
| 出现位置 | 首屏 + sticky + 页面底部（3处） | 只有页面底部 |

---

## 文案准则

### Headline 公式
- ✅ "The Best [Category] Under $[Price]"（价格锚定）
- ✅ "[Number] [Category] Under $[Price] — [Key Benefit]"（数字+利益）
- ❌ 不要写问题型标题（"How to choose..."）

### Scarcity / 紧迫感
- "🚚 Prime delivery — arrives before Easter"
- "⭐ 4.6★ from 3,800+ reviews"
- "✓ Prime fast shipping · No wrapping needed"

### 信任文案（Affiliate披露改写）
- ❌ "As an Amazon Associate, we earn from qualifying purchases."
- ✅ "We may earn a commission — but we only recommend products we'd buy ourselves."

---

## 移动端优先检查清单（生成页面前必查）

- [ ] Hero 区 CTA 在第一屏可见
- [ ] 移动端 sticky CTA 固定底部（position: fixed; bottom: 0）
- [ ] 字体大小：标题 clamp(28px, 7vw, 48px)，正文 min 16px
- [ ] 按钮高度 min 44px
- [ ] 图片懒加载（loading="lazy"）非首屏图片
- [ ] 首屏无需要缩放的元素
- [ ] 页面长度：核心说服在 1.5屏内完成

---

## 使用方法

### Step 1: 收集产品信息

| 参数 | 必填 | 说明 |
|------|------|------|
| Hero 产品名 | ✅ | 只选1个核心产品 |
| Hero 产品价格 | ✅ | 当前售价 |
| Hero Amazon链接 | ✅ | 联盟跳转链接 |
| Hero 产品图URL | ✅ | 产品真实图片URL |
| 次选产品列表 | ❌ | 其他产品（名称/价格/链接/图片）。**注意**：如果只有1个产品，此数组设为空，Other Picks区域自动隐藏 |
| 目标用户痛点 | ✅ | 1句话描述产品解决什么问题 |
| 核心Benefit | ✅ | 4个以内（格式：动词+具体好处） |
| 精选用户评价 | ✅ | 1条真实好评（带评分） |

### Step 2: 选择页面类型

- **单一产品页**（推荐）：广告落地页，1个Hero产品，次选区域条件显示（有空才渲染）
- **多产品对比页**：SEO有机流量页，3产品并排Hero

### Step 3: 生成页面

按照上方结构模板生成，内容必须覆盖：
1. 首屏出现 CTA + 价格 + 评分 + Benefits
2. sticky CTA（移动端固定底部）
3. 其他产品不干扰主推
4. FAQ 解答物流/退换/适合人群问题

---

## 参考文件

- `references/sections.md` — 详细 section 模板（已更新为新结构）
- `references/copy-formulas.md` — 完整文案公式库

---
