# 静态站点来源

该目录是 46 个公开 HTML 页面的唯一生成来源。

## Module interface

```powershell
python tools/site_builder.py build --root . --output .
python tools/site_builder.py check --root .
```

`build` 隐藏页面层级、相对资源路径、导航状态、公共外壳和输出目录创建等实现细节。`check` 从相同来源在临时目录重建，并检测公开 HTML 是否被手工修改。

Markdown 笔记先通过统一转换接口生成安全的正文片段：

```powershell
python tools/content_converter.py convert --input path/to/note.md --output path/to/note.html
```

转换命令只负责 Markdown 语义，不生成导航、页脚或完整文档外壳；这些职责仍由 `site_builder.py` 统一处理。

## 目录职责

- `pages.json`：页面清单和少量页面级配置
- `templates/base.html`：导航、移动菜单、页脚、资源引用等公共外壳
- `content/`：页面专属可见内容
- `head/`：页面专属 `<head>` 内容，例如 MathJax 或遗留内联样式
- `tail/`：页面末尾保留的遗留内联脚本

后续阶段会逐步把 `head/` 和 `tail/` 中可复用的遗留内容继续收敛，但阶段 2 为保证视觉零变化暂时原样保留。
