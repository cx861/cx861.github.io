"""Convert 计算机网络_按章节知识点.md to computer-network.html."""

import re

MD_PATH = r'C:\Users\陈鑫\Desktop\过程文档\文档\计算机网络_按章节知识点.md'
HTML_PATH = r'E:\coding\demo\docs\cs\computer-network.html'


def split_table_line(line):
    cells = []
    current = []
    i, n = 0, len(line)
    in_inline_math, in_display_math, in_code = False, False, False
    while i < n:
        ch = line[i]
        if ch == '`' and not in_inline_math and not in_display_math:
            in_code = not in_code
            current.append(ch)
            i += 1; continue
        if ch == '$' and not in_code:
            if i + 1 < n and line[i + 1] == '$':
                in_display_math = not in_display_math
                current.append('$$')
                i += 2; continue
            elif not in_display_math:
                in_inline_math = not in_inline_math
                current.append('$')
                i += 1; continue
        if ch == '|' and not in_inline_math and not in_display_math and not in_code:
            cells.append(''.join(current))
            current = []
            i += 1; continue
        current.append(ch)
        i += 1
    cells.append(''.join(current))
    return cells


def preprocess_table_bare_pipes(text):
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
                line = re.sub(r'\|([A-Za-z0-9])\|', r'PIPEPROTECT\1PIPEPROTECT', line)
                line = re.sub(r'\|([A-Za-z0-9\u4e00-\u9fff\-\+]+)\|', r'PIPEPROTECT\1PIPEPROTECT', line)
        result.append(line)
    return '\n'.join(result)


def process_inline(text):
    if not text: return text
    result = text
    def math_replace(m):
        return f'<span class="math-inline">${m.group(1)}$</span>'
    result = re.sub(r'(?<!\\)\$([^$]+?)(?<!\\)\$', math_replace, result)
    def code_replace(m):
        c = m.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<code>{c}</code>'
    result = re.sub(r'`([^`]+?)`', code_replace, result)
    result = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', result)
    return result


def process_table(table_lines):
    data_lines = []
    is_first = True
    for line in table_lines:
        stripped = line.strip()
        if re.match(r'^\|[-:\s|]+\|$', stripped): continue
        cells = split_table_line(stripped)
        if cells and cells[0].strip() == '': cells = cells[1:]
        if cells and cells[-1].strip() == '': cells = cells[:-1]
        row_cells = [process_inline(c.strip()) for c in cells]
        if is_first:
            data_lines.append(f'<tr class="table-header">{"".join(f"<th>{c}</th>" for c in row_cells)}</tr>')
            is_first = False
        else:
            data_lines.append(f'<tr>{"".join(f"<td>{c}</td>" for c in row_cells)}</tr>')
    return '<div class="table-wrapper"><table>' + '\n'.join(data_lines) + '</table></div>'


def convert_md_to_html(md_content):
    lines = md_content.split('\n')
    n, i = len(lines), 0
    content_parts, toc_items = [], []
    ch_counter = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped == '':
            i += 1; continue
        if stripped in ('---', '***', '___'):
            content_parts.append('<hr>')
            i += 1; continue

        # Code block
        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i]); i += 1
            if i < n: i += 1
            cc = '\n'.join(code_lines).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            content_parts.append(f'<pre><code>{cc}</code></pre>')
            continue

        # Heading
        m = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if m:
            sharp = len(m.group(1))
            if sharp == 1: i += 1; continue
            level = sharp
            hh = process_inline(m.group(2).strip())
            if level == 2:
                ch_counter += 1
                clean = re.sub(r'<[^>]+>', '', hh)
                toc_items.append(f'                <li><a href="#ch{ch_counter}">{clean}</a></li>')
                content_parts.append(f'<h2 id="ch{ch_counter}">{hh}</h2>')
            else:
                content_parts.append(f'<h{level}>{hh}</h{level}>')
            i += 1; continue

        # Blockquote
        m = re.match(r'^(>\s?)(.*)', stripped)
        if m:
            bq_lines = []
            while i < n and lines[i].strip().startswith('>'):
                bl = re.match(r'^(>\s?)(.*)', lines[i].strip())
                if bl: bq_lines.append(bl.group(2))
                i += 1
            bq_text = '<br>'.join(bq_lines)
            bq_text = process_inline(bq_text)
            content_parts.append(f'<blockquote>{bq_text}</blockquote>')
            continue

        # Table
        if stripped.startswith('|') and i + 1 < n and re.match(r'^\s*\|[-:\s|]+\|\s*$', lines[i + 1]):
            table_lines = []
            while i < n and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]); i += 1
            content_parts.append(process_table(table_lines))
            continue

        # Ordered list
        m = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if m:
            list_items = []
            while i < n and re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()):
                item_text = re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()).group(2)
                nested = ''
                i += 1
                if i < n and lines[i].strip().startswith('- '):
                    sub = []
                    while i < n and lines[i].strip().startswith('- '):
                        sub.append(f'<li>{process_inline(lines[i].strip()[2:])}</li>'); i += 1
                    nested = '<ul>' + ''.join(sub) + '</ul>'
                list_items.append(f'<li>{process_inline(item_text)}{nested}</li>')
            content_parts.append('<ol>' + '\n'.join(list_items) + '</ol>')
            continue

        # Unordered list
        if stripped.startswith('- ') or stripped.startswith('* '):
            marker = stripped[0]
            list_items = []
            while i < n and lines[i].strip().startswith(f'{marker} '):
                list_items.append(f'<li>{process_inline(lines[i].strip()[2:])}</li>'); i += 1
            content_parts.append('<ul>' + '\n'.join(list_items) + '</ul>')
            continue

        # Display math
        if stripped.startswith('$$'):
            if stripped.endswith('$$') and len(stripped) > 4:
                content_parts.append(f'<div class="math-block">$${stripped[2:-2].strip()}$$</div>')
                i += 1; continue
            else:
                math_lines = [stripped]; i += 1
                while i < n:
                    ls = lines[i].strip(); math_lines.append(ls)
                    if ls.endswith('$$'): break
                    i += 1
                all_math = '\n'.join(math_lines)
                if all_math.startswith('$$'): all_math = all_math[2:]
                if all_math.endswith('$$'): all_math = all_math[:-2]
                content_parts.append(f'<div class="math-block">$${all_math.strip()}$$</div>')
                i += 1; continue

        # Regular paragraph
        content_parts.append(f'<p>{process_inline(stripped)}</p>')
        i += 1

    return '\n'.join(content_parts), toc_items


