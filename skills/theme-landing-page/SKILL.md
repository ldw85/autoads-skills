---
name: theme-landing-page
description: Theme-based multi-product landing page generator. Use for "themed gift guides", "product comparison shopping guides", "topic-specific recommendations". Generates English or Chinese landing pages with multiple products, featuring pain-point oriented copy, user reviews, and benefit-focused messaging.
---

# Theme Landing Page Skill - 专题落地页技能

> Not just a product list — a decision-making guide that sells through storytelling

## Core Philosophy

### What Makes This Different from Single-Product Pages?

| Aspect | Single-Product Page | Theme Landing Page |
|--------|---------------------|-------------------|
| Goal | Push one specific product | Help users choose from multiple options |
| Copy | Feature-focused | **Pain-point oriented** + Benefit-driven |
| Structure | Deep-dive on one item | Quick picks + comparison +场景推荐 |
| User Journey | "Buy this one" | "Which one is right for ME?" |

---

## Content Requirements (Critical)

### 1. Language: English by Default

**ALL landing pages should be in English** unless explicitly requested otherwise.
- Headlines, descriptions, CTAs all in English
- Product names stay in original language
- Meta descriptions also in English

### 2. Pain-Point Oriented Copy (核心要求)

**Don't write features. Write solutions.**

❌ **Wrong (Feature-focused):**
> "36 RGB LEDs, 16 million colors, auto light-up"

✅ **Right (Pain-point + Benefit):**
> **The Problem:** Kids are glued to screens after dark. They need a reason to go outside.
> **The Solution:** This glowing ring gets them active and creates magical nighttime memories.

**Pain Point Formula:**
```
[Situation] → [Negative outcome] → [Your product solves it]
```

### 3. Benefits Over Features

| Features (功能) | Benefits (益处) |
|----------------|----------------|
| 36 RGB LEDs | Creates mesmerizing light shows that kids LOVE |
| 30-hour battery | All-night play without recharging |
| Waterproof | Pool parties, beach trips, any weather |
| Award winner | Proven quality you can trust |

### 4. Include User Reviews (Required)

Every product card MUST include a real user review snippet:

```html
<div class="product-review">
    <p class="review-quote">This is the best purchase I've made. My kids can't put it down!</p>
    <p class="review-author">— Verified Amazon Buyer</p>
</div>
```

### 5. Price Display

Always show current price prominently:
- Large, bold price display
- Original price with strikethrough if on sale
- Format: "$XX.XX" (USD)

---

## Page Structure (8 Sections)

### Section 1: Hero
```
[Theme Badge: 🐰 Easter 2026]
[Main Headline: Best Easter Gifts on Amazon]
[Sub-headline: Curated picks for kids who love toys, sweets & surprises]
```

### Section 2: Quick Picks Table
| Our Pick | Key Benefit | Perfect For | Price | CTA |
|----------|-------------|-------------|-------|-----|
| Best for Night Fun | Gets kids outside after dark | Outdoor play | $39.27 | Check Price |

### Section 3: Pain Point Section (per product)
```
THE PROBLEM:
[Kids are glued to screens. They need...]

THE SOLUTION:
[This product solves it because...]
```

### Section 4: Product Cards (with reviews)
- Product image (real URL)
- Badge: "Best for X"
- Tagline (benefit-focused)
- Rating + review count
- **Pain point box**
- **Benefits list (not features)**
- **User review quote**
- Tags
- Price + CTA

### Section 5: Use Case /场景推荐
```
🎯 For Outdoor Fun → Product A
🌙 For Night Play → Product B  
🎁 For Gifts → Product C
```

### Section 6: FAQ (Pain-point questions)
- "Why buy now?"
- "Why this over alternatives?"
- "Is it worth the price?"

### Section 7: Final CTA
```
[Headline: Ready to Find Your Perfect Gift?]
[Buttons: Shop #1 Pick | View All]
```

---

## Product JSON Schema

```json
{
  "name": "Product Name",
  "tagline": "Benefit-focused tagline",
  "position": "Best for X",
  "price": "$XX.XX",
  "originalPrice": "$XX.XX",
  "affiliateLink": "https://...",
  "image": "https://...",
  "rating": 4.7,
  "reviewCount": 3200,
  "painPoint": "The problem this solves...",
  "benefits": [
    "Benefit 1",
    "Benefit 2",
    "Benefit 3"
  ],
  "userReview": {
    "text": "Review quote...",
    "author": "Verified Buyer"
  },
  "useCases": ["Gift", "Outdoor", "Kids"]
}
```

---

## Usage

### Generate Landing Page
```bash
cd /root/.openclaw/workspace/skills/theme-landing-page/scripts
python3 generate_theme_landing.py \
  --theme "Best Easter Gifts 2026" \
  --description "Curated Easter gift recommendations..." \
  --products /path/to/products.json \
  --badge "🐰 Easter 2026" \
  --output /path/to/output.html
```

### Products JSON Example
```json
[
  {
    "name": "TOSY Flying Ring",
    "tagline": "The glowing ring that gets kids outside after dark",
    "position": "Best for Nighttime Fun",
    "price": "$39.27",
    "originalPrice": "$49.99",
    "affiliateLink": "https://amzn.to/xxx",
    "image": "https://m.media-amazon.com/...",
    "rating": 4.7,
    "reviewCount": 3200,
    "painPoint": "Kids are glued to screens after school. They need a reason to go outside — especially when the sun goes down.",
    "benefits": [
      "Gets kids OFF screens and OUTSIDE at night",
      "Light-up design creates magical memories",
      "Durable enough to survive hundreds of crashes"
    ],
    "userReview": {
      "text": "My screen-addicted 10-year-old son loves going outside at night to play with it. Worth every cent!",
      "author": "Verified Amazon Buyer"
    },
    "useCases": ["Easter Gifts", "Outdoor Play", "Family Fun"]
  }
]
```

---

## Design System

- **Theme:** Dark mode (#0a0a0b background)
- **Accent:** Amazon Orange (#FF9900) for CTAs
- **Secondary Accent:** Teal (#00C4B4) for badges/highlights
- **Typography:** System fonts, clean hierarchy
- **Responsive:** Mobile-first, 1-2 column grid

---

## Output

Generates a single HTML file:
- Inline CSS (no external dependencies)
- Optimized for Amazon affiliate conversion
- Real product images from provided URLs
- Working CTA buttons linking to affiliate URLs

---

## Example Prompt

```
Create a theme landing page for "Best Father's Day Gifts 2026" with:
- 4 products from $20-$100
- Include real user review snippets
- Pain-point oriented copy
- Benefits not features
- English content
```

---

*Turn browsing into buying — through storytelling, not selling.*
