#!/usr/bin/env python3
"""
Theme Landing Page Generator - 专题多商品落地页生成器
"""

import json
import argparse
from datetime import datetime


def generate_landing_page(theme, description, products, theme_badge="2026年度精选", output_file="theme_landing.html"):
    """生成专题落地页"""
    
    update_date = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().year
    
    # Quick Picks
    quick_picks_rows = ""
    for p in products:
        badge = f'<span class="pick-badge">{p.get("position", "推荐")}</span>'
        highlight = p.get("tagline", "")
        audience = ", ".join(p.get("useCases", [])[:2]) if p.get("useCases") else "通用"
        price = p.get("price", "")
        link = p.get("affiliateLink", "#")
        quick_picks_rows += f'''
                        <tr>
                            <td>{badge}</td>
                            <td class="pick-highlight">{highlight}</td>
                            <td>{audience}</td>
                            <td class="pick-price">{price}</td>
                            <td><a href="{link}" class="pick-cta" target="_blank" rel="noopener">查看详情</a></td>
                        </tr>
        '''
    
    # Product Cards
    product_cards = ""
    for i, p in enumerate(products):
        badge_class = "" if i % 2 == 0 else "badge-alt"
        badge = p.get("position", "推荐")
        rating = p.get("rating", 0)
        full_stars = "★" * int(rating)
        empty_stars = "☆" * (5 - int(rating))
        review_count = p.get("reviewCount", 0)
        review_text = f"{review_count/1000:.1f}K" if review_count >= 1000 else str(review_count)
        highlights = p.get("highlights", [])
        highlight_items = "".join([f"<li>{h.strip()}</li>" for h in highlights[:3]])
        use_cases = p.get("useCases", [])
        tags = "".join([f'<span class="product-tag">#{tag.strip()}</span>' for tag in use_cases[:3]])
        price = p.get("price", "")
        original_price = p.get("originalPrice", "")
        original_html = f'<span class="product-price-original">{original_price}</span>' if original_price else ""
        image_url = p.get("image", "")
        image_html = f'<img src="{image_url}" alt="{p.get("name", "")}" loading="lazy">' if image_url else '<div style="color: var(--text-muted);">📷 产品图片</div>'
        
        product_cards += f'''
                <div class="product-card">
                    <div class="product-image">
                        <span class="product-badge {badge_class}">{badge}</span>
                        {image_html}
                    </div>
                    <div class="product-content">
                        <h3 class="product-name">{p.get("name", "")}</h3>
                        <p class="product-tagline">{p.get("tagline", "")}</p>
                        <div class="product-rating">
                            <span class="stars">{full_stars}{empty_stars}</span>
                            <span class="rating-text">{rating} ({review_text}条评价)</span>
                        </div>
                        <ul class="product-highlights">
                            {highlight_items}
                        </ul>
                        <div class="product-tags">
                            {tags}
                        </div>
                        <div class="product-price-row">
                            <div>
                                <span class="product-price">{price}</span>
                                {original_html}
                            </div>
                            <a href="{p.get("affiliateLink", "#")}" class="product-cta" target="_blank" rel="noopener">查看详情</a>
                        </div>
                    </div>
                </div>
        '''
    
    # Use Case Cards
    use_cases_seen = {}
    for p in products:
        for uc in p.get("useCases", []):
            if uc not in use_cases_seen:
                use_cases_seen[uc] = p
    
    icons = {"通勤": "🚇", "办公": "💼", "运动": "🏃", "游戏": "🎮", "音乐": "🎵", "学习": "📚", "旅行": "✈️", "编程": "💻"}
    use_case_cards = ""
    for uc, product in list(use_cases_seen.items())[:4]:
        icon = icons.get(uc, "📦")
        reason = (product.get("highlights", ["优质选择"])[0] if product.get("highlights") else "综合表现优秀")
        use_case_cards += f'''
                <div class="use-case-card">
                    <div class="use-case-icon">{icon}</div>
                    <h3>适合{uc}</h3>
                    <p>基于实际使用场景和用户反馈推荐</p>
                    <div class="use-case-recommendation">
                        <strong>{product.get("name", "")}</strong>
                        <p class="use-case-reason">推荐理由: {reason}</p>
                    </div>
                </div>
        '''
    
    # FAQ
    faq_templates = _get_faq_templates(theme)
    faq_items = ""
    for q, a in faq_templates:
        faq_items += f'''
                <div class="faq-item">
                    <div class="faq-question">{q}</div>
                    <div class="faq-answer"><p>{a}</p></div>
                </div>
        '''
    
    # Final CTA
    top_product = products[0] if products else None
    final_cta_buttons = ""
    if top_product:
        final_cta_buttons = f'''
                <a href="{top_product.get("affiliateLink", "#")}" class="final-cta-btn" target="_blank" rel="noopener">查看我们的首选</a>
                <a href="#products" class="final-cta-btn secondary">查看所有推荐</a>
        '''
    
    # Read template and replace placeholders
    with open(__file__.replace("generate_theme_landing.py", "template.html"), "r", encoding="utf-8") as f:
        html = f.read()
    
    # Replace placeholders
    replacements = {
        "{theme_badge}": theme_badge,
        "{headline}": theme,
        "{description}": description,
        "{product_count}": str(len(products)),
        "{update_date}": update_date,
        "{quick_picks_rows}": quick_picks_rows,
        "{product_cards}": product_cards,
        "{use_case_cards}": use_case_cards,
        "{faq_items}": faq_items,
        "{final_cta_title}": f"找到最适合你的{theme}",
        "{final_cta_description}": f"无论预算是高是低，这份清单都能帮你找到最佳选择。我们精选了{len(products)}款商品，总有一款适合你。",
        "{final_cta_buttons}": final_cta_buttons,
        "{current_year}": str(current_year),
    }
    
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 落地页已生成: {output_file}")
    return output_file


def _get_faq_templates(theme):
    theme_lower = theme.lower()
    if "耳机" in theme or "headphone" in theme_lower:
        return [
            ("降噪耳机对听力有伤害吗？", "正确使用下不会。主动降噪反而可以降低音量保护听力。"),
            ("头戴式vs入耳式，哪个更适合我？", "头戴式：降噪效果好，音质佳，适合长时间使用。入耳式：轻便易携带，适合运动通勤。"),
        ]
    else:
        return [
            ("这个推荐是怎么选的？", "我们基于实际评测、用户反馈和性价比综合考量。"),
            ("价格会波动吗？", "显示的价格为参考价，实际价格以购买页面为准。"),
        ]


if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(description="生成专题落地页")
    parser.add_argument("--theme", type=str, help="主题名称")
    parser.add_argument("--description", type=str, default="", help="主题描述")
    parser.add_argument("--products", type=str, help="商品JSON文件路径")
    parser.add_argument("--output", type=str, default="theme_landing.html", help="输出文件")
    parser.add_argument("--badge", type=str, default="2026年度精选", help="主题徽章")
    
    args = parser.parse_args()
    
    if args.products:
        with open(args.products, 'r', encoding='utf-8') as f:
            products = json.load(f)
        generate_landing_page(args.theme or "商品推荐", args.description, products, args.badge, args.output)
    else:
        parser.print_help()
