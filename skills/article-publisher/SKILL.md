---
name: article-publisher
description: AI驱动的自动化文章发布系统，用于 my-blog (Astro静态博客) 的全流程管理：写文章（含占位符）、构建验证、GitHub推送、文章列表模块动态维护。

使用场景：
- AI写文章后自动构建并推送GitHub
- 替换文章中的 affiliate 链接占位符
- 自动将文章添加到指定的列表模块（BlogHighlightedPosts、Electronics Rankings、AI Tools Rankings等）
- 更新已发布文章的 affiliate 链接

触发条件：用户说"写文章发布"、"发布文章"、"更新文章链接"、"替换 affiliate" 或类似表达
---

# Article Publisher Skill

自动化文章发布流程，涵盖 AI 写文章 → 构建验证 → GitHub 推送 → 列表维护全链路。

## 核心文件路径

- 博客文章目录：`src/data/post/`
- 博客首页：`src/pages/index.astro`
- 产品数据库：`scripts/affiliate-products.json`
- 占位符说明：`references/placeholder-syntax.md`

## 工作流总览

```
用户需求
  ↓
Step 1: 写文章（带占位符）或替换链接
  ↓
Step 2: 更新文章列表模块
  ↓
Step 3: 本地构建 (npm run build)
  ↓
Step 4: GitHub 推送
  ↓
完成
```

---

## Step 1: 写文章或替换链接

### 占位符语法

**产品占位符**（用于 AI 写文章时标记产品位置）：
```
[AFFILIATE: 产品名称]
```
运行时自动替换为 HTML 链接格式。

**图片占位符**（用于 AI 写文章时标记产品图片位置）：
```
[IMAGE: 产品名称]
```
运行时自动替换为 HTML 图片格式。

### 执行替换

两种情况：

**情况A - AI写文章（新产品）**：
从产品数据库 `scripts/affiliate-products.json` 查找产品信息，替换占位符。

**情况B - 替换链接（用户指定新链接）**：
接收用户提供的「产品名→新链接」映射，直接替换 `[AFFILIATE: xxx]` 中的链接。

### 产品数据库格式

```json
{
  "Audio-Technica ATH-M50x": {
    "link": "https://amzn.to/43n1M4g",
    "image": "https://m.media-amazon.com/images/I/B00HVLUR86._SX679_.jpg"
  },
  "Sennheiser HD 560S": {
    "link": "https://amzn.to/3PP8Nb3",
    "image": "https://m.media-amazon.com/images/I/B08J9MVB6W._SX679_.jpg"
  }
}
```

---

## Step 2: 更新文章列表模块

### 支持的列表类型

| 列表ID | 组件/位置 | 更新方式 |
|--------|-----------|----------|
| `index-featured` | `BlogHighlightedPosts` (index.astro) | 添加 postId |
| `index-electronics` | "Electronics Rankings" (index.astro) | 动态写入 |
| `index-ai` | "AI Tools Rankings" (index.astro) | 动态写入 |
| `latest` | `BlogLatestPosts` | 自动（按时间） |

### BlogHighlightedPosts 更新逻辑

该组件通过 `postIds` 数组指定文章：

```astro
<BlogHighlightedPosts postIds={["post-id-1", "post-id-2"]} />
```

**规则**：
1. 文章 slug（即文件名，不含 `.md`）作为 postId
2. 新文章 ID 添加到数组**最前面**（最新优先）
3. 建议最多保留 6 个 ID，超出时移除最旧的
4. 更新时保持 JSON 数组格式正确

### Rankings 列表更新逻辑

硬编码的手动列表，位于 `index.astro` 的 `<ul>` 中：

```html
<ul class="space-y-3">
  <li class="flex items-center gap-2">
    <span class="text-blue-600 font-bold">1</span>
    <span>文章标题</span>
  </li>
</ul>
```

**规则**：
1. 从对应列表末尾追加新条目
2. 每类 rankings 最多保留 5 条
3. 添加时自动编号（1-N）

### 列表选择策略

- `audio` 相关 → `index-electronics`
- `ai`、`saas` 相关 → `index-ai`
- `blog-featured` 或明确指定 → `index-featured`
- `latest` 或无指定 → 自动添加到 `BlogLatestPosts`（无需手动操作）

---

## Step 3: 构建验证

```bash
cd /root/.openclaw/workspace/my-blog && npm run build
```

- **成功**（Exit code 0）→ 继续 Step 4
- **失败** → 报告构建错误，**不推送 GitHub**

---

## Step 4: GitHub 推送

```bash
cd /root/.openclaw/workspace/my-blog
git add -A
git commit -m "发布: <文章标题> (<日期>)"
git push origin main
```

**注意**：如果 token 已失效，先更新 remote 再推送：
```bash
git remote set-url origin https://ghp_<新token>@github.com/ldw85/my-blog.git
```

---

## 详细参考

- 占位符语法详情：查看 `references/placeholder-syntax.md`
- 文章列表管理详情：查看 `references/article-lists.md`
- 产品数据库说明：查看 `references/affiliate-products.md`
- 发布脚本：执行 `scripts/publish_article.py --help`