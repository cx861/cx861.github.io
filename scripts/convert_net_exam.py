"""Convert 计算机网络_常考题型与解法.md to network-exam-types.html."""
import re

MD = r'C:\Users\陈鑫\Desktop\过程文档\文档\计算机网络_常考题型与解法.md'
OUT = r'E:\coding\demo\docs\cs\network-exam-types.html'
REF = r'E:\coding\demo\docs\cs\os-exam-types.html'

def stl(line):
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
        cs=stl(s)
        if cs and cs[0].strip()=='': cs=cs[1:]
        if cs and cs[-1].strip()=='': cs=cs[:-1]
        rc=[pi(c.strip()) for c in cs]
        if isf: dl.append(f'<tr class="table-header">{"".join(f"<th>{c}</th>" for c in rc)}</tr>'); isf=False
        else: dl.append(f'<tr>{"".join(f"<td>{c}</td>" for c in rc)}</tr>')
    return '<div class="table-wrapper"><table>'+'\n'.join(dl)+'</table></div>'

def conv(md):
    ls=md.split('\n'); n,i=len(ls),0; ps=[]
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

def main():
    with open(MD,'r',encoding='utf-8') as f: md=f.read()
    md=ptbp(md)
    c=conv(md); c=c.replace('PIPEPROTECT','|')
    tb=re.findall(r'<table>(.*?)</table>',c,re.DOTALL)
    for i,t in enumerate(tb):
        rs=re.findall(r'<tr[^>]*>(.*?)</tr>',t,re.DOTALL)
        cs=[len(re.findall(r'<t[dh]>',r)) for r in rs if r.strip()]
        if cs and len(set(cs))>1: print(f'WARNING: Table {i+1}: {set(cs)}')
    print(f'Tables: {len(tb)} OK, Content: {len(c)} chars')

    with open(REF,'r',encoding='utf-8') as f: ref=f.read()
    cp=ref.find('<div class="content-card">')
    hd=ref[:cp+len('<div class="content-card">')]
    tl=ref[ref.find('</div>\n    </div>'):]
    hd=hd.replace('操作系统','计算机网络')
    hd=re.sub(r'<h1>.*?</h1>','<h1>🌐 计算机网络 常考题型与解法</h1>',hd)
    hd=re.sub(r'<div class="breadcrumb">.*?</div>',
        '<div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / 计算机网络</div>',hd)

    h2s=re.findall(r'<h2>(.*?)</h2>',c); toc=[]
    for h in h2s:
        cln=re.sub(r'<[^>]+>','',h); tid='s'+str(len(toc)+1)
        toc.append(f'                <li><a href="#{tid}">{cln}</a></li>')
        c=c.replace(f'<h2>{h}</h2>',f'<h2 id="{tid}">{h}</h2>',1)

    tus=hd.find('<ul>',hd.find('<div class="toc">'))
    tue=hd.find('</ul>',tus)
    if tus>=0 and tue>=0: hd=hd[:tus+4]+'\n'+'\n'.join(toc)+'\n            '+hd[tue:]

    pg=hd+'\n'+c+'\n        '+tl
    with open(OUT,'w',encoding='utf-8') as f: f.write(pg)
    print(f'Done: {OUT} ({len(pg)} chars)')

if __name__=='__main__': main()
