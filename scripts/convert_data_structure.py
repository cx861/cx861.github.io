# -*- coding: utf-8 -*-
"""
Markdown -> HTML converter for CS knowledge base pages.
Handles: headings, lists, tables (math-aware pipe splitting), blockquotes,
bold, inline code, inline math $...$, display math $$...$$.
"""

import re


def escape_html(text):
    """Escape HTML special characters (but not $ or backslashes for LaTeX)."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def process_inline(text):
    """Process inline markdown: bold, inline code, inline math $...$."""
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code: `text`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Inline math: $...$ (not $$...$$)
    text = process_inline_math(text)
    return text


def process_inline_math(text):
    """Process inline $...$ math, preserving $$...$$ display math."""
    result = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '$':
            if i + 1 < n and text[i + 1] == '$':
                # Display math boundary - pass through
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
        cells = split_table_line(stripped)
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


def process_unordered_list(lines, start_i):
    """Process unordered list."""
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
            # Multi-line continuation
            while i < n and lines[i].strip() and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and lines[i].strip() != '>' and not lines[i].strip().startswith('>'):
                cont = lines[i].strip()
                cont_html = process_inline(cont)
                html[-1] = html[-1].replace('</li>', '') + f' {cont_html}</li>'
                i += 1
        else:
            break
    html.append('</ul>')
    return {'html': '\n'.join(html), 'next_i': i}


def process_ordered_list(lines, start_i):
    """Process ordered list."""
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
            while i < n and lines[i].strip() and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^\|', lines[i]) and lines[i].strip() != '>' and not lines[i].strip().startswith('>'):
                cont = lines[i].strip()
                cont_html = process_inline(cont)
                html[-1] = html[-1].replace('</li>', '') + f' {cont_html}</li>'
                i += 1
        else:
            break
    html.append('</ol>')
    return {'html': '\n'.join(html), 'next_i': i}


def convert_md_to_html(md_text):
    """Convert markdown text to HTML content."""
    lines = md_text.split('\n')
    html_lines = []
    toc_items = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # --- Horizontal rule ---
        if re.match(r'^---+$', stripped):
            html_lines.append('<hr>')
            i += 1
            continue

        # --- Heading ---
        m = re.match(r'^(#{1,4})\s+(.+)$', line)
        if m:
            sharp_count = len(m.group(1))
            if sharp_count == 1:
                i += 1
                continue
            level = sharp_count  # ## -> h2, ### -> h3, #### -> h4
            heading_text = m.group(2).strip()
            heading_id = re.sub(r'[^\w\u4e00-\u9fff]+', '-', heading_text).strip('-').lower()[:50]
            heading_html = process_inline(heading_text)
            html_lines.append(f'<h{level} id="{heading_id}">{heading_html}</h{level}>')
            if level == 2:
                toc_items.append((heading_id, heading_text))
            i += 1
            continue

        # --- Blockquote ---
        if stripped.startswith('>'):
            bq_lines = []
            while i < n and lines[i].strip().startswith('>'):
                bq_text = lines[i].strip()
                if bq_text == '>':
                    bq_lines.append('')
                else:
                    bq_lines.append(bq_text[1:].strip() if bq_text.startswith('>') else bq_text)
                i += 1
            bq_content = ' '.join(bq_lines)
            bq_html = process_inline(bq_content)
            html_lines.append(f'<blockquote>{bq_html}</blockquote>')
            continue

        # --- Table ---
        if stripped.startswith('|') and i + 1 < n and re.match(r'^\s*\|[-:\s|]+\|\s*$', lines[i + 1]):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_html = process_table(table_lines)
            html_lines.append(table_html)
            continue

        # --- Unordered list ---
        if re.match(r'^(\s*)- ', line):
            result = process_unordered_list(lines, i)
            html_lines.append(result['html'])
            i = result['next_i']
            continue

        # --- Ordered list ---
        if re.match(r'^(\s*)\d+\.\s', line):
            result = process_ordered_list(lines, i)
            html_lines.append(result['html'])
            i = result['next_i']
            continue

        # --- Display math block ($$) ---
        if stripped.startswith('$$'):
            if stripped.endswith('$$') and len(stripped) > 4:
                math_expr = stripped[2:-2].strip()
                html_lines.append(f'<div class="math-block">$${math_expr}$$</div>')
                i += 1
                continue
            else:
                math_lines = [stripped]
                i += 1
                while i < n:
                    ml = lines[i].strip()
                    math_lines.append(ml)
                    if ml.endswith('$$'):
                        break
                    i += 1
                all_math = '\n'.join(math_lines)
                if all_math.startswith('$$'):
                    all_math = all_math[2:]
                if all_math.endswith('$$'):
                    all_math = all_math[:-2]
                math_expr = all_math.strip()
                html_lines.append(f'<div class="math-block">$${math_expr}$$</div>')
                i += 1
                continue

        # --- Regular paragraph ---
        para_lines = [stripped]
        i += 1
        while i < n and lines[i].strip() and not re.match(r'^#{1,4}\s', lines[i]) and not re.match(r'^---', lines[i]) and not re.match(r'^(\s*)- ', lines[i]) and not re.match(r'^(\s*)\d+\.\s', lines[i]) and not lines[i].strip().startswith('|') and not lines[i].strip().startswith('>') and not lines[i].strip().startswith('$$'):
            para_lines.append(lines[i].strip())
            i += 1
        para_text = ' '.join(para_lines)
        para_html = process_inline(para_text)
        html_lines.append(f'<p>{para_html}</p>')

    return '\n'.join(html_lines), toc_items


def preprocess_table_bare_pipes(text):
    """In table rows, protect bare |X| set/absolute-value notation from pipe splitting.
    Strategy: only protect |X| where X is a single letter/digit (|V|, |E|, |v|)
    and also protect |expr| patterns that appear adjacent to math operators ($, numbers, ≤, etc.)
    """
    lines = text.split('\n')
    in_table = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and not in_table:
            in_table = True
        elif not stripped.startswith('|') and in_table:
            in_table = False

        if in_table and stripped.startswith('|'):
            if not re.match(r'^\|[-:\s|]+\|$', stripped):
                # Phase 1: protect single-letter |X| (e.g. |V|, |E|)
                line = re.sub(r'\|([A-Za-z0-9])\|', r'PIPEPROTECT\1PIPEPROTECT', line)
                # Phase 2: protect |expr| where expr is short and contains math-like chars
                # e.g. |i-j|, |左右子树高度差|
                # Match |...| where content has letters, digits, -, +, Chinese chars, but no spaces
                line = re.sub(r'\|([A-Za-z0-9\u4e00-\u9fff\-\+]+)\|', r'PIPEPROTECT\1PIPEPROTECT', line)
        result.append(line)
    return '\n'.join(result)


def postprocess_pipeprotect(text):
    """Convert PIPEPROTECT placeholders back to |X| for rendering."""
    return text.replace('PIPEPROTECT', '|')


def main():
    md_path = r'C:\Users\陈鑫\Desktop\过程文档\文档\408数据结构_按章节知识点.md'
    output_path = r'E:\coding\demo\docs\cs\data-structure.html'

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Preprocess: protect bare |X| in table rows (e.g. O(|V|²))
    md_content = preprocess_table_bare_pipes(md_content)

    content_html, toc_items = convert_md_to_html(md_content)

    # Postprocess: restore PIPEPROTECT placeholders
    content_html = postprocess_pipeprotect(content_html)

    # Build TOC
    toc_html = '            <ul>\n'
    for item_id, item_text in toc_items:
        toc_html += f'                <li><a href="#{item_id}">{item_text}</a></li>\n'
    toc_html += '            </ul>'

    # Read existing page template
    with open(output_path, 'r', encoding='utf-8') as f:
        page = f.read()

    # Replace TOC
    page = re.sub(
        r'(<div class="toc">\s*<h3>目录</h3>\s*)<ul>.*?</ul>(\s*</div>)',
        rf'\1{toc_html}\2',
        page,
        flags=re.DOTALL
    )

    # Replace content-card content
    card_start = page.find('<div class="content-card">')
    card_end_marker = '</div>\n    </div>'
    if card_start >= 0:
        # Find the closing </div> for content-card
        # It's the </div> right before </div> (container close)
        search_start = card_start + len('<div class="content-card">')
        # Find the pattern: content </div>\n    </div>
        end_pattern = card_end_marker
        end_idx = page.find(end_pattern, search_start)
        if end_idx >= 0:
            page = page[:card_start + len('<div class="content-card">')] + '\n' + content_html + '\n        ' + page[end_idx:]

    # Add MathJax if not present
    if 'MathJax' not in page:
        page = page.replace('</head>', '''    <script>
        MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true
            },
            options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
        };
    </script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>''')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page)

    print(f'Generated: {output_path}')
    print(f'Content length: {len(content_html)} chars')
    print(f'TOC items: {len(toc_items)}')

    # Validation
    with open(output_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Check tables
    tables = re.findall(r'<table>.*?</table>', html, re.DOTALL)
    print(f'\nTables: {len(tables)}')
    for idx, t in enumerate(tables):
        rows = re.findall(r'<tr>.*?</tr>', t, re.DOTALL)
        if len(rows) > 1:
            first_count = len(re.findall(r'<t[dh]>', rows[0]))
            ok = True
            for r in rows[1:]:
                if len(re.findall(r'<t[dh]>', r)) != first_count:
                    print(f'  WARNING Table {idx+1}: cell count mismatch')
                    ok = False
                    break
            if ok:
                print(f'  OK Table {idx+1}: {len(rows)} rows x {first_count} cols')

    # Check math
    mb = re.findall(r'<div class="math-block">', html)
    im = re.findall(r'<span class="math-inline">', html)
    print(f'Display math blocks: {len(mb)}')
    print(f'Inline math spans: {len(im)}')

    # Check bold
    raw_bold = re.findall(r'\*\*[^*]+\*\*', html)
    print(f'Raw **bold** in output: {len(raw_bold)} (should be 0)')

    print('\nDone!')


if __name__ == '__main__':
    main()
