"""Convert 408数据结构_常考题型与解法.md to data-structure-exam-types.html."""

import re

MD_PATH = r'C:\Users\陈鑫\Desktop\过程文档\文档\408数据结构_常考题型与解法.md'
OUTPUT_PATH = r'E:\coding\demo\docs\cs\data-structure-exam-types.html'
REF_PATH = r'E:\coding\demo\docs\math\linear-algebra-exam-types.html'


def split_table_line(line):
    cells = []; current = []; i, n = 0, len(line)
    im, dm, cc = False, False, False
    while i < n:
        ch = line[i]
        if ch == '`' and not im and not dm: cc = not cc; current.append(ch); i += 1; continue
        if ch == '$' and not cc:
            if i+1<n and line[i+1]=='$': dm = not dm; current.append('$$'); i += 2; continue
            elif not dm: im = not im; current.append('$'); i += 1; continue
        if ch == '|' and not im and not dm and not cc: cells.append(''.join(current)); current = []; i += 1; continue
        current.append(ch); i += 1
    cells.append(''.join(current)); return cells


def preprocess_table_bare_pipes(text):
    lines = text.split('\n'); in_table = False; result = []
    for line in lines:
        s = line.strip()
        if s.startswith('|') and not in_table: in_table = True
        elif not s.startswith('|') and in_table: in_table = False
        if in_table and s.startswith('|') and not re.match(r'^\|[-:\s|]+\|$', s):
            line = re.sub(r'\|([A-Za-z0-9])\|', r'PIPEPROTECT\1PIPEPROTECT', line)
            line = re.sub(r'\|([A-Za-z0-9\u4e00-\u9fff\-\+]+)\|', r'PIPEPROTECT\1PIPEPROTECT', line)
        result.append(line)
    return '\n'.join(result)


def process_inline(text):
    if not text: return text
    r = text
    r = re.sub(r'(?<!\\)\$([^$]+?)(?<!\\)\$', lambda m: f'<span class="math-inline">${m.group(1)}$</span>', r)
    r = re.sub(r'`([^`]+?)`', lambda m: f'<code>{m.group(1).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</code>', r)
    r = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', r)
    return r


def process_table(table_lines):
    data_lines = []; is_first = True
    for line in table_lines:
        s = line.strip()
        if re.match(r'^\|[-:\s|]+\|$', s): continue
        cells = split_table_line(s)
        if cells and cells[0].strip()=='': cells=cells[1:]
        if cells and cells[-1].strip()=='': cells=cells[:-1]
        rc = [process_inline(c.strip()) for c in cells]
        if is_first:
            data_lines.append(f'<tr class="table-header">{"".join(f"<th>{c}</th>" for c in rc)}</tr>')
            is_first = False
        else: data_lines.append(f'<tr>{"".join(f"<td>{c}</td>" for c in rc)}</tr>')
    return '<div class="table-wrapper"><table>'+'\n'.join(data_lines)+'</table></div>'


def convert(md_content):
    lines = md_content.split('\n'); n, i = len(lines), 0
    parts = []

    while i < n:
        s = lines[i].strip()
        if s == '': i+=1; continue
        if s in ('---','***','___'): parts.append('<hr>'); i+=1; continue

        if s.startswith('```'):
            cl = []; i+=1
            while i<n and not lines[i].strip().startswith('```'):
                cl.append(lines[i]); i+=1
            if i<n: i+=1
            cc = '\n'.join(cl).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            parts.append(f'<pre><code>{cc}</code></pre>'); continue

        m = re.match(r'^(#{1,4})\s+(.+)$', s)
        if m:
            lv = len(m.group(1))
            if lv == 1: i+=1; continue
            hh = process_inline(m.group(2).strip())
            parts.append(f'<h{lv}>{hh}</h{lv}>'); i+=1; continue

        m = re.match(r'^(>\s?)(.*)', s)
        if m:
            bq = []
            while i<n and lines[i].strip().startswith('>'):
                bl = re.match(r'^(>\s?)(.*)', lines[i].strip())
                if bl: bq.append(bl.group(2))
                i+=1
            bt = '<br>'.join(bq); bt = process_inline(bt)
            parts.append(f'<blockquote>{bt}</blockquote>'); continue

        if s.startswith('|') and i+1<n and re.match(r'^\s*\|[-:\s|]+\|\s*$', lines[i+1]):
            tl = []
            while i<n and lines[i].strip().startswith('|'): tl.append(lines[i]); i+=1
            parts.append(process_table(tl)); continue

        m = re.match(r'^(\d+)\.\s+(.+)$', s)
        if m:
            li = []
            while i<n and re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()):
                it = re.match(r'^(\d+)\.\s+(.+)$', lines[i].strip()).group(2)
                nested = ''; i+=1
                if i<n and lines[i].strip().startswith('- '):
                    sub = []
                    while i<n and lines[i].strip().startswith('- '):
                        sub.append(f'<li>{process_inline(lines[i].strip()[2:])}</li>'); i+=1
                    nested = '<ul>'+''.join(sub)+'</ul>'
                li.append(f'<li>{process_inline(it)}{nested}</li>')
            parts.append('<ol>'+'\n'.join(li)+'</ol>'); continue

        if s.startswith('- ') or s.startswith('* '):
            mk = s[0]; li = []
            while i<n and lines[i].strip().startswith(f'{mk} '):
                li.append(f'<li>{process_inline(lines[i].strip()[2:])}</li>'); i+=1
            parts.append('<ul>'+'\n'.join(li)+'</ul>'); continue

        if s.startswith('$$'):
            if s.endswith('$$') and len(s)>4:
                parts.append(f'<div class="math-block">$${s[2:-2].strip()}$$</div>'); i+=1; continue
            else:
                ml=[s]; i+=1
                while i<n:
                    ls=lines[i].strip(); ml.append(ls)
                    if ls.endswith('$$'): break
                    i+=1
                am='\n'.join(ml)
                if am.startswith('$$'): am=am[2:]
                if am.endswith('$$'): am=am[:-2]
                parts.append(f'<div class="math-block">$${am.strip()}$$</div>'); i+=1; continue

        parts.append(f'<p>{process_inline(s)}</p>'); i+=1

    return '\n'.join(parts)


