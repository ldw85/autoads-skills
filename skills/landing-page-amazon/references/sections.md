# Landing Page Amazon - Section Templates (New Structure)

> 基于摩擦力理论 + 拇指法则的新标准结构
> 所有模板均为纯 HTML/CSS/JS（无 Astro 组件依赖）

---

## Section 1: HERO（首屏 — 核心说服区）

**设计原则：**
- 首屏必须出现：标题 + 价格 + 评分 + 4个Benefits + CTA
- 标题结论性，不要问题型
- CTA 按钮醒目（珊瑚红 #E8523A 或 Amazon 黄渐变）
- 首屏完成核心说服，不要让用户滚动

```html
<section class="hero">
  <!-- 标签 -->
  <div class="hero-badge">🐰 Easter 2026</div>

  <!-- 主标题：结论型 -->
  <h1>The Best [Category] Under $[Price]</h1>
  <p class="hero-sub">
    [核心卖点1] · [核心卖点2] · [核心卖点3]
  </p>

  <!-- Hero 产品卡片 -->
  <div class="hero-product">
    <div class="hero-product-img">
      <span class="img-badge">🏆 #1 Pick for [场景]</span>
      <img src="[Hero产品图URL]" alt="[产品名]" loading="eager">
    </div>
    <div class="hero-product-body">
      <div class="hero-product-name">[产品名]</div>
      <div class="hero-product-tagline">[短 tagline]</div>
      <div class="hero-product-rating">
        <span class="hero-product-stars">★★★★☆</span>
        <span class="hero-product-reviews">[评分] · [评论数] reviews</span>
      </div>
      <div class="hero-product-price">$[价格]</div>
      <div class="hero-product-benefit">✓ [Benefit 1]</div>
      <div class="hero-product-benefit">✓ [Benefit 2]</div>
      <div class="hero-product-benefit">✓ [Benefit 3]</div>
      <div class="hero-product-benefit">✓ [Benefit 4]</div>
    </div>
  </div>

  <!-- 主CTA（必须在首屏） -->
  <a href="[Amazon链接]" class="hero-cta-btn">
    🐰 See Price on Amazon →
  </a>

  <p class="hero-trust">🚚 Prime delivery · ✓ No wrapping needed · ↩️ 30-day returns</p>
</section>
```

---

## Section 2: STICKY CTA（移动端固定底部按钮）

**设计原则：**
- 移动端：position: fixed; bottom: 0; 全宽
- 桌面端：滚动出 Hero 后淡入（IntersectionObserver）
- 按钮颜色与 Hero CTA 一致

```html
<div class="sticky-cta-wrap" id="stickyWrap">
  <div class="sticky-cta">
    <div class="sticky-cta-info">
      <div class="sticky-cta-price">$[价格]</div>
      <div class="sticky-cta-note">⭐ [评分] · Prime delivery</div>
    </div>
    <a href="[Amazon链接]" class="sticky-cta-btn">
      🐰 Shop on Amazon →
    </a>
  </div>
</div>

<script>
(function(){
  var wrap = document.getElementById('stickyWrap');
  var hero = document.getElementById('hero-product');
  if (!wrap || !hero) return;
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(e) {
      wrap.classList.toggle('visible', !e.isIntersecting);
    });
  }, { threshold: 0 });
  observer.observe(hero);
})();
</script>
```

---

## Section 3: WHY THIS（为什么选这个）

**设计原则：**
- 4张卡片，解答"买这个而不是别的"的疑虑
- 图标 + 标题 + 一句话说明
- 桌面4列，移动端2列

```html
<section class="why-section">
  <h2>Why Families Pick [产品名] Every Year</h2>
  <div class="why-grid">
    <div class="why-card">
      <div class="why-icon">📦</div>
      <h3>[Benefit 1 标题]</h3>
      <p>[一句话说明]</p>
    </div>
    <div class="why-card">
      <div class="why-icon">⭐</div>
      <h3>[Benefit 2 标题]</h3>
      <p>[一句话说明]</p>
    </div>
    <div class="why-card">
      <div class="why-icon">🚚</div>
      <h3>[Benefit 3 标题]</h3>
      <p>[一句话说明]</p>
    </div>
    <div class="why-card">
      <div class="why-icon">💯</div>
      <h3>[Benefit 4 标题]</h3>
      <p>[一句话说明]</p>
    </div>
  </div>
</section>
```

---

## Section 4: SOCIAL PROOF（精选评价）

**设计原则：**
- 1~2条精选真实好评，带 Verified Purchase 标签
- 引用格式，左边框强调色

```html
<section class="proof-section">
  <div class="proof-inner">
    <div class="proof-quote">
      <div class="proof-stars">★★★★★</div>
      <p>"[用户评价原文 — 真实、有具体细节]</p>
      <div class="proof-author">— Verified Amazon Buyer</div>
    </div>
    <div class="proof-verified">✓ Verified Purchase</div>
  </div>
</section>
```

