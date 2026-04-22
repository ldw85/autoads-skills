# Google Ads Conversion Tracker Skill

## 用途
为Astro静态网站添加Google Ads转化追踪代码，支持：
- 全局Base Tag安装（Layout.astro）
- 页面级转化追踪脚本
- 兼容Astro View Transitions

## 输入参数
用户需要提供：
- `GA_MEASUREMENT_ID` - Google Ads Measurement ID (格式: AW-XXXXXXXX)
- `CONVERSION_ID` - Conversion ID (格式: AW-XXXXXXXX/YYYYYY)
- `PAGE_TYPE` - 页面类型:
  - `astro-layout` - Astro页面（需要修改Layout + 页面文件）
  - `static-html` - 独立静态HTML页面
- `BUTTON_SELECTOR` - 按钮CSS选择器 (默认: `.amazon-btn`)
- `PAGE_PATH` - 页面路径 (如: `/product/macbook-neo` 或 `public/landing-capcut.html`)

## 工作流程

### 1. 全局Base Tag (仅需执行一次)
在 `src/layouts/Layout.astro` 的 `<head>` 中添加:
```html
<!-- Google tag (gtag.js) -->
<script is:inline src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script is:inline>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>
```

### 2. Astro页面转化追踪 (src/pages/xxx.astro)
在页面 `</Layout>` 前添加:
```astro
<script>
  function handleConversion(url: string) {
    // @ts-ignore
    if (typeof gtag !== 'undefined') {
      // @ts-ignore
      gtag('event', 'conversion', {
        'send_to': '{CONVERSION_ID}',
        'value': 1.0,
        'currency': 'CNY',
        'event_callback': function () {
          console.log('Conversion tracked successfully');
        }
      });
    }
  }

  function setupButtons() {
    const buttons = document.querySelectorAll('{BUTTON_SELECTOR}');
    buttons.forEach(btn => {
      const newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);
      newBtn.addEventListener('click', function(e) {
        handleConversion(this.href);
      });
    });
  }

  setupButtons();
  document.addEventListener('astro:page-load', setupButtons);
</script>
```

### 3. 静态HTML页面 (public/xxx.html)
在 `<head>` 添加Base Tag，在 `</body>` 前添加:
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>

<!-- Conversion Tracking (before </body>) -->
<script>
(function() {
  function handleConversion(url) {
    if (typeof gtag !== 'undefined') {
      gtag('event', 'conversion', {
        'send_to': '{CONVERSION_ID}',
        'value': 1.0,
        'currency': 'CNY',
        'event_callback': function() {
          console.log('Conversion tracked');
        }
      });
    }
  }

  function setupButtons() {
    var buttons = document.querySelectorAll('{BUTTON_SELECTOR}');
    buttons.forEach(function(btn) {
      var newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);
      newBtn.addEventListener('click', function(e) {
        handleConversion(this.href);
      });
    });
  }

  setupButtons();
})();
</script>
```

## 优势
1. **is:inline** - 确保gtag全局可用，不被Astro模块化
2. **event_callback** - Google标准做法，确保数据发送成功
3. **astro:page-load** - 兼容View Transitions
4. **cloneNode** - 避免重复绑定事件

## 注意事项
- 按钮需要有对应的CSS类名或选择器
- 静态HTML页面需要手动构建部署（不在Astro构建系统中）
- 默认货币为CNY，可根据需要修改
