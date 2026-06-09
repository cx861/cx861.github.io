#!/usr/bin/env python3
"""将 01-马原常见题型.md 转换为 HTML 页面"""

import re
import os

INPUT = r"C:\Users\陈鑫\Desktop\知识库\政治\题型\01-马原常见题型.md"
OUTPUT = r"E:\coding\demo\docs\politics\marxism-exam-types.html"

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

with open(INPUT, "r", encoding="utf-8") as f:
    lines = f.readlines()

# ===== 预处理：保护 table 中的 | 不被后续分割 =====
def preprocess_table_row(line):
    """对表格行做预处理，把行内代码中的|替换为占位符"""
    result = []
    in_backtick = False
    i = 0
    while i < len(line):
        if line[i] == '`' and not in_backtick:
            in_backtick = True
            result.append(line[i])
        elif line[i] == '`' and in_backtick:
            in_backtick = False
            result.append(line[i])
        elif line[i] == '|' and in_backtick:
            result.append('\u0001')
        else:
            result.append(line[i])
        i += 1
    return ''.join(result)

def split_table_line(line):
    """安全分割表格行，跳过行内代码中的|"""
    processed = preprocess_table_row(line)
    parts = processed.split('|')
    return [p.replace('\u0001', '|').strip() for p in parts]

# ===== 转换主逻辑 =====
html_parts = []
i = 0
in_table = False
in_code = False
code_lines = []
in_list = False
list_type = None  # 'ul' or 'ol'
in_blockquote = False
blockquote_lines = []

def flush_table():
    global in_table, html_parts
    if in_table:
        html_parts.append('</table></div>\n')
        in_table = False

def flush_code():
    global in_code, code_lines, html_parts
    if code_lines:
        html_parts.append('<pre><code>')
        html_parts.append('\n'.join(code_lines))
        html_parts.append('</code></pre>\n')
    code_lines = []
    in_code = False

def flush_list():
    global in_list, list_type, html_parts
    if list_type:
        html_parts.append(f'</{list_type}>\n')
    in_list = False
    list_type = None

def flush_blockquote():
    global in_blockquote, blockquote_lines, html_parts
    if not blockquote_lines:
        in_blockquote = False
        return
    
    # 包裹引用块内的 <li> 项到 <ul> 中
    processed = []
    i = 0
    while i < len(blockquote_lines):
        line = blockquote_lines[i]
        if line.startswith('<li>'):
            processed.append('<ul>')
            while i < len(blockquote_lines) and blockquote_lines[i].startswith('<li>'):
                processed.append(blockquote_lines[i])
                i += 1
            processed.append('</ul>')
        else:
            processed.append(line)
            i += 1
    
    html_parts.append('<blockquote>\n')
    html_parts.extend(processed)
    html_parts.append('</blockquote>\n')
    blockquote_lines = []
    in_blockquote = False

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def process_inline(text):
    """处理行内样式: **bold**,  `code`, 链接(很少,暂不处理)"""
    # **bold**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # `code`
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    return text

def make_td(cell):
    return f'<td>{process_inline(cell)}</td>'

def make_tr(cells, is_header=False):
    tag = 'th' if is_header else 'td'
    cls = ' class="table-header"' if is_header else ''
    return '<tr>' + ''.join(f'<{tag}{cls}>{process_inline(c)}</{tag}>' for c in cells) + '</tr>'

