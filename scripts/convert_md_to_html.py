import re
import sys

def convert_md_to_html(md_text):
    lines = md_text.split('\n')
    result = []
    i = 0
    chapter_num = 0
    
    def process_inline(text):
        """Process inline markdown elements: bold"""
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        return text
    
    def collect_until_next_h2(lines, start):
        """Check if the next structural element is h2, used for warning block boundary"""
        pass
    
    while i < len(lines):
        line = lines[i]
        
        # Skip the first H1 title (line 0: # 考研数学一...)
        if i == 0 and line.startswith('# ') and '考研数学一' in line:
            i += 1
            continue
        
        # Handle blockquotes
        if line.startswith('> '):
            result.append('<blockquote>')
            bq_lines = []
            while i < len(lines) and lines[i].startswith('> '):
                bq_lines.append(lines[i][2:])
                i += 1
            content = '<br>\n'.join(bq_lines)
            content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
            result.append(content)
            result.append('</blockquote>')
            continue
        
        # Display math blocks (multi-line $$...$$)
        if line.strip() == '$$':
            # Start of multi-line display math
            math_lines = ['$$']
            i += 1
            while i < len(lines):
                math_lines.append(lines[i])
                if lines[i].strip() == '$$':
                    i += 1
                    break
                i += 1
            result.append('\n'.join(math_lines))
            continue
        
        # Single-line display math $$...$$ (not starting with $$ alone)
        if line.strip().startswith('$$') and line.strip() != '$$' and line.strip().endswith('$$'):
            result.append(line)
            i += 1
            continue
        
        # Chapter headers: # 第X章 → <h2 id="chX">
        if line.startswith('# 第') and '章' in line:
            chapter_num += 1
            title = line[2:].strip()
            result.append(f'<h2 id="ch{chapter_num}">{title}</h2>')
            i += 1
            continue
        
        # Type headers: ## 题型N... → <h3>
        if line.startswith('## '):
            title = line[3:].strip()
            title = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', title)
            result.append(f'<h3>{title}</h3>')
            i += 1
            continue
        
        # Sub-headers: ### ... → <h4>
        if line.startswith('### '):
            title = line[4:].strip()
            title = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', title)
            result.append(f'<h4>{title}</h4>')
            i += 1
            continue
        
        # Horizontal rule
        if line.strip() == '---':
            result.append('<hr>')
            i += 1
            continue
        
        # Table detection - look ahead for header separator line
        if '|' in line and i + 1 < len(lines) and '|---' in lines[i + 1]:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            result.append('<table>')
            for ti, tline in enumerate(table_lines):
                cells = [c.strip() for c in tline.split('|')]
                if cells and cells[0] == '':
                    cells = cells[1:]
                if cells and cells[-1] == '':
                    cells = cells[:-1]
                
                if ti == 0:
                    result.append('<tr>')
                    for cell in cells:
                        cell_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                        result.append(f'<th>{cell_html}</th>')
                    result.append('</tr>')
                elif ti == 1:
                    continue
                else:
                    result.append('<tr>')
                    for cell in cells:
                        cell_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cell)
                        result.append(f'<td>{cell_html}</td>')
                    result.append('</tr>')
            result.append('</table>')
            continue
        
        # Code blocks (with ``` markers)
        if line.strip().startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing ```
            result.append('<pre><code>')
            for cl in code_lines:
                cl = cl.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                result.append(cl)
            result.append('</code></pre>')
            continue
        
        # ⚠️ warning detection - wrap in highlight-box
        if '⚠️' in line:
            warn_lines = []
            start_i = i
            # Collect the ⚠️ line and subsequent list items
            while i < len(lines):
                l = lines[i]
                if i == start_i:
                    warn_lines.append(l)
                    i += 1
                elif l.startswith('- ') or l.startswith('1. ') or l.startswith('2. ') or l.startswith('3. '):
                    warn_lines.append(l)
                    i += 1
                elif l.strip() and not l.startswith('#') and not l.startswith('---') and not l.startswith('>'):
                    # Continue if it was a continuation of previous bullet (like description after -)
                    # But we need to be careful - stop at next heading or hr
                    warn_lines.append(l)
                    i += 1
                else:
                    break
            result.append('<div class="highlight-box">')
            for wl in warn_lines:
                wl_processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', wl)
                if wl.startswith('- '):
                    result.append(wl_processed)
                elif wl.startswith(('1. ', '2. ', '3. ')):
                    result.append(wl_processed)
                elif wl.strip():
                    result.append(f'<p>{wl_processed}</p>')
                else:
                    result.append(wl_processed)
            result.append('</div>')
            continue
        
        # Process regular lines
        if line.strip():
            processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            
            # Unordered list items
            if line.startswith('- '):
                result.append('<ul>')
                ul_lines = []
                while i < len(lines) and lines[i].startswith('- '):
                    item = lines[i][2:]
                    item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                    ul_lines.append(f'<li>{item}</li>')
                    i += 1
                result.extend(ul_lines)
                result.append('</ul>')
                continue
            
            # Ordered list items
            if re.match(r'^\d+\.\s', line):
                result.append('<ol>')
                ol_lines = []
                while i < len(lines) and re.match(r'^\d+\.\s', lines[i]):
                    item = re.sub(r'^\d+\.\s', '', lines[i])
                    item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                    ol_lines.append(f'<li>{item}</li>')
                    i += 1
                result.extend(ol_lines)
                result.append('</ol>')
                continue
            
            # Regular paragraph
            result.append(f'<p>{processed}</p>')
        else:
            # Empty line
            result.append('')
        
        i += 1
    
    return '\n'.join(result)


# Main
if __name__ == '__main__':
    with open(r'E:\coding\demo\docs\math\calculus\数学一-分章节经典题型与关联知识点.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_body = convert_md_to_html(md_content)
    
    # Template - use raw string but don't double braces
    template = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>常考题型 — 高等数学 - 考研笔记</title>\n    <link rel="stylesheet" href="../assets/css/style.css">\n    <script src="../assets/js/main.js" defer></script>\n    <script>\n        MathJax = {\n            tex: { inlineMath: [[\'$\', \'$\'], [\'\\\\(\', \'\\\\)\']], displayMath: [[\'$$\', \'$$\'], [\'\\\\[\', \'\\\\]\']] },\n            options: { ignoreHtmlClass: \'no-math\' }\n        };\n    </script>\n    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" defer></script>\n</head>\n<body>\n<a class="skip-link" href="#main-content">跳到内容</a>\n<div id="scroll-progress"></div>\n\n<nav class="site-nav">\n    <div class="site-nav-inner">\n        <span class="nav-logo">考研笔记</span>\n        <a href="../index.html">首页</a>\n        <a href="../knowledge-base.html">知识库</a>\n        <a href="../exam-types.html" class="active">常考题型及解法</a>\n        <a href="../notes.html">个人笔记</a>\n        <a href="../mistakes.html">错题本</a>\n        <div class="nav-controls">\n            <button class="theme-toggle" aria-label="切换深色/浅色模式"><span class="theme-toggle-icon">🌙</span></button>\n            <button class="hamburger" aria-label="菜单" aria-expanded="false"><span></span><span></span><span></span></button>\n        </div>\n    </div>\n</nav>\n<div class="mobile-nav-overlay"></div>\n<div class="mobile-menu" role="dialog" aria-label="导航菜单">\n    <a href="../index.html">首页</a>\n    <a href="../knowledge-base.html">知识库</a>\n    <a href="../exam-types.html">常考题型及解法</a>\n    <a href="../notes.html">个人笔记</a>\n    <a href="../mistakes.html">错题本</a>\n    <button class="menu-theme-toggle"><span class="menu-theme-icon">🌙</span> 切换深色/浅色模式</button>\n</div>\n\n<div class="page-header math">\n    <h1>🎯 高等数学 · 常考题型与解法</h1>\n    <div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../exam-types.html">常考题型及解法</a> / 高等数学</div>\n</div>\n\n<div class="container" id="main-content">\n    <div class="toc">\n        <h3>章节导航</h3>\n        <ul>\n            <li><a href="#ch1">第一章 函数极限连续</a></li>\n            <li><a href="#ch2">第二章 导数与微分</a></li>\n            <li><a href="#ch3">第三章 中值定理及导数的应用</a></li>\n            <li><a href="#ch4">第四章 不定积分</a></li>\n            <li><a href="#ch5">第五章 定积分及其应用</a></li>\n            <li><a href="#ch6">第六章 常微分方程</a></li>\n            <li><a href="#ch7">第七章 多元函数微分学</a></li>\n            <li><a href="#ch8">第八章 二重积分</a></li>\n            <li><a href="#ch9">第九章 向量代数与空间解析</a></li>\n            <li><a href="#ch10">第十章 无穷级数</a></li>\n            <li><a href="#ch11">第十一章 三重积分曲线曲面积分</a></li>\n            <li><a href="#ch12">第十二章 多元积分学应用</a></li>\n        </ul>\n    </div>\n\n    <div class="content-card">\nCONTENT_PLACEHOLDER\n    </div>\n</div>\n\n<div class="site-footer">\n    <p>&copy; 2026 cx861 | 考研笔记 | <a href="https://github.com/cx861">GitHub</a></p>\n</div>\n<button class="back-top" id="backTop" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">↑</button>\n<script>\nconst backTop = document.getElementById(\'backTop\');\nwindow.addEventListener(\'scroll\', () => backTop.classList.toggle(\'visible\', window.scrollY > 300));\n</script>\n</body>\n</html>'
    
    output = template.replace('CONTENT_PLACEHOLDER', html_body)
    
    with open(r'E:\coding\demo\docs\math\exam-types.html', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print('Done! Converted', len(html_body.split('\n')), 'lines of HTML body.')