def validate(content_html):
    errors = []
    for idx, block in enumerate(re.findall(r'\$\$(.*?)\$\$', content_html, re.DOTALL)):
        o, c = block.count('{'), block.count('}')
        if o != c: errors.append(f'Block {idx+1}: {{={o}, }}={c}')
    if errors:
        for e in errors: print(f'WARNING: {e}')
    else:
        print('OK: All $$ blocks have matching braces')
    b, e = len(re.findall(r'\\begin\{', content_html)), len(re.findall(r'\\end\{', content_html))
    print(f'OK: \\begin/\\end: {b}/{e}' if b == e else f'WARNING: \\begin({b}) != \\end({e})')
    tables = re.findall(r'<table>(.*?)</table>', content_html, re.DOTALL)
    for idx, t in enumerate(tables):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        cols = [len(re.findall(r'<t[dh]>', r)) for r in rows if r.strip()]
        if cols and len(set(cols)) > 1:
            print(f'WARNING: Table {idx+1}: cols vary {set(cols)}')


def main():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_content = f.read()

    md_content = preprocess_table_bare_pipes(md_content)
    content_html, toc_items = convert_md_to_html(md_content)
    content_html = content_html.replace('PIPEPROTECT', '|')

    print(f'Conversion done: {len(content_html)} chars')
    print(f'TOC items: {len(toc_items)}')
    print('\n--- Validation ---')
    validate(content_html)

    h2s = len(re.findall(r'<h2 ', content_html))
    tables = len(re.findall(r'<table>', content_html))
    cbs = len(re.findall(r'<pre><code>', content_html))
    bqs = len(re.findall(r'<blockquote>', content_html))
    print(f'\n--- Stats ---')
    print(f'h2:{h2s} tables:{tables} code-blocks:{cbs} blockquotes:{bqs}')

    toc_html = '\n'.join(toc_items)

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        page = f.read()

    card_start = page.find('<div class="content-card">')
    end_marker = '</div>\n    </div>'
    if card_start >= 0:
        search_start = card_start + len('<div class="content-card">')
        end_idx = page.find(end_marker, search_start)
        if end_idx >= 0:
            new_page = (page[:card_start + len('<div class="content-card">')]
                        + '\n' + content_html + '\n        ' + page[end_idx:])
        else: print("ERROR: end marker"); return
    else: print("ERROR: content-card"); return

    # TOC
    toc_ul = new_page.find('<div class="toc">')
    if toc_ul >= 0:
        us = new_page.find('<ul>', toc_ul)
        ue = new_page.find('</ul>', us)
        if us >= 0 and ue >= 0:
            new_page = new_page[:us + 4] + '\n' + toc_html + '\n            ' + new_page[ue:]

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_page)
    print(f'\nDone! Wrote {len(new_page)} chars')


if __name__ == '__main__':
    main()
