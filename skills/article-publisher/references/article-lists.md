# 文章列表模块管理

## 概览

my-blog 首页有多个文章列表位置，需要在发布文章时动态维护。

## 列表位置详解

### 1. BlogHighlightedPosts (`index-featured`)

**组件路径**：`src/components/widgets/BlogHighlightedPosts.astro`

**用法**：
```astro
<BlogHighlightedPosts 
  title="Featured Posts"
  postIds={["wired-headphones-audiophile-comeback-2024", "portable-cassette-players-revival-2024"]}
 />
```

**规则**：
- `postIds` 是文章 slug 的数组（即文件名，不含 `.md` 扩展名）
- 新文章 slug 添加到数组**最前面**
- 建议最多保留 6 个 slug
- 超出时从末尾移除最旧的

**在 index.astro 中查找**：
搜索 `BlogHighlightedPosts` 找到插入位置。

### 2. Electronics Rankings (`index-electronics`)

**位置**：`src/pages/index.astro` 内 "Electronics Rankings" section

**结构**：
```html
<section class="py-16 not-prose">
  <!-- Electronics Rankings -->
  <a href="/blog" class="block p-6 rounded-xl ...">
    <ul class="space-y-3">
      <li class="flex items-center gap-2">
        <span class="text-blue-600 font-bold">1</span>
        <span>文章标题</span>
      </li>
      <!-- 更多条目 -->
    </ul>
  </a>
</section>
```

**规则**：
- 每条为 `<li>`，包含序号（`<span class="text-blue-600 font-bold">N</span>`）和标题
- 新条目从底部添加（编号随之变化）
- 最多保留 5 条
- 序号自动重编（1-N）

**匹配关键词**：`Electronics`、`Headphones`、`Keyboard`、`Smart Home`、`Phone`

### 3. AI Tools Rankings (`index-ai`)

**位置**：`src/pages/index.astro` 内 "AI Tools Rankings" section

**结构**：同 Electronics Rankings，样式为 `text-purple-600`

**匹配关键词**：`AI`、`ChatGPT`、`Claude`、`SaaS`、`Productivity`

### 4. BlogLatestPosts (自动)

**组件**：`src/components/widgets/BlogLatestPosts.astro`

**规则**：
- 按时间顺序自动排序，**无需手动维护**
- 文章 frontmatter 的 `pubDate` 决定顺序
- 在 index.astro 中的 `<BlogLatestPosts count={6} />` 控制显示数量

---

## 更新流程

1. 确定文章主题和分类
2. 根据分类决定目标列表：
   - `audio`、`electronics`、`peripherals` → `index-electronics`
   - `ai-tools`、`saas` → `index-ai`
   - `blog-featured` 或用户指定 → `index-featured`
3. 读取 `index.astro` 内容
4. 精确定位目标列表的 `<ul>` 位置
5. 插入新条目（带正确序号）
6. 如果超出上限，移除最旧条目

---

## 注意事项

- 修改 `index.astro` 时保持 HTML 结构完整
- 序号使用 `text-blue-600`（Electronics）或 `text-purple-600`（AI）
- 不要修改其他不相关的列表