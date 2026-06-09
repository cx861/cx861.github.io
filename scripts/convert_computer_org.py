"""Convert 计算机组成原理_按章节知识点.md to computer-organization.html.

Handles: tables with 6-7 columns, code blocks (```), inline code (`...`),
LaTeX math ($...$ and $$...$$), blockquotes, lists, headings.
"""

import re

MD_PATH = r'C:\Users\陈鑫\Desktop\过程文档\文档\计算机组成原理_按章节知识点.md'
HTML_PATH = r'E:\coding\demo\docs\cs\computer-organization.html'


# ============================================================
# Math-aware table splitter (same as data-structure converter)
# ============================================================
def split_table_line(line):
    """Split a markdown table line by |, but NOT inside $...$ or $$...$$."""
    cells = []
    current = []
    i, n = 0, len(line)
    in_inline_math, in_display_math = False, False

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


# ============================================================
# Preprocess: protect bare |X| patterns in table rows
# ============================================================
def preprocess_table_bare_pipes(text):
    """Protect bare |X| set/absolute-value notation from pipe splitting."""
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
                # Protect single-letter |X|
                line = re.sub(r'\|([A-Za-z0-9])\|', r'PIPEPROTECT\1PIPEPROTECT', line)
                # Protect short math-like |expr|
                line = re.sub(r'\|([A-Za-z0-9\u4e00-\u9fff\-\+]+)\|', r'PIPEPROTECT\1PIPEPROTECT', line)
        result.append(line)
    return '\n'.join(result)


def postprocess_pipeprotect(text):
    """Restore PIPEPROTECT back to |X|."""
    return text.replace('PIPEPROTECT', '|')


# ============================================================
# Inline processing
# ============================================================
def process_inline(text):
    """Process inline Markdown: **bold**, `code`, $math$."""
    if not text:
        return text

    result = text

    # Inline math $...$ (do before bold to avoid conflicts)
    def math_replace(m):
        math_content = m.group(1)
        # Skip if inside code
        return f'<span class="math-inline">${math_content}$</span>'

    result = re.sub(r'(?<!\\)\$([^$]+?)(?<!\\)\$', math_replace, result)

    # Inline code `...`
    def code_replace(m):
        code_content = m.group(1)
        # Escape HTML entities
        code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<code>{code_content}</code>'

    result = re.sub(r'`([^`]+?)`', code_replace, result)

    # Bold **...**
    result = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', result)

    # Emoji/unicode superscripts are fine as-is

    return result


# ============================================================
# Table processing
# ============================================================
def process_table(table_lines):
    """Process a markdown table into HTML <table>."""
    data_lines = []
    is_first = True
    column_count = None

    for line in table_lines:
        stripped = line.strip()
        if re.match(r'^\|[-:\s|]+\|$', stripped):
            continue

        cells = split_table_line(stripped)
        if cells and cells[0].strip() == '':
            cells = cells[1:]
        if cells and cells[-1].strip() == '':
            cells = cells[:-1]

        if column_count is None:
            column_count = len(cells)

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


