---
name: landing-page-generator
description: Generate high-converting landing pages for products, services, and lead generation. Use when creating marketing pages, product launches, squeeze pages, or digital asset sales pages.
---

# Landing Page Generator

## Overview

> **核心原则：锁死用户的视线。** 当用户的视线被你掌控时，转化自然发生。

## Part 1: 视线停留六法则

> 参考 David 的联盟营销素材设计原则（2026-05-23）

### 〔01〕页面左上角 — 第一落点

用户打开页面，视线的第一个落点几乎固定在左上角。这是几十年阅读习惯训练出来的本能。

**落地页设计：**
- ❌ 不要在这里放 logo（浪费黄金位置）
- ✅ 在这里放一句话，明确告诉用户「你来对地方了」
- 示例："🎯 $50以下最好的降噪耳机" 或 "✅ 3000+真实好评的选择"

### 〔02〕标题 — 第一个真正意义上的停留点

如果左上角是第一落点，那么标题就是第一个停留点。标题决定了用户要不要继续往下看。

**标题有效性来自：**
- 不是创意，而是和用户当下状态的匹配程度
- 当用户带着问题或需求来到页面，标题能精准响应这个状态，视线自然会停下来
- 必须是结论型，不是问题型（如 "Best [Category] Under $50" 而非 "How to choose..."）

### 〔03〕图片是强制停留点

人眼对视觉内容有本能反应，图片和视频会强制打断扫视节奏。

**高停留图片的特征：**
- ✅ 包含具体数字（"4.6★ from 3,800+ reviews"）
- ✅ 对比信息（前/后、使用/不使用)
- ✅ 人脸（人眼对人脸的识别是出厂设置级别的本能）
- ❌ 纯装饰性图片（零点几秒就划过）

### 〔04〕主动寻找价格和数字

数字代表客观，代表可信度。用户在扫视时会主动搜索数字。

**数字优先原则：**
- 核心卖点能用数字表达的，就不要用文字
- 价格、评分、评论数、折扣比例、用户数等都是强效信息
- 数字在视觉上与文字有明显区别，天然吸睛

### 〔05〕CTA按钮 — 决策时刻的停留

按钮出现在用户考虑要不要行动的时刻。

**按钮设计的两点有效性：**
1. **清晰**：用户需要知道点击后会发生什么
2. **低风险感**：用户需要感觉这个动作的代价不高

**按钮文案示例：**
- ✅ "See Price on Amazon →" / "Check It on Amazon"
- ❌ 避免 "Buy Now" / "Purchase" （压力过大）

### 〔06〕页面底部 — 二次确认

有一类用户会把页面从头读到尾。他们已经有购买意向，只差最后一个理由。


**底部的作用：**
- 重复核心卖点
- 放精选用户评价
- 再放一个按钮（成交的最后一次机会）
- 针对「还在犹豫」的用户做最后的说服

---

### 决策路径映射

| 视线停留点 | 对应的用户心理 |
|----------|-------------|
| 左上角 | 建立信任：「我是来对地方了吗？」 |
| 标题 | 去留决定：「这跟我有关吗？」 |
| 图片+数字 | 信息获取：「真的有用吗？」 |
| CTA按钮 | 行动触发：「我要点击吗？」 |
| 页面底部 | 最后说服：「我应该买！」 |

---

## Core Capabilities

### 1. Page Templates

**Pre-built templates for:**
- Product launch pages (pre-launch and launch)
- Squeeze pages (email capture)
- Webinar registration pages
- Digital product sales pages (courses, ebooks, templates)
- Service booking pages
- Affiliate review pages
- Comparison pages (Product A vs Product B)
- Thank you/confirmation pages

### 2. Copywriting Frameworks

**Built with proven frameworks:**
- AIDA (Attention, Interest, Desire, Action)
- PAS (Problem, Agitation, Solution)
- Story-based hooks
- Social proof integration
- Objection handling
- Scarcity/urgency elements

### 3. SEO Optimization

**Automatically includes:**
- Optimized meta tags (title, description, keywords)
- Header tags (H1, H2, H3)
- Alt text for images
- Structured data (schema markup)
- Mobile-responsive design
- Fast loading structure

### 4. Conversion Elements

