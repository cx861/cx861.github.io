# AGENTS.md

## 项目概览

这是一个个人使用、托管在 GitHub Pages 的考研笔记静态站点。

- 技术：HTML、CSS、原生 JavaScript、Python 内容处理脚本
- 部署：`.github/workflows/pages.yml`
- 页面：根目录为入口页，`math/`、`cs/`、`english/`、`politics/` 为学科内容
- 公共资源：`assets/css/style.css`、`assets/css/study-archive.css`、`assets/js/main.js`
- 页面来源：`site/pages.json`、`site/templates/`、`site/content/`
- 当前没有后端、数据库或前端框架

## 常用命令

```powershell
# 本地预览
python -m http.server 8000

# 根据统一模板重建公开 HTML
python tools/site_builder.py build --root . --output .

# 将 Markdown 笔记转换为 HTML 正文片段
python tools/content_converter.py convert --input path/to/note.md --output path/to/note.html

# 检查公开 HTML 是否与来源一致
python tools/site_builder.py check --root .

# 运行测试
python -m unittest discover -s tests -v

# 检查当前站点是否与验收基线一致
python tools/site_audit.py check --root . --baseline tests/baseline/site-baseline.json

# 仅在确认页面或内容变更是预期行为后更新基线
python tools/site_audit.py scan --root . --output tests/baseline/site-baseline.json
```

## 修改约束

- 保持现有公开 HTML 路径稳定，避免破坏 GitHub Pages 链接。
- 不覆盖用户已有的未提交或未跟踪文件。
- 编辑页面正文时修改 `site/content/` 中对应文件；根目录和学科目录中的 HTML 是生成结果。
- 公共导航、移动菜单、页脚和资源引用只在 `site/templates/base.html` 中维护。
- 基础布局与旧页面兼容样式在 `assets/css/style.css` 中维护；视觉主题统一在 `assets/css/study-archive.css` 中维护。
- 新增页面时同步登记到 `site/pages.json`，然后运行构建命令。
- 正式站点网址、站点名和默认页面描述只在 `site/pages.json` 的 `site` 配置中维护。
- 内容处理脚本必须使用仓库相对路径，不得新增本机绝对路径。
- Markdown 转换统一使用 `tools/content_converter.py`；不要为单个学科复制转换脚本。
- 页面结构、标题、锚点或链接发生预期变化时，应先检查差异，再更新基线。
- `output/playwright/baseline/` 中命名后的 PNG 是视觉基线；`.playwright-cli/` 是临时产物。
- `output/playwright/stage4/` 中命名后的 PNG 是阶段 4 的视觉验收结果。
- GitHub Pages 只发布构建并审计后的 `dist/`，不要把工作流的上传路径改回仓库根目录。
- 设计改动必须单独进行；阶段 1 的测试和文档不得改变现有页面表现。
