# 专题落地页 - Section 模板参考

## Section 1: Hero 区域

```html
<section class="hero">
    <div class="container">
        <span class="hero-badge">{theme_badge}</span>
        <h1>{主题名称}</h1>
        <p class="hero-description">{描述}</p>
        <div class="hero-meta">
            <span>{N}款商品精选</span>
            <span>独立评测 · 无广告植入</span>
            <span>最后更新: {日期}</span>
        </div>
    </div>
</section>
```

## Section 2: Quick Picks 快速推荐表格

```html
<section class="quick-picks">
    <div class="container">
        <div class="section-header">
            <h2>⚡ 快速选择</h2>
            <p>不知道选哪款？看看我们的精选推荐</p>
        </div>
        <div class="quick-picks-table">
            <table>
                <thead>
                    <tr>
                        <th>推荐</th>
                        <th>核心亮点</th>
                        <th>适合人群</th>
                        <th>价格</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {每款商品的行}
                </tbody>
            </table>
        </div>
    </div>
</section>
```

## Section 3: Product Cards 商品卡片组

```html
<section class="products" id="products">
    <div class="container">
        <div class="section-header">
            <h2>🏆 商品推荐</h2>
            <p>每款都是同价位的最佳选择</p>
        </div>
        <div class="products-grid">
            {每款商品的卡片}
        </div>
    </div>
</section>
```

## Section 4: Use Case Cards 场景推荐

```html
<section class="use-cases">
    <div class="container">
        <div class="section-header">
            <h2>🎯 场景推荐</h2>
            <p>按需匹配，找到最适合你的那一款</p>
        </div>
        <div class="use-case-grid">
            {每个场景的卡片}
        </div>
    </div>
</section>
```

## Section 5: FAQ 手风琴

```html
<section class="faq">
    <div class="container">
        <div class="section-header">
            <h2>❓ 常见问题</h2>
            <p>选购前的疑问，一文解答</p>
        </div>
        <div class="faq-list">
            <div class="faq-item">
                <div class="faq-question">{问题}</div>
                <div class="faq-answer"><p>{答案}</p></div>
            </div>
        </div>
    </div>
</section>
```

## Section 6: Final CTA 结束CTA

```html
<section class="final-cta">
    <div class="container">
        <h2>找到最适合你的{主题}</h2>
        <p>无论预算是高是低，这份清单都能帮你找到最佳选择。</p>
        <div class="final-cta-buttons">
            <a href="#" class="final-cta-btn">查看我们的首选</a>
            <a href="#products" class="final-cta-btn secondary">查看所有推荐</a>
        </div>
    </div>
</section>
```