**Built-in conversion triggers:**
- Clear value propositions
- Benefit-oriented bullet points
- Testimonials/social proof
- FAQ sections
- Multiple CTAs (above and below fold)
- Guarantee/risk-reversal statements
- Countdown timers
- Limited-time offers

### 5. Responsive Design

**Optimized for:**
- Desktop (1920px+)
- Tablet (768px - 1024px)
- Mobile (320px - 767px)
- Cross-browser compatibility

## Quick Start

### Generate Product Launch Page

```python
# Use scripts/generate_landing.py
python3 scripts/generate_landing.py \
  --type product-launch \
  --product "SEO Course" \
  --price 299 \
  --benefits "learn SEO,rank higher,get traffic" \
  --testimonials 3 \
  --cta "Enroll Now" \
  --output product_launch.html
```

### Generate Squeeze Page

```python
python3 scripts/generate_landing.py \
  --type squeeze \
  --headline "Get Free SEO Checklist" \
  --benefits "checklist,tips,strategies" \
  --cta "Send Me The Checklist" \
  --output squeeze.html
```

### Generate Affiliate Review Page

```python
python3 scripts/generate_landing.py \
  --type affiliate-review \
  --product "Software XYZ" \
  --affiliate-link "https://example.com/affiliate" \
  --pros 5 \
  --cons 2 \
  --cta "Try XYZ Now" \
  --output affiliate_review.html
```

## Scripts

### `generate_landing.py`
Generate landing page from parameters.

**Parameters:**
- `--type`: Page type (product-launch, squeeze, webinar, digital-product, service, affiliate-review, comparison, thank-you)
- `--headline`: Main headline
- `--subheadline`: Supporting subheadline
- `--product`: Product/service name
- `--price`: Price or "Starting at $X"
- `--benefits`: Comma-separated benefits
- `--features`: Comma-separated features
- `--testimonials`: Number of testimonials to include
- `--cta`: Call-to-action button text
- `--guarantee`: Guarantee text (optional)
- `--urgency`: Urgency message (optional)
- `--output`: Output file

**Example:**
```bash
python3 scripts/generate_landing.py \
  --type product-launch \
  --headline "Master SEO in 30 Days" \
  --subheadline "Complete course with live coaching" \
  --product "SEO Mastery Course" \
  --price 299 \
  --benefits "rank higher,drive traffic,boost sales" \
  --features "video lessons,templates,community" \
  --testimonials 5 \
  --cta "Enroll Now - Save 50% Today" \
  --guarantee "30-day money-back guarantee" \
  --urgency "Limited spots - Offer ends Friday" \
  --output landing.html
```

### `optimize_copy.py`
Optimize existing landing page copy.

**Parameters:**
- `--input`: Input HTML file
- `--framework`: Copywriting framework (AIDA, PAS, story)
- `--add-social-proof`: Add testimonial placeholders
- `--add-urgency`: Add scarcity elements
- `--output`: Optimized output

### `ab_test_variations.py`
Generate A/B testing variations.

**Parameters:**
- `--input`: Base landing page
- `--variations`: Number to generate (default: 3)
- `--test-elements`: What to test (headline, cta, price, colors)
- `--output-dir`: Output directory for variations

## Page Templates

### Product Launch Page Structure

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Product Name] - Transform Your Life</title>
  <meta name="description" content="...">
  <!-- SEO meta tags -->
  <!-- Schema markup -->
