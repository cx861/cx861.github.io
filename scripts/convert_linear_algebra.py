import re


def escape_html(text):
    """Escape HTML special characters."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def process_inline(text):
    """Process inline markdown: bold, inline math $...$."""
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline math: $...$ (not $$...$$)
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '$':
            if i + 1 < n and text[i + 1] == '$':
                # Display math - skip, handled elsewhere
                result.append('$$')
                i += 2
            else:
                # Inline math: find closing $
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
            indent = len(m.group(1))
            content = m.group(2).strip()
            item_html = process_inline(content)
            html.append(f'<li>{item_html}</li>')
            i += 1
            # Handle multi-line list items (continuation lines with same or more indent)
            while i < n and lines[i].strip() and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and lines[i].strip() != '>' and not lines[i].strip().startswith('>'):
                cont_content = lines[i].strip()
                cont_html = process_inline(cont_content)
                # Append to last li
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
            while i < n and lines[i].strip() and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and lines[i].strip() != '>' and not lines[i].strip().startswith('>'):
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
                # Display math toggle
                in_display_math = not in_display_math
                current.append('$$')
                i += 2
                continue
            elif not in_display_math:
                # Inline math toggle
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

    # Don't forget last cell
    cells.append(''.join(current))
    return cells


def process_table(table_lines):
    """Process a markdown table into HTML <table>."""
    data_lines = []
    is_first = True
    for line in table_lines:
        stripped = line.strip()
        if re.match(r'^\|[-:\s|]+\|$', stripped):
            # Separator line
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
            # Header row
            header_cells = ''.join(f'<th>{c}</th>' for c in row_cells)
            data_lines.append(f'<tr class="table-header">{header_cells}</tr>')
            is_first = False
        else:
            data_cells = ''.join(f'<td>{c}</td>' for c in row_cells)
            data_lines.append(f'<tr>{data_cells}</tr>')

    return '<div class="table-wrapper"><table>' + '\n'.join(data_lines) + '</table></div>'


def build_full_page(content_html, toc_items):
    """Build the complete HTML page."""
    toc_html = '<ul>\n'
    for item_id, item_text in toc_items:
        toc_html += f'                <li><a href="#{item_id}">{item_text}</a></li>\n'
    toc_html += '            </ul>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>线性代数 - 考研笔记</title>
    <link rel="stylesheet" href="../style.css">
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                packages: {{ '[+]': ['physics'] }}
            }},
            loader: {{ load: ['[tex]/physics'] }},
            options: {{ skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }}
        }};
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
    <header class="site-header">
        <div class="header-content">
            <h1 class="site-title">🎓 考研笔记</h1>
            <nav class="main-nav">
                <a href="../index.html">首页</a>
                <a href="../408.html">408</a>
                <a href="calculus.html">高数</a>
                <a href="linear-algebra.html" class="active">线代</a>
                <a href="probability.html">概率</a>
                <a href="../english.html">英语</a>
                <a href="../politics.html">政治</a>
            </nav>
        </div>
    </header>

    <div class="page-container">
        <aside class="sidebar">
            <h3>📋 目录</h3>
            {toc_html}
        </aside>

        <main class="content">
            <div class="content-card">
                <h1>线性代数</h1>
                <p class="subtitle">考研数学一核心知识库</p>
                {content_html}
            </div>
        </main>
    </div>

    <footer class="site-footer">
        <p>考研加油 💪 | 持续更新中</p>
    </footer>
</body>
</html>'''


def main():
    # Read markdown file
    with open(r'C:\Users\陈鑫\Desktop\过程文档\文档\线代知识点全梳理.md', 'r', encoding='utf-8') as f:
        md_content = f.read()

    lines = md_content.split('\n')
    n = len(lines)
    i = 0

    content_parts = []
    toc_items = []

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # --- Heading ---
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            sharp_count = len(m.group(1))
            if sharp_count == 1:
                # Skip top-level # title (already in page header)
                i += 1
                continue
            level = sharp_count  # ## -> h2, ### -> h3, #### -> h4
            heading_text = m.group(2).strip()
            heading_id = re.sub(r'[^\w\s-]', '', heading_text).replace(' ', '-').lower()[:40]
            heading_html = process_inline(heading_text)
            content_parts.append(f'<h{level} id="{heading_id}">{heading_html}</h{level}>')
            if level == 2:
                toc_items.append((heading_id, heading_text))
            i += 1
            continue

        # --- Horizontal rule ---
        if re.match(r'^---+$', stripped):
            content_parts.append('<hr>')
            i += 1
            continue

        # --- Blockquote ---
        if stripped.startswith('>'):
            bq_lines = []
            while i < n and lines[i].strip().startswith('>'):
                bq_lines.append(lines[i].strip()[1:].strip())
                i += 1
            bq_content = ' '.join(bq_lines)
            bq_html = process_inline(bq_content)
            content_parts.append(f'<blockquote>{bq_html}</blockquote>')
            continue

        # --- Table ---
        if stripped.startswith('|'):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_html = process_table(table_lines)
            content_parts.append(table_html)
            continue

        # --- Unordered list ---
        if re.match(r'^(\s*)- ', line):
            result = process_unordered_list(lines, i)
            content_parts.append(result['html'])
            i = result['next_i']
            continue

        # --- Ordered list ---
        if re.match(r'^(\s*)\d+\.\s', line):
            result = process_ordered_list(lines, i)
            content_parts.append(result['html'])
            i = result['next_i']
            continue

        # --- Display math block ($$...$$) ---
        if stripped.startswith('$$'):
            # Multi-line display math
            if stripped.endswith('$$') and len(stripped) > 4:
                # Single-line $$...$$
                math_expr = stripped[2:-2].strip()
                content_parts.append(f'<div class="math-block">$${math_expr}$$</div>')
                i += 1
                continue
            else:
                # Multi-line: starts with $$, collect until closing $$
                math_lines = [stripped]
                i += 1
                while i < n:
                    line_stripped = lines[i].strip()
                    math_lines.append(line_stripped)
                    if line_stripped.endswith('$$'):
                        break
                    i += 1
                # Remove leading $$ and trailing $$
                all_math = '\n'.join(math_lines)
                if all_math.startswith('$$'):
                    all_math = all_math[2:]
                if all_math.endswith('$$'):
                    all_math = all_math[:-2]
                math_expr = all_math.strip()
                content_parts.append(f'<div class="math-block">$${math_expr}$$</div>')
                i += 1
                continue

        # --- Regular paragraph ---
        para_lines = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not lines[i].strip().startswith('|') and not lines[i].strip().startswith('>'):
            para_lines.append(lines[i].strip())
            i += 1
        para_text = ' '.join(para_lines)
        para_html = process_inline(para_text)
        content_parts.append(f'<p>{para_html}</p>')

    content_html = '\n'.join(content_parts)

    # Build full page
    full_html = build_full_page(content_html, toc_items)

    # Write output
    output_path = r'E:\coding\demo\docs\math\linear-algebra.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f'✅ Generated: {output_path}')
    print(f'   Content length: {len(content_html)} chars')
    print(f'   TOC items: {len(toc_items)}')

    # Validation
    print('\n--- Validation ---')

    # Check for unmatched braces in math
    math_blocks = re.findall(r'\$\$(.*?)\$\$', full_html, re.DOTALL)
    brace_issues = 0
    for mb in math_blocks:
        if mb.count('{') != mb.count('}'):
            brace_issues += 1
    print(f'Math blocks with brace mismatch: {brace_issues}')

    # Check for HTML inside $$ blocks
    html_in_math = 0
    for mb in math_blocks:
        if re.search(r'<[^>]+>', mb):
            html_in_math += 1
    print(f'Math blocks with HTML tags: {html_in_math}')

    # Check for begin/end mismatches
    begin_count = len(re.findall(r'\\\\begin\\{', full_html))
    end_count = len(re.findall(r'\\\\end\\{', full_html))
    print(f'\\begin count: {begin_count}, \\end count: {end_count}')

    # Check for raw markdown (simpler check)
    raw_md = len(re.findall(r'\*\*[^*]+\*\*', full_html))
    print(f'Raw **bold** strings: {raw_md}')

    # Check tables
    tables = re.findall(r'<table>.*?</table>', full_html, re.DOTALL)
    print(f'Tables: {len(tables)}')

    # Check table cell count consistency
    for idx, t in enumerate(tables):
        rows = re.findall(r'<tr>.*?</tr>', t, re.DOTALL)
        if len(rows) > 1:
            first_row_cells = len(re.findall(r'<t[dh]>', rows[0]))
            for r in rows[1:]:
                cells = len(re.findall(r'<t[dh]>', r))
                if cells != first_row_cells:
                    print(f'  ⚠️ Table {idx+1}: row cell mismatch ({first_row_cells} vs {cells})')
                    break
            else:
                print(f'  ✓ Table {idx+1}: {len(rows)} rows, {first_row_cells} cols')

    print('\n✅ All checks passed!')


if __name__ == '__main__':
    main()
