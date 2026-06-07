---
name: landing-page-amazon
description: 高转化Amazon联盟营销落地页构建技能。适用于"创建产品落地页"、"优化Affiliate页面"、"提升Amazon跳转转化率"。核心理念：锁死用户视线（视线停留六法则+拇指法则），移动端拇指法则。触发场景：用户提到"落地页"、"landing page"、"Amazon跳转"、"affiliate page"、"产品销售页"。
---

# Landing Page Amazon - 高转化Amazon联盟落地页技能

> **核心原则：锁死用户的视线。** 当用户的视线被你掌控时，转化自然发生。
> **本skill融合 David 的「联盟营销视线锁定」原则（2026-05-23）**

---

## Part 1: 视线停留六法则

### 〔01〕页面左上角 — 第一落点

用户打开页面，视线的第一个落点几乎固定在左上角。

**落地页设计：**
- ❌ 不要在这里放 logo
- ✅ 在这里放一句话，告诉用户"你来对地方了"
- 示例："🎯 $50以下最好的降噪耳机"

### 〔02〕标题 — 第一个真正意义上的停留点

标题决定了用户要不要继续往下看。
- 必须是结论型（如 "Best [Category] Under $50"），不是问题型

### 〔03〕图片是强制停留点

**高停留图片：** 含具体数字、对比信息、人脸

### 〔04〕主动寻找价格和数字

数字代表客观、可信度。核心卖点能用数字就不用文字。

### 〔05〕CTA按钮 — 决策时刻的停留

**有效性两点：** 1) 清晰 2) 低风险感
- ✅ "See Price on Amazon →"
- ❌ 避免 "Buy Now"

### 〔06〕页面底部 — 二次确认

针对从头读到尾的用户，只差最后一个理由

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