# ============================================================
# Main converter
# ============================================================
def convert_md_to_html(md_content):
    """Convert markdown content to HTML, return (html, toc_items)."""
    lines = md_content.split('\n')
    n = len(lines)
    i = 0
    content_parts = []
    toc_items = []
    ch_counter = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # --- Empty line ---
        if stripped == '':
            i += 1
            continue

        # --- Horizontal rule ---
        if stripped == '---' or stripped == '***' or stripped == '___':
            content_parts.append('<hr>')
            i += 1
            continue

        # --- Code block (```...```) ---
        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1  # skip closing ```
            code_content = '\n'.join(code_lines)
            # Escape HTML entities
            code_content = code_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            content_parts.append(f'<pre><code>{code_content}</code></pre>')
            continue

        # --- Heading ---
        m = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m:
            sharp_count = len(m.group(1))
            if sharp_count == 1:
                i += 1
                continue
            level = sharp_count
            heading_text = m.group(2).strip()
            heading_text_html = process_inline(heading_text)

            if level == 2:
                ch_counter += 1
                ch_id = f'ch{ch_counter}'
                # Extract clean title for TOC
                clean_title = re.sub(r'<[^>]+>', '', heading_text_html)
                toc_items.append(f'                <li><a href="#{ch_id}">{clean_title}</a></li>')
                content_parts.append(f'<h2 id="{ch_id}">{heading_text_html}</h2>')
            else:
                content_parts.append(f'<h{level}>{heading_text_html}</h{level}>')
            i += 1
            continue

        # --- Blockquote ---
        m = re.match(r'^(>\s?)(.*)', stripped)
        if m:
            bq_lines = []
            while i < n and lines[i].strip().startswith('>'):
                bq_line = re.match(r'^(>\s?)(.*)', lines[i].strip())
                if bq_line:
                    bq_lines.append(bq_line.group(2))
                i += 1
            bq_text = '\n'.join(bq_lines)
            # Process bold, code, math inside blockquote
            bq_text = process_inline(bq_text)
            # Handle line breaks
            bq_text = bq_text.replace('\n', '<br>')
            content_parts.append(f'<blockquote>{bq_text}</blockquote>')
            continue

        # --- Table ---
        if stripped.startswith('|') and i + 1 < n and re.match(r'^\s*\|[-:\s|]+\|\s*$', lines[i + 1]):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            table_html = process_table(table_lines)
            content_parts.append(table_html)
            continue

        # --- Ordered list ---
        m = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m:
            list_items = []
            while i < n and re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()):
                item_text = re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()).group(2)
                # Check for nested sub-list in next lines
                nested_html = ''
                i += 1
                if i < n and lines[i].strip().startswith('- '):
                    sub_items = []
                    while i < n and lines[i].strip().startswith('- '):
                        sub_text = lines[i].strip()[2:]
                        sub_items.append(f'<li>{process_inline(sub_text)}</li>')
                        i += 1
                    nested_html = '<ul>' + ''.join(sub_items) + '</ul>'

                item_html = process_inline(item_text)
                list_items.append(f'<li>{item_html}{nested_html}</li>')
            content_parts.append('<ol>' + '\n'.join(list_items) + '</ol>')
            continue

        # --- Unordered list ---
        if stripped.startswith('- ') or stripped.startswith('* '):
            list_items = []
            marker = stripped[0]
            while i < n and lines[i].strip().startswith(f'{marker} '):
                item_text = lines[i].strip()[2:]
                list_items.append(f'<li>{process_inline(item_text)}</li>')
                i += 1
            content_parts.append('<ul>' + '\n'.join(list_items) + '</ul>')
            continue

        # --- Display math block ($$...$$) ---
        if stripped.startswith('$$'):
            if stripped.endswith('$$') and len(stripped) > 4:
                math_expr = stripped[2:-2].strip()
                content_parts.append(f'<div class="math-block">$${math_expr}$$</div>')
                i += 1
                continue
            else:
                math_lines = [stripped]
                i += 1
                while i < n:
                    ls = lines[i].strip()
                    math_lines.append(ls)
                    if ls.endswith('$$'):
                        break
                    i += 1
                all_math = '\n'.join(math_lines)
                if all_math.startswith('$$'):
                    all_math = all_math[2:]
                if all_math.endswith('$$'):
                    all_math = all_math[:-2]
                content_parts.append(f'<div class="math-block">$${all_math.strip()}$$</div>')
                i += 1
                continue

        # --- Regular paragraph ---
        # Skip processing if this line was already consumed by a sub-list
        para_html = process_inline(stripped)
        content_parts.append(f'<p>{para_html}</p>')
        i += 1

    return '\n'.join(content_parts), toc_items