while i < len(lines):
    line = lines[i].rstrip('\n')

    # --- 空行 ---
    if line.strip() == '':
        if in_table: flush_table()
        if in_code: flush_code()
        if in_blockquote: flush_blockquote()
        if in_list: flush_list()
        html_parts.append('\n')
        i += 1
        continue

    # --- 代码块 ---
    if line.strip().startswith('```'):
        if in_code:
            flush_code()
        else:
            flush_table()
            flush_list()
            flush_blockquote()
            in_code = True
        i += 1
        continue

    if in_code:
        code_lines.append(line)
        i += 1
        continue

    # --- 引用块 ---
    if line.strip().startswith('>'):
        if in_table: flush_table()
        if in_list: flush_list()
        in_blockquote = True
        content = line.strip()[1:].strip()
        # 引用块内列表项
        if content.startswith('- ') or content.startswith('* '):
            content = content[2:]
            blockquote_lines.append(f'<li>{process_inline(content)}</li>')
        elif content:
            blockquote_lines.append(f'<p>{process_inline(content)}</p>')
        else:
            blockquote_lines.append('<br>')
        i += 1
        continue

    # --- 表格 ---
    if '|' in line and line.strip().startswith('|'):
        if in_list: flush_list()
        if in_blockquote: flush_blockquote()

        cells = split_table_line(line)
        # 过滤开头的空
        cells = [c for c in cells if c]
        if not cells:
            i += 1
            continue

        # 判断是否为分隔行
        if all(re.match(r'^-+$', c) for c in cells):
            i += 1
            continue

        if not in_table:
            html_parts.append('<div class="table-wrapper"><table>\n')
            in_table = True

        # 检查是否是表头（下一行是分隔行）
        is_header = False
        if i + 1 < len(lines):
            next_cells = split_table_line(lines[i + 1].rstrip('\n'))
            next_cells = [c for c in next_cells if c]
            if next_cells and all(re.match(r'^-+$', c) for c in next_cells):
                is_header = True

        html_parts.append(make_tr(cells, is_header))
        i += 1
        continue

    # --- 水平线 ---
    if line.strip() == '---':
        if in_table: flush_table()
        if in_list: flush_list()
        if in_blockquote: flush_blockquote()
        html_parts.append('<hr>\n')
        i += 1
        continue

    # --- 标题 ---
    if line.startswith('# '):
        if in_table: flush_table()
        if in_list: flush_list()
        if in_blockquote: flush_blockquote()
        title = process_inline(line[2:].strip())
        # h1 不添加 id，留给 page-header 使用
        i += 1
        continue  # 跳过h1，由page-header处理

    if line.startswith('## '):
        if in_table: flush_table()
        if in_list: flush_list()
        if in_blockquote: flush_blockquote()
        text = process_inline(line[3:].strip())
        id_slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', text)[:30]
        html_parts.append(f'<h2 id="{id_slug}">{text}</h2>\n')
        i += 1
        continue

    if line.startswith('### '):
        if in_table: flush_table()
        if in_list: flush_list()
        if in_blockquote: flush_blockquote()
        text = process_inline(line[4:].strip())
        id_slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', text)[:30]
        html_parts.append(f'<h3 id="{id_slug}">{text}</h3>\n')
        i += 1
        continue

    # --- 无序列表 ---
    if line.strip().startswith('- ') or line.strip().startswith('* '):
        if in_table: flush_table()
        if in_blockquote: flush_blockquote()
        if not in_list:
            in_list = True
            list_type = 'ul'
            html_parts.append('<ul>\n')
        content = process_inline(line.strip()[2:])
        html_parts.append(f'<li>{content}</li>\n')
        i += 1
        continue

    # --- 有序列表 ---
    m = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
    if m:
        if in_table: flush_table()
        if in_blockquote: flush_blockquote()
        if not in_list:
            in_list = True
            list_type = 'ol'
            html_parts.append('<ol>\n')
        content = process_inline(m.group(2))
        html_parts.append(f'<li>{content}</li>\n')
        i += 1
        continue

    # --- 普通段落 ---
    if in_table: flush_table()
    if in_list: flush_list()
    if in_blockquote: flush_blockquote()
    html_parts.append(f'<p>{process_inline(line.strip())}</p>\n')
    i += 1

# 清理未关闭的块
if in_table: flush_table()
if in_code: flush_code()
if in_list: flush_list()
if in_blockquote: flush_blockquote()

body_content = ''.join(html_parts)

