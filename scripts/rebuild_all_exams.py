"""Rebuild all exam-type pages with correct template extraction."""
import re, os

CS_ROOT = r'E:\coding\demo\docs\cs'
CLEAN_REF = r'E:\coding\demo\docs\math\linear-algebra-exam-types.html'

# Shared converter functions
def split_table_line(line):
    cells=[]; cur=[]; i,n=0,len(line); im=dm=cc=False
    while i<n:
        ch=line[i]
        if ch=='`' and not im and not dm: cc=not cc; cur.append(ch); i+=1; continue
        if ch=='$' and not cc:
            if i+1<n and line[i+1]=='$': dm=not dm; cur.append('$$'); i+=2; continue
            elif not dm: im=not im; cur.append('$'); i+=1; continue
        if ch=='|' and not im and not dm and not cc: cells.append(''.join(cur)); cur=[]; i+=1; continue
        cur.append(ch); i+=1
    cells.append(''.join(cur)); return cells

def ptbp(text):
    lines=text.split('\n'); it=False; res=[]
    for l in lines:
        s=l.strip()
        if s.startswith('|') and not it: it=True
        elif not s.startswith('|') and it: it=False
        if it and s.startswith('|') and not re.match(r'^\|[-:\s|]+\|$',s):
            l=re.sub(r'\|([A-Za-z0-9])\|',r'PIPEPROTECT\1PIPEPROTECT',l)
            l=re.sub(r'\|([A-Za-z0-9\u4e00-\u9fff\-\+]+)\|',r'PIPEPROTECT\1PIPEPROTECT',l)
        res.append(l)
    return '\n'.join(res)

def pi(text):
    if not text: return text
    r=text
    r=re.sub(r'(?<!\\)\$([^$]+?)(?<!\\)\$',lambda m:f'<span class="math-inline">${m.group(1)}$</span>',r)
    r=re.sub(r'`([^`]+?)`',lambda m:f'<code>{m.group(1).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</code>',r)
    r=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',r)
    return r

def pt(tl):
    dl=[]; isf=True
    for l in tl:
        s=l.strip()
        if re.match(r'^\|[-:\s|]+\|$',s): continue
        cs=split_table_line(s)
        if cs and cs[0].strip()=='': cs=cs[1:]
        if cs and cs[-1].strip()=='': cs=cs[:-1]
        rc=[pi(c.strip()) for c in cs]
        if isf: dl.append(f'<tr class="table-header">{"".join(f"<th>{c}</th>" for c in rc)}</tr>'); isf=False
        else: dl.append(f'<tr>{"".join(f"<td>{c}</td>" for c in rc)}</tr>')
    return '<div class="table-wrapper"><table>'+'\n'.join(dl)+'</table></div>'

