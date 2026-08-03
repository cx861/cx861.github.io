# 考研笔记

个人使用的考研知识库静态网站，托管于 GitHub Pages。项目保持纯静态输出，不依赖后端、数据库或前端框架。

## 本地预览

```powershell
python tools/site_builder.py build --root . --output .
python -m http.server 8000
```

浏览器访问 `http://127.0.0.1:8000/`。

## Markdown 内容转换

新笔记统一通过一个无本机路径依赖的命令转换为 HTML 片段：

```powershell
python tools/content_converter.py convert --input path/to/note.md --output path/to/note.html
```

转换器支持标题锚点、MathJax 行内与块级公式、表格、代码块、引用、有序/无序列表和基础强调语法。输出是正文片段；确认结果后将其放入对应的 `site/content/` 页面源文件，再运行站点构建命令。

## 质量检查

```powershell
python -m unittest discover -s tests -v
python tools/site_builder.py check --root .
python tools/site_audit.py check --root . --baseline tests/baseline/site-baseline.json
```

检查内容包括生成一致性、页面集合、标题、一级标题、锚点、本地链接、公共页面结构和 MathJax 使用情况。

如果页面、标题或锚点是有意修改的，先检查差异，确认没有链接损坏后再更新基线：

```powershell
python tools/site_audit.py scan --root . --output tests/baseline/site-baseline.json
python -m unittest discover -s tests -v
```

## 目录

- `assets/css/style.css`：基础布局与旧页面兼容样式
- `assets/css/study-archive.css`：全站“个人考研知识档案”视觉主题
- `assets/js/main.js`：全站交互行为
- `math/`、`cs/`、`english/`、`politics/`：学科页面
- `site/pages.json`：46 个公开页面的路径、标题和导航状态
- `site/templates/base.html`：全站唯一的公共页面外壳
- `site/content/`：页面专属正文，是内容修改的来源
- `site/head/`、`site/tail/`：少数页面保留的专属样式或脚本
- `scripts/`：个人数据导入辅助脚本，不参与站点构建
- `tools/content_converter.py`：Markdown 笔记到安全 HTML 片段的统一转换入口
- `tools/site_builder.py`：静态页面构建与生成一致性检查
- `tools/site_audit.py`：静态站点验收命令
- `robots.txt`、`sitemap.xml`：由构建器根据 `site/pages.json` 自动生成
- `tests/baseline/site-baseline.json`：页面、链接和结构基线
- `output/playwright/baseline/`：阶段 1 的原始视觉基线
- `output/playwright/stage4/`：阶段 4 的桌面端、移动端和深色模式验收截图

## 页面修改流程

不要直接长期修改生成后的公开 HTML。正确流程是：

1. 修改 `site/content/` 中对应正文，或先用统一转换器生成 Markdown 的 HTML 片段。
2. 执行 `python tools/site_builder.py build --root . --output .`。
3. 执行测试、生成一致性检查和站点审计。

当前 GitHub Pages 托管构建后的纯静态文件，不需要 Node.js 或服务器运行环境。

## GitHub Pages 发布

`site/pages.json` 顶部的 `site` 配置统一维护站点名称、正式网址和默认页面描述。构建器会据此生成每页 description、canonical、Open Graph 元数据，以及 `robots.txt` 和 `sitemap.xml`。

发布工作流会先运行测试，再生成并审计只包含公开页面与资源的 `dist/`：

```powershell
python -m unittest discover -s tests -v
python tools/site_builder.py build --root . --output dist
python tools/site_audit.py check --root dist --baseline tests/baseline/site-baseline.json
```

只有测试、构建和审计全部通过后，GitHub Pages 才会部署 `dist/`；仓库中的脚本、页面源片段和测试不会进入线上站点。