def validate(html):
    for i,b in enumerate(re.findall(r'\$\$(.*?)\$\$', html, re.DOTALL)):
        o,c = b.count('{'), b.count('}')
        if o!=c: print(f'WARNING: Block {i+1}: {{{o}, }}{c}')
    tb = re.findall(r'<table>(.*?)</table>', html, re.DOTALL)
    for i,t in enumerate(tb):
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
        cols = [len(re.findall(r'<t[dh]>', r)) for r in rows if r.strip()]
        if cols and len(set(cols))>1: print(f'WARNING: Table {i+1}: cols vary {set(cols)}')
    print(f'Tables checked: {len(tb)}')


def main():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md = f.read()
    md = preprocess_table_bare_pipes(md)
    content = convert(md)
    content = content.replace('PIPEPROTECT', '|')
    print(f'Content: {len(content)} chars')
    validate(content)

    # Build page title from h2
    h2s = re.findall(r'<h2>(.*?)</h2>', content)
    print(f'Sections: {", ".join(re.sub(r"<[^>]+>","",h)[:15] for h in h2s[:5])}...')

    # Build full page using reference template
    with open(REF_PATH, 'r', encoding='utf-8') as f:
        ref = f.read()

    # Extract template structure (before content-card)
    card_pos = ref.find('<div class="content-card">')
    template_head = ref[:card_pos + len('<div class="content-card">')]
    # After content-card close
    card_close = ref.find('</div>\n    </div>')
    template_tail = ref[card_close:]

    # Customize for CS
    template_head = template_head.replace('数学习题', '计算机')
    # Update nav active
    template_head = template_head.replace('数学</a>', '计算机</a>')
    # Update page-header
    template_head = re.sub(
        r'<div class="page-header math">',
        '<div class="page-header cs">',
        template_head
    )
    template_head = re.sub(
        r'<h1>.*?</h1>',
        '<h1>🗃️ 数据结构 常考题型与解法</h1>',
        template_head
    )
    template_head = re.sub(
        r'<div class="breadcrumb">.*?</div>',
        '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / 数据结构</div>',
        template_head
    )
    # CSS path
    template_head = template_head.replace('../assets/css/style.css', '../assets/css/style.css')
    template_head = template_head.replace('../assets/js/main.js', '../assets/js/main.js')

    # Build TOC from h2 sections
    h2_full = re.findall(r'<h2>(.*?)</h2>', content)
    toc_items = []
    for h in h2_full:
        clean = re.sub(r'<[^>]+>', '', h)
        tid = 's'+str(len(toc_items)+1)
        toc_items.append(f'                <li><a href="#{tid}">{clean}</a></li>')
        # Replace h2 with id
        content = content.replace(f'<h2>{h}</h2>', f'<h2 id="{tid}">{h}</h2>', 1)

    toc_html = '\n'.join(toc_items)

    # Replace TOC
    tus = template_head.find('<ul>', template_head.find('<div class="toc">'))
    tue = template_head.find('</ul>', tus)
    if tus>=0 and tue>=0:
        template_head = template_head[:tus+4] + '\n' + toc_html + '\n            ' + template_head[tue:]

    page = template_head + '\n' + content + '\n        ' + template_tail
    page = page.replace('🧮', '🗃️')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'Done: {OUTPUT_PATH} ({len(page)} chars)')


if __name__ == '__main__':
    main()