# ===== 生成 TOC =====
toc_items = []
for m in re.finditer(r'<h2 id="([^"]*)">([^<]*)</h2>', body_content):
    tid, ttext = m.group(1), m.group(2)
    toc_items.append(f'<li><a href="#{tid}">{ttext}</a></li>')

toc_html = '\n'.join(toc_items)

# ===== 页面标题（从h1提取）=====
title_match = re.search(r'^# (.+)$', lines[0] if lines else '', re.MULTILINE)
page_title = title_match.group(1) if title_match else '马原常见题型'

# ===== 完整HTML模板 =====
full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - 考研笔记</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <script src="../assets/js/main.js" defer></script>
    <script>MathJax = {{tex: {{inlineMath: [["$", "$"], ["\\\\(", "\\\\)"]], displayMath: [["$$", "$$"], ["\\\\[", "\\\\]"]], packages: {{'[+]': ['physics']}}}}, options: {{ignoreHtmlClass: "no-math"}}}};</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" defer></script>
    <style>
        mjx-container {{
            max-width: 100%;
            overflow-x: auto;
            white-space: normal;
        }}
        .table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}
        .table-wrapper table {{
            table-layout: auto;
            width: 100%;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .math-block {{
            overflow-x: auto;
            padding: 0.5em 0;
        }}
        pre {{
            background: #f5f5f5;
            padding: 12px 16px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        code {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        pre code {{
            background: transparent;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid var(--politics);
            background: var(--politics-bg);
            padding: 12px 16px;
            margin: 12px 0;
            border-radius: 0 4px 4px 0;
        }}
        blockquote p {{
            margin: 0;
        }}
        .container {{
            margin-left: 3%;
            margin-right: auto;
        }}
    </style>
</head>
<body>
<a class="skip-link" href="#main-content">跳到内容</a>
<div id="scroll-progress"></div>

    <nav class="site-nav">
        <div class="site-nav-inner">
            <span class="nav-logo">考研笔记</span>
            <a href="../index.html">首页</a>
            <a href="../knowledge-base.html">知识库</a>
            <a href="../exam-types.html" class="active">常考题型及解法</a>
            <a href="../notes.html">个人笔记</a>
            <a href="../mistakes.html">错题本</a>
            <div class="nav-controls">
                <button class="theme-toggle" aria-label="切换深色/浅色模式"><span class="theme-toggle-icon">🌙</span></button>
                <button class="hamburger" aria-label="菜单" aria-expanded="false">
                    <span></span><span></span><span></span>
                </button>
            </div>
        </div>
    </nav>

<div class="mobile-nav-overlay"></div>
<div class="mobile-menu" role="dialog" aria-label="导航菜单">
    <a href="../index.html">首页</a>
    <a href="../knowledge-base.html">知识库</a>
    <a href="../exam-types.html">常考题型及解法</a>
    <a href="../notes.html">个人笔记</a>
    <a href="../mistakes.html">错题本</a>
    <button class="menu-theme-toggle"><span class="menu-theme-icon">🌙</span> 切换深色/浅色模式</button>
</div>

    <div class="page-header politics">
        <h1>📕 {page_title}</h1>
        <div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / 马原</div>
    </div>

    <div class="container" id="main-content">
        <div class="toc">
            <h3>章节导航</h3>
            <ul>
{toc_html}
            </ul>
        </div>

        <div class="content-card">
{body_content}
        </div>
    </div>

    <div class="site-footer" style="display:none">
        <p>&copy; 2026 cx861 | 考研笔记 | <a href="https://github.com/cx861">GitHub</a></p>
    </div>

    <button class="back-top" id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
    <script>
    const backTop = document.getElementById('backTop');
    window.addEventListener('scroll', () => {{
        backTop.classList.toggle('visible', window.scrollY > 300);
    }});
    </script>
</body>
</html>'''

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Done: {OUTPUT}")
print(f"TOC items: {len(toc_items)}")
