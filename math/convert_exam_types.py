# -*- coding: utf-8 -*-
"""
Markdown -> HTML converter for exam types (linear algebra).
Handles: headings, lists, tables, blockquotes, bold, inline math, display math, code blocks.
Carefully avoids: bare markdown in output, HTML tags inside $$ blocks, pipe conflicts.
"""

import re
import sys


def convert_md_to_html(md_text):
    """Convert markdown text to HTML content for injection."""
    lines = md_text.split('\n')
    html_lines = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # --- Horizontal rule ---
        if re.match(r'^-{3,}\s*$', line.strip()):
            html_lines.append('<hr>')
            i += 1
            continue

        # --- Code block (```) ---
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            # i now points to closing ```
            code_content = '\n'.join(code_lines)
            # Escape HTML special chars in code
            code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(f'<pre><code>{code_content}</code></pre>')
            i += 1  # skip closing ```
            continue

        # --- Heading ---
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            sharp_count = len(m.group(1))
            if sharp_count == 1:
                i += 1
                continue
            level = sharp_count
            heading_text = m.group(2).strip()
            heading_html = process_inline(heading_text)
            heading_id = re.sub(r'[^\w\u4e00-\u9fff]+', '-', heading_text).strip('-')
            html_lines.append(f'<h{level} id="{heading_id}">{heading_html}</h{level}>')
            i += 1
            continue

        # --- Blockquote ---
        m = re.match(r'^>\s*(.*)$', line)
        if m:
            bq_lines = []
            while i < n and re.match(r'^>\s*(.*)$', lines[i]):
                bq_lines.append(re.match(r'^>\s*(.*)$', lines[i]).group(1).strip())
                i += 1
            bq_html = process_inline(' '.join(bq_lines))
            html_lines.append(f'<blockquote><p>{bq_html}</p></blockquote>')
            continue

        # --- Table ---
        # Check if this line starts a table (starts with | and next line is separator)
        stripped_line = line.strip()
        if stripped_line.startswith('|') and i + 1 < n and re.match(r'^\s*\|[-:\s|]+\|\s*$', lines[i + 1]):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_html = process_table(table_lines)
            html_lines.append(table_html)
            continue

        # --- Unordered list ---
        if re.match(r'^(\s*)- ', line):
            list_html = process_unordered_list(lines, i)
            html_lines.append(list_html['html'])
            i = list_html['next_i']
            continue

        # --- Ordered list ---
        if re.match(r'^(\s*)\d+\.\s', line):
            list_html = process_ordered_list(lines, i)
            html_lines.append(list_html['html'])
            i = list_html['next_i']
            continue

        # --- Empty line ---
        if line.strip() == '':
            i += 1
            continue

        # --- Display math block ($$) ---
        if '$$' in line:
            if line.strip() == '$$':
                math_lines = []
                i += 1
                while i < n and lines[i].strip() != '$$':
                    math_lines.append(lines[i])
                    i += 1
                math_content = '\n'.join(math_lines)
                html_lines.append(f'<div class="math-block">$$\n{math_content}\n$$</div>')
                i += 1
                continue
            else:
                m_block = re.match(r'^\s*\$\$(.+?)\$\$\s*$', line)
                if m_block:
                    math_content = m_block.group(1).strip()
                    html_lines.append(f'<div class="math-block">$${math_content}$$</div>')
                    i += 1
                    continue

        # --- Paragraph / mixed content ---
        if line.strip():
            para_html = process_inline(line.strip())
            html_lines.append(f'<p>{para_html}</p>')
            i += 1
            continue

        i += 1

    return '\n'.join(html_lines)


