#!/usr/bin/env python3
"""
Article Publisher - 自动化文章发布脚本

Usage:
    python3 publish_article.py --article <slug> [--replace-links <json>] [--lists <list_ids>]
    python3 publish_article.py --help

Examples:
    # 发布文章（替换占位符，更新列表）
    python3 publish_article.py --article wired-headphones-audiophile-comeback-2024 --lists index-electronics,index-featured

    # 替换 affiliate 链接
    python3 publish_article.py --article my-article --replace-links '{"Audio-Technica ATH-M50x": "https://new-link.com"}'

    # 查看帮助
    python3 publish_article.py --help
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BLOG_DIR = Path("/root/.openclaw/workspace/my-blog")
POST_DIR = BLOG_DIR / "src/data/post"
INDEX_FILE = BLOG_DIR / "src/pages/index.astro"
PRODUCTS_FILE = Path(__file__).parent / "affiliate-products.json"


def load_products():
    """加载产品数据库"""
    if not PRODUCTS_FILE.exists():
        return {}
    with open(PRODUCTS_FILE) as f:
        return json.load(f)


def replace_placeholders_in_file(filepath: str, products: dict, custom_links: dict = None):
    """
    替换文章中的占位符
    - [AFFILIATE: 产品名] → <a href="...">产品名</a>
    - [IMAGE: 产品名] → <a href="..."><img src="..."/></a>
    """
    with open(filepath) as f:
        content = f.read()

    # 替换 [AFFILIATE: 产品名]
    def replace_affiliate(match):
        product_name = match.group(1).strip()
        for key, data in products.items():
            if key.lower() == product_name.lower():
                link = custom_links.get(product_name, data["link"]) if custom_links else data["link"]
                return f'<a href="{link}">{product_name}</a>'
        print(f"⚠️  未找到产品: {product_name}", file=sys.stderr)
        return match.group(0)  # 保留原占位符

    content = re.sub(r'\[AFFILIATE:\s*([^\]]+)\]', replace_affiliate, content)

    # 替换 [IMAGE: 产品名]
    def replace_image(match):
        product_name = match.group(1).strip()
        for key, data in products.items():
            if key.lower() == product_name.lower():
                link = custom_links.get(product_name, data["link"]) if custom_links else data["link"]
                return f'<a href="{link}"><img src="{data["image"]}" alt="{product_name}" loading="lazy" style="max-width:300px"></a>'
        print(f"⚠️  未找到产品图片: {product_name}", file=sys.stderr)
        return match.group(0)

    content = re.sub(r'\[IMAGE:\s*([^\]]+)\]', replace_image, content)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"✅ 占位符替换完成: {filepath}")


def update_blog_highlighted_posts(article_slug: str):
    """更新 BlogHighlightedPosts 组件的 postIds"""
    with open(INDEX_FILE) as f:
        content = f.read()

    # 查找 BlogHighlightedPosts 组件
    pattern = r'(<BlogHighlightedPosts\s+postIds=\{\[)([^\]]+)(\]\s*/>)'
    match = re.search(pattern, content)

    if not match:
        print("⚠️  未找到 BlogHighlightedPosts 组件")
        return

    existing_ids = match.group(2).strip()
    # 解析现有 IDs
    ids = [x.strip().strip('"').strip("'") for x in existing_ids.split(",") if x.strip()] if existing_ids else []

    # 添加新文章 ID（去重，添加到最前面）
    if article_slug not in ids:
        ids.insert(0, article_slug)
    else:
        ids.remove(article_slug)
        ids.insert(0, article_slug)

    # 限制最多 6 个
    if len(ids) > 6:
        ids = ids[:6]

    new_ids_str = '["' + '", "'.join(ids) + '"]'
    new_component = f'<BlogHighlightedPosts postIds={{[{new_ids_str}]}} />'

    content = content[:match.start()] + new_component + content[match.end():]

    with open(INDEX_FILE, "w") as f:
        f.write(content)

    print(f"✅ BlogHighlightedPosts 已更新: {new_ids_str}")


def update_rankings_list(rankings_type: str, article_title: str):
    """
    更新 Rankings 列表
    rankings_type: 'electronics' 或 'ai'
    """
    with open(INDEX_FILE) as f:
        content = f.read()

    # 确定颜色类名
    color_class = "text-blue-600" if rankings_type == "electronics" else "text-purple-600"
    section_name = "Electronics Rankings" if rankings_type == "electronics" else "AI Tools Rankings"

    # 找到 section
    section_pattern = rf'(<a[^>]*href="/blog"[^>]*>\s*<div[^>]*>.*?<h3[^>]*>{section_name}</h3>.*?<ul class="space-y-3">)(.*?)(</ul>)'
    section_match = re.search(section_pattern, content, re.DOTALL)

    if not section_match:
        print(f"⚠️  未找到 {section_name} 列表")
        return

    ul_content = section_match.group(2)

    # 统计现有条目数
    existing_items = re.findall(r'<li', ul_content)
    count = len(existing_items)

    if count >= 5:
        # 移除最旧的一条（第一个 <li>）
        first_li_pattern = r'<li class="flex items-center gap-2">\s*<span[^>]*>[^<]*</span>\s*<span>[^<]*</span>\s*</li>\s*'
        ul_content = re.sub(first_li_pattern, '', ul_content, count=1)
        count -= 1

    # 添加新条目
    new_number = count + 1
    new_item = f'''
            <li class="flex items-center gap-2">
              <span class="{color_class} font-bold">{new_number}</span>
              <span>{article_title}</span>
            </li>'''

    new_ul = section_match.group(1) + ul_content + new_item + section_match.group(3)

    content = content[:section_match.start()] + new_ul + content[section_match.end():]

    with open(INDEX_FILE, "w") as f:
        f.write(content)

    print(f"✅ {section_name} 已更新，添加: {article_title}")


def run_build():
    """运行 npm build"""
    print("🔨 开始构建...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=BLOG_DIR,
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0


def push_to_github(commit_message: str):
    """推送到 GitHub"""
    print("📤 推送到 GitHub...")

    # 设置 remote（如果需要）
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=BLOG_DIR,
        capture_output=True,
        text=True
    )

    remote_url = result.stdout.strip()

    # 检查是否使用了旧的（无效的）token
    if "ghp_" not in remote_url or remote_url.count("@") > 0:
        print("⚠️  GitHub remote URL 可能需要更新")
        print(f"   当前: {remote_url}")

    commands = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", commit_message],
        ["git", "push", "origin", "main"]
    ]

    for cmd in commands:
        result = subprocess.run(cmd, cwd=BLOG_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ 命令失败: {' '.join(cmd)}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            return False
        if result.stdout:
            print(result.stdout.strip())

    print("✅ 推送完成!")
    return True


def get_article_title(slug: str) -> str:
    """从文章文件获取标题"""
    filepath = POST_DIR / f"{slug}.md"
    if not filepath.exists():
        return slug

    with open(filepath) as f:
        content = f.read()

    # 尝试从 frontmatter 获取 title
    match = re.search(r'^title:\s*["\']?([^"\n]+)["\']?', content, re.MULTILINE)
    if match:
        return match.group(1)

    return slug


def main():
    parser = argparse.ArgumentParser(description="Article Publisher - 自动化文章发布")
    parser.add_argument("--article", required=True, help="文章 slug（不含 .md）")
    parser.add_argument("--replace-links", help='JSON 格式的链接映射 {"产品名": "新链接"}')
    parser.add_argument("--lists", default="", help="要更新的列表，逗号分隔，如: index-electronics,index-featured")
    parser.add_argument("--no-push", action="store_true", help="只替换占位符，不推送")
    parser.add_argument("--commit-message", help="自定义 commit 消息")

    args = parser.parse_args()

    article_slug = args.article
    filepath = POST_DIR / f"{article_slug}.md"

    if not filepath.exists():
        print(f"❌ 文章文件不存在: {filepath}", file=sys.stderr)
        sys.exit(1)

    # 获取文章标题
    article_title = get_article_title(article_slug)

    # 加载产品数据
    products = load_products()

    # 解析自定义链接
    custom_links = None
    if args.replace_links:
        custom_links = json.loads(args.replace_links)

    # Step 1: 替换占位符
    print(f"📝 处理文章: {article_slug}")
    replace_placeholders_in_file(str(filepath), products, custom_links)

    # Step 2: 更新文章列表
    if args.lists:
        list_ids = [l.strip() for l in args.lists.split(",") if l.strip()]

        for list_id in list_ids:
            if list_id == "index-featured":
                update_blog_highlighted_posts(article_slug)
            elif list_id == "index-electronics":
                update_rankings_list("electronics", article_title)
            elif list_id == "index-ai":
                update_rankings_list("ai", article_title)
            else:
                print(f"⚠️  未知列表: {list_id}")

    # Step 3: 构建
    if not run_build():
        print("❌ 构建失败，终止推送", file=sys.stderr)
        sys.exit(1)

    # Step 4: 推送
    if args.no_push:
        print("⏭️  跳过推送（--no-push）")
        return

    commit_msg = args.commit_message or f"发布: {article_title}"
    push_to_github(commit_msg)


if __name__ == "__main__":
    main()