</head>
<body>
  <!-- Hero Section -->
  <section class="hero">
    <!-- 〔01〕左上角信任建立 -->
    <div class="hero-badge">🎯 [Value Hook: $50以下最好/3000+真实好评...]</div>
    
    <!-- 〔02〕标题 — 第一个停留点（结论型，不是问题型） -->
    <h1>[Headline: Best XXX Under $50 — Key Benefit]</h1>
    <p class="hero-sub">[Subheadline with benefits separated by ·]</p>
    
    <!-- 〔04〕数字吸睛：价格 + 评分 + 评论数 -->
    <div class="hero-price-rating">
      <span class="price">$[Price]</span>
      <span class="rating">⭐ [Rating] · [Reviews]+ reviews</span>
    </div>
    
    <!-- 〔05〕CTA按钮 — 首屏必须出现 -->
    <a href="[Affiliate Link]" class="cta">[CTA: See Price on Amazon →]</a>
    
    <!-- 信任元素 -->
    <p class="hero-trust">✓ Prime delivery · ↩️ 30-day returns · 🔒 Secure checkout</p>
  </section>

  <!-- Problem Section -->
  <section class="problem">
    <h2>Struggling with [Problem]?</h2>
    <p>You're not alone...</p>
  </section>

  <!-- Solution Section -->
  <section class="solution">
    <h2>Introducing [Product Name]</h2>
    <ul>[Benefits List]</ul>
  </section>

  <!-- Features Section -->
  <section class="features">
    <h2>What You'll Get</h2>
    <div class="feature-grid">
      [Feature 1]
      [Feature 2]
      [Feature 3]
    </div>
  </section>

  <!-- Testimonials Section -->
  <section class="testimonials">
    <h2>What People Are Saying</h2>
    [Testimonial Cards]
  </section>

  <!-- Pricing Section -->
  <section class="pricing" id="pricing">
    <h2>Choose Your Plan</h2>
    [Pricing Cards]
  </section>

  <!-- Guarantee Section -->
  <section class="guarantee">
    <h2>[Guarantee]</h2>
    <p>[Risk-free language]</p>
  </section>

  <!-- FAQ Section -->
  <section class="faq">
    <h2>Frequently Asked Questions</h2>
    [FAQ Items]
  </section>

  <!-- Final CTA -->
  <section class="final-cta">
    <a href="#pricing" class="cta">[CTA]</a>
    <p>[Urgency message]</p>
  </section>

  <!-- Footer -->
  <footer>[Legal links, contact info]</footer>
</body>
</html>
```

## Best Practices

### Headlines — 〔02法则〕第一个停留点
- **Length:** 6-12 words maximum
- **Format:** 结论型，不是问题型（例如 "Best [Category] Under $50" 而非 "How to choose..."）
- **匹配度**：与用户当下状态精准匹配，决定用户是否继续阅读

### CTAs — 〔05法则〕决策时刻的停留
- **Positioning:** 首屏 + sticky + 底部（三处出现）
- **Color:** 高对比色（珊瑚红 #E8523A 或 Amazon黄渐变）
- **Text:** 低压力查询型（"See Price on Amazon →" 而非 "Buy Now"）
- **Urgency:** 添加 Prime delivery 等低风险感知

### Social Proof — 〔03法则〕强制停留点
- ** Placement:** 紧邻 CTA，增加决策信心
- **数字优先:** 包含具体评分和评论数（如 "4.6★ from 3,800+ reviews"）
- **人脸加成:** 如有真实用户照片，放左上角增强注意力

### Pricing — 〔04法则〕主动搜索的数字
- **锚定:** 显示原价格对比（Save $50 was $199）
- **突出:** 价格要用大号字体，放在首屏可见位置
- **心理:** 用 $299 而非 $300

### Mobile Optimization — 大拇指法则
- **首屏完成:** CTA 在第一屏可见
- **Sticky CTA:** 移动端固定底部（拇指区）
- **字体:** 最小 16px
- **触摸:** 按钮 min 44px

## Automation

### Bulk Landing Page Generation

```bash
# Generate landing pages for multiple products
0 10 * * * /path/to/landing-page-generator/scripts/bulk_generate.py \
  --csv products.csv \
  --output-dir /path/to/landing-pages
```

### A/B Test Automation

```bash
# Generate variations for top pages
0 9 * * 1 /path/to/landing-page-generator/scripts/ab_test_variations.py \
  --input /path/to/top-pages/ \
  --variations 3 \
  --output-dir /path/to/ab-tests
```

## Integration Opportunities

### With Product Description Generator
```bash
# 1. Generate product description
product-description-generator/scripts/generate_description.py \
  --product "Course Name"

# 2. Extract benefits
# 3. Generate landing page
landing-page-generator/scripts/generate_landing.py \
  --benefits "[extracted]"
```

### With Review Summarizer
```bash
# 1. Get review insights
review-summarizer/scripts/scrape_reviews.py --url "[product_url]"

# 2. Extract pros/cons
# 3. Generate review page
landing-page-generator/scripts/generate_landing.py \
  --type affiliate-review \
  --pros "[extracted]" \
  --cons "[extracted]"
```

---

**Build pages. Convert visitors. Scale revenue.**
