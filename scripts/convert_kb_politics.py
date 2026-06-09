#!/usr/bin/env python3
"""政治知识库 Markdown → HTML 批量转换"""
import re, os

def preprocess_table_row(line):
    result = []
    in_backtick = False
    for ch in line:
        if ch == '`' and not in_backtick: in_backtick = True; result.append(ch)
        elif ch == '`' and in_backtick: in_backtick = False; result.append(ch)
        elif ch == '|' and in_backtick: result.append('\u0001')
        else: result.append(ch)
    return ''.join(result)

def split_table_line(line):
    return [p.replace('\u0001', '|').strip() for p in preprocess_table_row(line).split('|')]

def process_inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    return text

def convert(lines, emoji, page_title):
    html, i = [], 0
    in_table = in_code = in_list = in_blockquote = False
    code_lines = blockquote_lines = []
    list_type = None

    def ft():
        nonlocal in_table
        if in_table: html.append('</table></div>\n'); in_table = False
    def fc():
        nonlocal in_code, code_lines
        if code_lines:
            joined = "\n".join(code_lines)
            html.append(f'<pre><code>{joined}</code></pre>\n')
        code_lines = []; in_code = False
    def fl():
        nonlocal in_list, list_type
        if list_type: html.append(f'</{list_type}>\n')
        in_list = False; list_type = None
    def fb():
        nonlocal in_blockquote, blockquote_lines
        if not blockquote_lines: in_blockquote = False; return
        proc, idx = [], 0
        while idx < len(blockquote_lines):
            ln = blockquote_lines[idx]
            if ln.startswith('<li>'):
                proc.append('<ul>')
                while idx < len(blockquote_lines) and blockquote_lines[idx].startswith('<li>'):
                    proc.append(blockquote_lines[idx]); idx += 1
                proc.append('</ul>')
            else: proc.append(ln); idx += 1
        html.append('<blockquote>\n'); html.extend(proc); html.append('</blockquote>\n')
        blockquote_lines = []; in_blockquote = False

    while i < len(lines):
        line = lines[i].rstrip('\n')
        if line.strip() == '':
            ft(); fc(); fb(); fl()
            html.append('\n'); i += 1; continue
        if line.strip().startswith('```'):
            if in_code: fc()
            else: ft(); fl(); fb(); in_code = True
            i += 1; continue
        if in_code: code_lines.append(line); i += 1; continue
        if line.strip().startswith('>'):
            ft(); fl(); in_blockquote = True
            c = line.strip()[1:].strip()
            if c.startswith('- '): blockquote_lines.append(f'<li>{process_inline(c[2:])}</li>')
            elif c: blockquote_lines.append(f'<p>{process_inline(c)}</p>')
            else: blockquote_lines.append('<br>')
            i += 1; continue
        if '|' in line and line.strip().startswith('|'):
            fl(); fb()
            cells = [c for c in split_table_line(line) if c]
            if not cells: i += 1; continue
            if all(re.match(r'^-+$', c) for c in cells): i += 1; continue
            if not in_table: html.append('<div class="table-wrapper"><table>\n'); in_table = True
            is_header = False
            if i + 1 < len(lines):
                nc = [c for c in split_table_line(lines[i+1].rstrip('\n')) if c]
                if nc and all(re.match(r'^-+$', c) for c in nc): is_header = True
            tag = 'th' if is_header else 'td'
            cls = ' class="table-header"' if is_header else ''
            html.append('<tr>' + ''.join(f'<{tag}{cls}>{process_inline(c)}</{tag}>' for c in cells) + '</tr>')
            i += 1; continue
        if line.strip() == '---':
            ft(); fl(); fb()
            html.append('<hr>\n'); i += 1; continue
        if line.startswith('## '):
            ft(); fl(); fb()
            text = process_inline(line[3:].strip())
            sid = re.sub(r'[^\w\u4e00-\u9fff-]', '', text)[:30]
            html.append(f'<h2 id="{sid}">{text}</h2>\n'); i += 1; continue
        if line.startswith('### '):
            ft(); fl(); fb()
            text = process_inline(line[4:].strip())
            sid = re.sub(r'[^\w\u4e00-\u9fff-]', '', text)[:30]
            html.append(f'<h3 id="{sid}">{text}</h3>\n'); i += 1; continue
        if line.startswith('#### '):
            ft(); fl(); fb()
            text = process_inline(line[5:].strip())
            sid = re.sub(r'[^\w\u4e00-\u9fff-]', '', text)[:30]
            html.append(f'<h4 id="{sid}">{text}</h4>\n'); i += 1; continue
        if line[0] == '#' and line[0:5] != '#### ':
            ft(); fl(); fb(); i += 1; continue
        if line.strip().startswith('- '):
            ft(); fb()
            if not in_list: in_list = True; list_type = 'ul'; html.append('<ul>\n')
            html.append(f'<li>{process_inline(line.strip()[2:])}</li>\n'); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.+)$', line.strip())
        if m:
            ft(); fb()
            if not in_list: in_list = True; list_type = 'ol'; html.append('<ol>\n')
            html.append(f'<li>{process_inline(m.group(2))}</li>\n'); i += 1; continue
        ft(); fl(); fb()
        html.append(f'<p>{process_inline(line.strip())}</p>\n'); i += 1

    ft(); fc(); fl(); fb()
    body = ''.join(html)

    toc = []
    for m in re.finditer(r'<h2 id="([^"]*)">([^<]*)</h2>', body):
        toc.append(f'<li><a href="#{m.group(1)}">{m.group(2)}</a></li>')
    toc_html = '\n'.join(toc)

    tables_n = body.count('<div class="table-wrapper"')
    code_n = body.count('<pre>')
    bq_n = body.count('</blockquote>')

    return f'''<!DOCTYPE html>
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
        mjx-container {{ max-width:100%; overflow-x:auto; white-space:normal; }}
        .table-wrapper {{ overflow-x:auto; -webkit-overflow-scrolling:touch; }}
        .table-wrapper table {{ table-layout:auto; width:100%; word-wrap:break-word; overflow-wrap:break-word; }}
        pre {{ background:#f5f5f5; padding:12px 16px; border-radius:6px; overflow-x:auto; font-family:Consolas,Monaco,monospace; font-size:0.9em; line-height:1.5; }}
        code {{ font-family:Consolas,Monaco,monospace; background:#f0f0f0; padding:2px 5px; border-radius:3px; font-size:0.9em; }}
        pre code {{ background:transparent; padding:0; }}
        blockquote {{ border-left:4px solid var(--politics); background:var(--politics-bg); padding:12px 16px; margin:12px 0; border-radius:0 4px 4px 0; }}
        blockquote p {{ margin:0; }}
        .container {{ margin-left:3%; margin-right:auto; }}
    </style>
</head>
<body>
<a class="skip-link" href="#main-content">跳到内容</a>
<div id="scroll-progress"></div>
    <nav class="site-nav">
        <div class="site-nav-inner">
            <span class="nav-logo">考研笔记</span>
            <a href="../index.html">首页</a>
            <a href="../knowledge-base.html" class="active">知识库</a>
            <a href="../exam-types.html">常考题型及解法</a>
            <a href="../notes.html">个人笔记</a>
            <a href="../mistakes.html">错题本</a>
            <div class="nav-controls">
                <button class="theme-toggle" aria-label="切换深色/浅色模式"><span class="theme-toggle-icon">🌙</span></button>
                <button class="hamburger" aria-label="菜单" aria-expanded="false"><span></span><span></span><span></span></button>
            </div>
        </div>
    </nav>
<div class="mobile-nav-overlay"></div>
<div class="mobile-menu" role="dialog" aria-label="导航菜单">
    <a href="../index.html">首页</a><a href="../knowledge-base.html">知识库</a><a href="../exam-types.html">常考题型及解法</a><a href="../notes.html">个人笔记</a><a href="../mistakes.html">错题本</a>
    <button class="menu-theme-toggle"><span class="menu-theme-icon">🌙</span> 切换深色/浅色模式</button>
</div>
    <div class="page-header politics">
        <h1>{emoji} {page_title}</h1>
        <div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../knowledge-base.html">知识库</a> / {page_title}</div>
    </div>
    <div class="container" id="main-content">
        <div class="toc"><h3>章节导航</h3><ul>{toc_html}</ul></div>
        <div class="content-card">{body}</div>
    </div>
    <div class="site-footer" style="display:none"><p>&copy; 2026 cx861 | 考研笔记 | <a href="https://github.com/cx861">GitHub</a></p></div>
    <button class="back-top" id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>
    <script>const backTop=document.getElementById('backTop');window.addEventListener('scroll',()=>{{backTop.classList.toggle('visible',window.scrollY>300);}});</script>
</body>
</html>''', tables_n, code_n, bq_n

# ===== 批量转换 =====
TASKS = [
    (r"C:\Users\陈鑫\Desktop\知识库\政治\06-形势与政策知识点.md",
     r"E:\coding\demo\docs\politics\policy.html", "🌍", "形势与政策以及当代世界经济与政治"),
]

os.makedirs(r"E:\coding\demo\docs\politics", exist_ok=True)

for input_path, output_path, emoji, title in TASKS:
    with open(input_path, "r", encoding="utf-8") as f:
        input_lines = f.readlines()
    html, tables_n, code_n, bq_n = convert(input_lines, emoji, title)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ {os.path.basename(output_path)}: {len(input_lines)}行 → {tables_n}T/{code_n}C/{bq_n}B")