---

## Section 5: OTHER PICKS（次选产品）

**设计原则：**
- 小卡片，不抢 Hero 产品风头
- 桌面端多列，移动端单列
- 只放产品图/名/价格/评分/CTA，不重复 Benefits

**重要：条件渲染** — 如果没有次选产品（即 `otherProducts.length === 0`），整个 section 应隐藏，不渲染空区域。

```html
<section class="other-section">
  <h2>More [Category] Favorites →</h2>
  <div class="other-grid">
    <!-- 每个次选产品卡片 -->
    <a href="[Amazon链接]" class="other-card" target="_blank" rel="noopener">
      <div class="other-card-img">
        <img src="[产品图URL]" alt="[产品名]" loading="lazy">
      </div>
      <div>
        <span class="other-card-badge">[类别标签]</span>
        <h3>[产品名]</h3>
        <div class="other-card-price">$[价格]</div>
        <div class="other-card-meta">★★★★☆ [评分] · [评论数] reviews</div>
      </div>
      <div class="other-card-cta">See on Amazon →</div>
    </a>
    <!-- 重复更多产品 -->
  </div>
</section>
```

---

## Section 6: FAQ（常见问题）

**设计原则：**
- 4个最常见问题：物流/退换/适合人群/价格
- 点击展开/收起（纯 JS，无依赖）

```html
<section class="faq-section">
  <h2>Quick Answers</h2>
  <div class="faq-list">
    <div class="faq-item" onclick="toggleFaq(this)">
      <div class="faq-q">问题1：物流相关？</div>
      <div class="faq-a"><p>回答内容...</p></div>
    </div>
    <div class="faq-item" onclick="toggleFaq(this)">
      <div class="faq-q">问题2：退换政策？</div>
      <div class="faq-a"><p>回答内容...</p></div>
    </div>
    <div class="faq-item" onclick="toggleFaq(this)">
      <div class="faq-q">问题3：适合人群？</div>
      <div class="faq-a"><p>回答内容...</p></div>
    </div>
    <div class="faq-item" onclick="toggleFaq(this)">
      <div class="faq-q">问题4：价格/折扣？</div>
      <div class="faq-a"><p>回答内容...</p></div>
    </div>
  </div>
</section>

<script>
function toggleFaq(el) { el.classList.toggle('open'); }
</script>
```

---

## Section 7: FINAL CTA（最终转化区）

```html
<section class="final-section">
  <h2>🎯 Ready for [Desired Action]?</h2>
  <p>[价格] · [核心卖点] · [紧迫感]</p>
  <a href="[Amazon链接]" class="final-btn">
    🐰 Shop [产品名] on Amazon →
  </a>
</section>
```

---

## Section 8: TRUST BAR（信任栏）

```html
<div class="trust-bar">
  <div class="trust-item"><span>🚚</span> Prime Delivery</div>
  <div class="trust-item"><span>↩️</span> 30-Day Returns</div>
  <div class="trust-item"><span>🔒</span> Secure Amazon Pay</div>
  <div class="trust-item"><span>💰</span> We may earn a commission</div>
</div>
<div class="disclosure">
  <p>As an Amazon Associate, we earn from qualifying purchases — but we only recommend products we'd buy ourselves.</p>
</div>
```

---

## CSS 变量规范

```css
:root {
  --bg: #FEF9F3;           /* 页面背景（暖色调） */
  --card: #FFFFFF;         /* 卡片背景 */
  --text: #1A1A1A;         /* 主文字 */
  --text-mid: #555;        /* 次要文字 */
  --text-light: #888;      /* 辅助文字 */
  --coral: #E8523A;        /* CTA 主色（珊瑚红） */
  --coral-dark: #C73820;   /* CTA 深色 */
  --sky: #3B9ED8;          /* 辅助强调色 */
  --gold: #F5A623;         /* 星级颜色 */
  --border: #EEE6DD;       /* 边框色 */
  --shadow: 0 2px 16px rgba(0,0,0,0.08);
  --radius: 16px;
}
```

---

## CTA 按钮全局样式

```css
/* 主CTA（珊瑚红） */
.hero-cta-btn, .sticky-cta-btn, .final-btn {
  display: inline-block;
  background: linear-gradient(135deg, var(--coral), var(--coral-dark));
  color: #fff;
  border-radius: 16px;
  font-size: 18px;
  font-weight: 800;
  padding: 16px 32px;
  text-decoration: none;
  box-shadow: 0 6px 20px rgba(232,82,58,0.35);
}

/* Amazon 黄（备选） */
.amazon-btn {
  background: linear-gradient(180deg, #FFD814 0%, #FFBB50 100%);
  border: 1px solid #FCD200;
  color: #0F1111;
  font-weight: 600;
}
```