# ============================================================
# Validation
# ============================================================
def validate(content_html):
    """Run all safety checks on the generated HTML."""
    errors = []

    # 1. Brace matching in $$ blocks
    math_blocks = re.findall(r'\$\$(.*?)\$\$', content_html, re.DOTALL)
    for idx, block in enumerate(math_blocks):
        opens = block.count('{')
        closes = block.count('}')
        if opens != closes:
            errors.append(f'  Block {idx+1}: {{ = {opens}, }} = {closes}')

    if errors:
        print('WARNING: Brace mismatches in $$ blocks:')
        for e in errors:
            print(e)
    else:
        print('OK: All $$ blocks have matching braces')

    # 2. Check \begin...\end pairing
    begins = len(re.findall(r'\\begin\{', content_html))
    ends = len(re.findall(r'\\end\{', content_html))
    if begins != ends:
        print(f'WARNING: \\begin ({begins}) != \\end ({ends})')
    else:
        print(f'OK: \\begin/\\end paired ({begins} pairs)')

    # 3. Check for raw markdown
    raw_h2 = len(re.findall(r'(?<!\<)##\s', content_html))
    raw_hr = len(re.findall(r'(?<!\<)---\s*\n', content_html))
    if raw_h2 > 10:
        print(f'WARNING: {raw_h2} naked ## headings detected')
    if raw_hr:
        print(f'WARNING: {raw_hr} naked --- detected')
    if raw_h2 <= 10 and not raw_hr:
        print('OK: No significant raw markdown')

    # 4. Check HTML in $$ blocks
    for idx, block in enumerate(math_blocks):
        if re.search(r'<\w+[^>]*>', block):
            print(f'WARNING: Block {idx+1} contains HTML tags')

    # 5. Check table column consistency
    tables = re.findall(r'<table>(.*?)</table>', content_html, re.DOTALL)
    for idx, table in enumerate(tables):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)
        cols_per_row = []
        for row in rows:
            cols = re.findall(r'<t[dh]>', row)
            cols_per_row.append(len(cols))
        if cols_per_row:
            if len(set(cols_per_row)) > 1:
                print(f'WARNING: Table {idx+1} has inconsistent columns: {set(cols_per_row)}')
        else:
            # Table with no data rows - count from header
            pass


# ============================================================
# Main
# ============================================================
def main():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Preprocess
    md_content = preprocess_table_bare_pipes(md_content)

    # Convert
    content_html, toc_items = convert_md_to_html(md_content)

    # Postprocess
    content_html = postprocess_pipeprotect(content_html)

    print(f'Conversion done: {len(content_html)} chars of content')
    print(f'TOC items: {len(toc_items)}')

    # Validate
    print('\n--- Validation ---')
    validate(content_html)

    # Count elements
    h2_count = len(re.findall(r'<h2 ', content_html))
    h3_count = len(re.findall(r'<h3>', content_html))
    h4_count = len(re.findall(r'<h4>', content_html))
    table_count = len(re.findall(r'<table>', content_html))
    math_block_count = len(re.findall(r'math-block', content_html))
    math_inline_count = len(re.findall(r'math-inline', content_html))
    code_blocks = len(re.findall(r'<pre><code>', content_html))
    blockquote_count = len(re.findall(r'<blockquote>', content_html))
    ol_count = len(re.findall(r'<ol>', content_html))
    ul_count = len(re.findall(r'<ul>', content_html))

    print(f'\n--- Statistics ---')
    print(f'h2: {h2_count}, h3: {h3_count}, h4: {h4_count}')
    print(f'Tables: {table_count}')
    print(f'Math blocks: {math_block_count}, inline math: {math_inline_count}')
    print(f'Code blocks: {code_blocks}')
    print(f'Blockquotes: {blockquote_count}')
    print(f'Ordered lists: {ol_count}, Unordered lists: {ul_count}')

    # Build TOC
    toc_html = '\n'.join(toc_items)

    # Read template
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        page = f.read()

    # Replace content-card content
    card_start = page.find('<div class="content-card">')
    end_marker = '</div>\n    </div>'
    if card_start >= 0:
        search_start = card_start + len('<div class="content-card">')
        end_idx = page.find(end_marker, search_start)
        if end_idx >= 0:
            new_page = (
                page[:card_start + len('<div class="content-card">')]
                + '\n'
                + content_html
                + '\n        '
                + page[end_idx:]
            )
        else:
            print("ERROR: Could not find content-card closing pattern!")
            return
    else:
        print("ERROR: content-card not found!")
        return

    # Replace TOC
    toc_start = new_page.find('<div class="toc">')
    toc_end = new_page.find('</div>', new_page.find('<div class="content-card">'))
    if toc_start >= 0 and toc_end >= 0:
        # Find the TOC's </ul> to insert new items
        toc_ul_start = new_page.find('<ul>', toc_start)
        toc_ul_end = new_page.find('</ul>', toc_ul_start)
        if toc_ul_start >= 0 and toc_ul_end >= 0:
            before = new_page[:toc_ul_start + 4]
            after = new_page[toc_ul_end:]
            new_page = before + '\n' + toc_html + '\n            ' + after

    # Update page-header title
    new_page = new_page.replace(
        '>计算机组成原理</h1>',
        '>计算机组成原理</h1>'
    )

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_page)

    print(f'\nDone! Wrote {len(new_page)} chars to {HTML_PATH}')


if __name__ == '__main__':
    main()