def convert(md_content):
    ls=md_content.split('\n'); n,i=len(ls),0; ps=[]
    while i<n:
        s=ls[i].strip()
        if s=='': i+=1; continue
        if s in('---','***','___'): ps.append('<hr>'); i+=1; continue
        if s.startswith('```'):
            cl=[]; i+=1
            while i<n and not ls[i].strip().startswith('```'): cl.append(ls[i]); i+=1
            if i<n: i+=1
            cc='\n'.join(cl).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
            ps.append(f'<pre><code>{cc}</code></pre>'); continue
        m=re.match(r'^(#{1,4})\s+(.+)$',s)
        if m:
            lv=len(m.group(1))
            if lv==1: i+=1; continue
            ps.append(f'<h{lv}>{pi(m.group(2).strip())}</h{lv}>'); i+=1; continue
        m=re.match(r'^(>\s?)(.*)',s)
        if m:
            bq=[]
            while i<n and ls[i].strip().startswith('>'):
                bl=re.match(r'^(>\s?)(.*)',ls[i].strip())
                if bl: bq.append(bl.group(2)); i+=1
            bt='<br>'.join(bq); bt=pi(bt)
            ps.append(f'<blockquote>{bt}</blockquote>'); continue
        if s.startswith('|') and i+1<n and re.match(r'^\s*\|[-:\s|]+\|\s*$',ls[i+1]):
            tl=[]
            while i<n and ls[i].strip().startswith('|'): tl.append(ls[i]); i+=1
            ps.append(pt(tl)); continue
        m=re.match(r'^(\d+)\.\s+(.+)$',s)
        if m:
            li=[]
            while i<n and re.match(r'^(\d+)\.\s+(.+)$',ls[i].strip()):
                it=re.match(r'^(\d+)\.\s+(.+)$',ls[i].strip()).group(2); nested=''; i+=1
                if i<n and ls[i].strip().startswith('- '):
                    sub=[]
                    while i<n and ls[i].strip().startswith('- '): sub.append(f'<li>{pi(ls[i].strip()[2:])}</li>'); i+=1
                    nested='<ul>'+''.join(sub)+'</ul>'
                li.append(f'<li>{pi(it)}{nested}</li>')
            ps.append('<ol>'+'\n'.join(li)+'</ol>'); continue
        if s.startswith('- ') or s.startswith('* '):
            mk=s[0]; li=[]
            while i<n and ls[i].strip().startswith(f'{mk} '): li.append(f'<li>{pi(ls[i].strip()[2:])}</li>'); i+=1
            ps.append('<ul>'+'\n'.join(li)+'</ul>'); continue
        if s.startswith('$$'):
            if s.endswith('$$') and len(s)>4: ps.append(f'<div class="math-block">$${s[2:-2].strip()}$$</div>'); i+=1; continue
            else:
                ml=[s]; i+=1
                while i<n:
                    lx=ls[i].strip(); ml.append(lx)
                    if lx.endswith('$$'): break; i+=1
                am='\n'.join(ml)
                if am.startswith('$$'): am=am[2:]
                if am.endswith('$$'): am=am[:-2]
                ps.append(f'<div class="math-block">$${am.strip()}$$</div>'); i+=1; continue
        ps.append(f'<p>{pi(s)}</p>'); i+=1
    return '\n'.join(ps)


def build_page(md_path, output_path, title_emoji, title_text, breadcrumb, page_header_class='cs'):
    """Build a clean exam-type page with correct template boundaries."""
    with open(md_path, 'r', encoding='utf-8') as f:
        md = f.read()
    md = ptbp(md)
    content = convert(md)
    content = content.replace('PIPEPROTECT', '|')

    # Validate tables
    tb = re.findall(r'<table>(.*?)</table>', content, re.DOTALL)
    for i,t in enumerate(tb):
        rs=re.findall(r'<tr[^>]*>(.*?)</tr>',t,re.DOTALL)
        cs=[len(re.findall(r'<t[dh]>',r)) for r in rs if r.strip()]
        if cs and len(set(cs))>1: print(f'  WARNING: Table {i+1}: cols vary {set(cs)}')

    # Read clean reference template
    with open(CLEAN_REF, 'r', encoding='utf-8') as f:
        ref = f.read()

    # Extract head (everything up to and including content-card opening)
    card_open = ref.find('<div class="content-card">')
    head = ref[:card_open + len('<div class="content-card">')]

    # Extract tail (from site-footer onwards) - use site-footer as anchor
    footer_start = ref.find('<div class="site-footer">')
    tail = ref[footer_start - 14:]  # "        </div>\n    </div>\n\n    <div class=\"site-footer\">"
    # Actually let's be more precise
    # The structure is:
    #         </div>  (closes content-card)
    #     </div>      (closes container)
    # 
    #     <div class="site-footer">
    # Find the closing of content-card: search for the </div> right before the container's </div>
    # Better: search from site-footer backwards
    container_close = ref.rfind('</div>', 0, footer_start)
    # Then find the content-card close (the </div> before container_close)
    card_close = ref.rfind('</div>', 0, container_close)
    # Now extract the proper tail
    tail = ref[card_close:]

    # Customize head
    head = re.sub(r'<div class="page-header math">', f'<div class="page-header {page_header_class}">', head)
    head = re.sub(r'<h1>.*?</h1>', f'<h1>{title_emoji} {title_text} 常考题型与解法</h1>', head)
    head = re.sub(r'<div class="breadcrumb">.*?</div>',
        f'<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / {breadcrumb}</div>',
        head)

    # Build TOC from h2 sections
    h2s = re.findall(r'<h2>(.*?)</h2>', content)
    toc = []
    for h in h2s:
        cln = re.sub(r'<[^>]+>', '', h)
        tid = 's'+str(len(toc)+1)
        toc.append(f'                <li><a href="#{tid}">{cln}</a></li>')
        content = content.replace(f'<h2>{h}</h2>', f'<h2 id="{tid}">{h}</h2>', 1)

    # Replace TOC in head
    tus = head.find('<ul>', head.find('<div class="toc">'))
    tue = head.find('</ul>', tus)
    if tus>=0 and tue>=0:
        head = head[:tus+4] + '\n' + '\n'.join(toc) + '\n            ' + head[tue:]

    # Assemble
    page = head + '\n' + content + '\n        ' + tail

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page)

    return len(page), len(tb)