def process_inline(text):
    """Process inline formatting: bold, inline math."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = process_inline_math(text)
    return text


def process_inline_math(text):
    """Process inline $...$ math, avoiding display math $$...$$ matches."""
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '$':
            if i + 1 < n and text[i + 1] == '$':
                result.append('$$')
                i += 2
                while i < n and not (text[i] == '$' and i + 1 < n and text[i + 1] == '$'):
                    result.append(text[i])
                    i += 1
                if i < n:
                    result.append('$$')
                    i += 2
            else:
                j = i + 1
                while j < n and text[j] != '$':
                    j += 1
                if j < n:
                    math_expr = text[i + 1:j]
                    result.append(f'<span class="math-inline">${math_expr}$</span>')
                    i = j + 1
                else:
                    result.append(text[i])
                    i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def process_unordered_list(lines, start_i):
    """Process unordered list starting at start_i."""
    html = ['<ul>']
    i = start_i
    n = len(lines)
    while i < n:
        m = re.match(r'^(\s*)- (.+)$', lines[i])
        if m:
            content = m.group(2).strip()
            item_html = process_inline(content)
            html.append(f'<li>{item_html}</li>')
            i += 1
            # Handle multi-line list items
            while i < n and lines[i].strip() and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and not lines[i].strip().startswith('>') and not lines[i].strip().startswith('```'):
                cont_content = lines[i].strip()
                cont_html = process_inline(cont_content)
                html[-1] = html[-1].replace('</li>', '') + f' {cont_html}</li>'
                i += 1
        else:
            break
    html.append('</ul>')
    return {'html': '\n'.join(html), 'next_i': i}


def process_ordered_list(lines, start_i):
    """Process ordered list starting at start_i."""
    html = ['<ol>']
    i = start_i
    n = len(lines)
    while i < n:
        m = re.match(r'^(\s*)\d+\.\s+(.+)$', lines[i])
        if m:
            content = m.group(2).strip()
            item_html = process_inline(content)
            html.append(f'<li>{item_html}</li>')
            i += 1
            # Handle multi-line
            while i < n and lines[i].strip() and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and not lines[i].strip().startswith('>') and not lines[i].strip().startswith('```'):
                cont_content = lines[i].strip()
                cont_html = process_inline(cont_content)
                html[-1] = html[-1].replace('</li>', '') + f' {cont_html}</li>'
                i += 1
        else:
            break
    html.append('</ol>')
    return {'html': '\n'.join(html), 'next_i': i}


def split_table_line(line):
    """Split a markdown table line by |, but NOT inside $...$ or $$...$$."""
    cells = []
    current = []
    i = 0
    n = len(line)
    in_inline_math = False
    in_display_math = False

    while i < n:
        ch = line[i]

        if ch == '$':
            if i + 1 < n and line[i + 1] == '$':
                in_display_math = not in_display_math
                current.append('$$')
                i += 2
                continue
            elif not in_display_math:
                in_inline_math = not in_inline_math
                current.append('$')
                i += 1
                continue

        if ch == '|' and not in_inline_math and not in_display_math:
            cells.append(''.join(current))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    cells.append(''.join(current))
    return cells


def process_table(table_lines):
    """Process a markdown table into HTML <table>."""
    data_lines = []
    is_first = True
    for line in table_lines:
        stripped = line.strip()
        if re.match(r'^\|[-:\s|]+\|$', stripped):
            continue

        # Use math-aware split
        cells = split_table_line(stripped)
        # Remove empty first/last from leading/trailing |
        if cells and cells[0].strip() == '':
            cells = cells[1:]
        if cells and cells[-1].strip() == '':
            cells = cells[:-1]

        row_cells = []
        for cell in cells:
            cell_stripped = cell.strip()
            cell_html = process_inline(cell_stripped)
            row_cells.append(cell_html)

        if is_first:
            header_cells = ''.join(f'<th>{c}</th>' for c in row_cells)
            data_lines.append(f'<tr class="table-header">{header_cells}</tr>')
            is_first = False
        else:
            data_cells = ''.join(f'<td>{c}</td>' for c in row_cells)
            data_lines.append(f'<tr>{data_cells}</tr>')

    return '<div class="table-wrapper"><table>' + '\n'.join(data_lines) + '</table></div>'


def build_full_page(content_html, toc_items):
    """Build the complete HTML page for exam types."""
    toc_html = '<ul>\n'
    for item_id, item_text in toc_items:
        toc_html += f'                <li><a href="#{item_id}">{item_text}</a></li>\n'
    toc_html += '            </ul>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>常考题型 - 线性代数 - 考研笔记</title>
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
            table-layout: fixed;
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
            border-left: 4px solid #f5a623;
            background: #fffbe6;
            padding: 12px 16px;
            margin: 12px 0;
            border-radius: 0 4px 4px 0;
        }}
        blockquote p {{
            margin: 0;
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

    <div class="page-header math">
        <h1>🎯 线性代数 · 常考题型与解法</h1>
        <div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / 线性代数</div>
    </div>

    <div class="container" id="main-content">
        <div class="toc">
            <h3>章节导航</h3>
            {toc_html}
        </div>

        <div class="content-card">
{content_html}
        </div>
    </div>

    <div class="site-footer">
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


def extract_toc(md_text):
    """Extract TOC items from markdown headings at ## and ### level."""
    toc_items = []
    for line in md_text.split('\n'):
        m = re.match(r'^(#{2,3})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            clean_text = re.sub(r'\$[^$]+\$', '', clean_text).strip()
            heading_id = re.sub(r'[^\w\u4e00-\u9fff]+', '-', text).strip('-')
            if level == 2:
                toc_items.append((heading_id, clean_text))
            elif level == 3:
                toc_items.append((heading_id, '　　' + clean_text))
    return toc_items


def validate_html(html_content):
    """Validate the generated HTML for common issues."""
    errors = []

    # 1. Check brace balance in $$ blocks
    blocks = re.findall(r'\$\$(.*?)\$\$', html_content, re.DOTALL)
    for idx, block in enumerate(blocks):
        opens = block.count('{')
        closes = block.count('}')
        if opens != closes:
            errors.append(f"花括号不匹配: $$ block {idx+1}: {{ = {opens}, }} = {closes}, diff = {opens - closes}")

    # 2. Check for HTML tags inside $$ blocks
    for idx, block in enumerate(blocks):
        if re.search(r'<\w+[^>]*>', block):
            errors.append(f"$$ block {idx+1} 内含 HTML 标签")

    # 3. Check for \begin without \end
    begins = re.findall(r'\\begin\{(\w+)\}', html_content)
    ends = re.findall(r'\\end\{(\w+)\}', html_content)
    begin_counts = {}
    end_counts = {}
    for b in begins:
        begin_counts[b] = begin_counts.get(b, 0) + 1
    for e in ends:
        end_counts[e] = end_counts.get(e, 0) + 1
    for env in set(list(begin_counts.keys()) + list(end_counts.keys())):
        bc = begin_counts.get(env, 0)
        ec = end_counts.get(env, 0)
        if bc != ec:
            errors.append(f"环境 {env}: \\begin={bc}, \\end={ec}")

    # 4. Check for bare markdown outside math blocks
    clean = re.sub(r'\$\$.*?\$\$', '', html_content, flags=re.DOTALL)
    clean = re.sub(r'\$[^$]+\$', '', clean)
    bare_patterns = [
        (r'(?<![<])####?\s', '裸标题标记 ##'),
        (r'(?<![<\w])\*\*[^*]+\*\*', '裸加粗 **text**'),
    ]
    for pattern, desc in bare_patterns:
        if re.search(pattern, clean):
            errors.append(desc)

    return errors


def main():
    md_path = r'C:\Users\陈鑫\Desktop\过程文档\文档\线代常考题型与解法.md'
    out_path = r'E:\coding\demo\docs\math\linear-algebra-exam-types.html'

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    print(f"Read {len(md_text)} chars from markdown file")

    toc_items = extract_toc(md_text)
    print(f"Extracted {len(toc_items)} TOC items")

    content_html = convert_md_to_html(md_text)
    print(f"Generated {len(content_html)} chars of HTML content")

    full_page = build_full_page(content_html, toc_items)
    print(f"Full page: {len(full_page)} chars")

    errors = validate_html(full_page)
    if errors:
        print("\n=== VALIDATION ERRORS ===")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        print("\n✅ All validation checks passed!")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full_page)

    print(f"\nWritten to: {out_path}")
    print("Done!")


if __name__ == '__main__':
    main()