# Define the 4 pages
pages = [
    {
        'md': r'C:\Users\陈鑫\Desktop\过程文档\文档\408数据结构_常考题型与解法.md',
        'out': r'E:\coding\demo\docs\cs\data-structure-exam-types.html',
        'emoji': '🗃\uFE0F',
        'title': '数据结构',
        'breadcrumb': '数据结构',
    },
    {
        'md': r'C:\Users\陈鑫\Desktop\过程文档\文档\计算机组成原理_常考题型与解法.md',
        'out': r'E:\coding\demo\docs\cs\computer-org-exam-types.html',
        'emoji': '⚙\uFE0F',
        'title': '计算机组成原理',
        'breadcrumb': '计算机组成原理',
    },
    {
        'md': r'C:\Users\陈鑫\Desktop\过程文档\文档\操作系统_常考题型与解法.md',
        'out': r'E:\coding\demo\docs\cs\os-exam-types.html',
        'emoji': '💾',
        'title': '操作系统',
        'breadcrumb': '操作系统',
    },
    {
        'md': r'C:\Users\陈鑫\Desktop\过程文档\文档\计算机网络_常考题型与解法.md',
        'out': r'E:\coding\demo\docs\cs\network-exam-types.html',
        'emoji': '🌐',
        'title': '计算机网络',
        'breadcrumb': '计算机网络',
    },
]

print("Rebuilding all exam-type pages...\n")
for p in pages:
    size, tables = build_page(**{k:v for k,v in p.items() if k!='md' and k!='out' and k!='emoji' and k!='title' and k!='breadcrumb'},
        md_path=p['md'], output_path=p['out'],
        title_emoji=p['emoji'], title_text=p['title'], breadcrumb=p['breadcrumb'])
    fname = os.path.basename(p['out'])
    # Count h2s
    with open(p['out'], 'r', encoding='utf-8') as f:
        h2c = len(re.findall(r'<h2[ >]', f.read()))
    print(f'  {fname}: {size:,} chars, {tables} tables, {h2c} sections')

# Final verification
print("\n--- Final check ---")
for p in pages:
    fname = os.path.basename(p['out'])
    with open(p['out'], 'r', encoding='utf-8') as f:
        html = f.read()
    h2c = len(re.findall(r'<h2[ >]', html))
    # Check for cross-contamination
    others = [x['title'] for x in pages if x['title'] != p['title']]
    contamination = [o for o in others if o in html]
    if h2c > 25:
        print(f'  {fname}: WARNING {h2c} h2s (possible contamination)')
    elif contamination:
        print(f'  {fname}: WARNING contains {contamination}')
    else:
        print(f'  {fname}: CLEAN ({h2c} sections)')
