"""Rebuild linear-algebra.html with the same theme as calculus.html."""
import re

la_path = r'E:\coding\demo\docs\math\linear-algebra.html'

with open(la_path, 'r', encoding='utf-8') as f:
    old_html = f.read()

# --- Step 1: Extract content from the old content-card ---
# Find content-card div
card_match = re.search(
    r'<div class="content-card">\s*\n(.*?)</div>\s*\n\s*</main>',
    old_html, re.DOTALL
)
if not card_match:
    print("ERROR: Could not find content-card!")
    exit(1)

raw_content = card_match.group(1)

# --- Step 2: Clean up the raw content ---
# Remove the page-level <h1> and subtitle (these go into page-header)
raw_content = re.sub(r'^\s*<h1>[^<]+</h1>\s*\n', '', raw_content)
raw_content = re.sub(r'^\s*<p class="subtitle">[^<]+</p>\s*\n', '', raw_content)
# Remove the first <blockquote> (编著信息, goes into page-header)
raw_content = re.sub(r'^\s*<blockquote>[^<]+</blockquote>\s*\n', '', raw_content)
# Remove leading <hr>
raw_content = re.sub(r'^\s*<hr>\s*\n', '', raw_content, count=1)

# Convert h2 id format: <h2 id="第一章-行列式"> -> <h2 id="ch1">
ch_counter = 0
def replace_h2(m):
    global ch_counter
    ch_counter += 1
    text = re.sub(r'<[^>]+>', '', m.group(1))
    return f'<h2 id="ch{ch_counter}">{m.group(1)}</h2>'

raw_content = re.sub(r'<h2 id="[^"]*">(.*?)</h2>', replace_h2, raw_content)

# Reset counter for TOC
ch_counter = 0

# --- Step 3: Extract chapter titles for TOC and breadcrumb ---
with open(r'C:\Users\陈鑫\Desktop\过程文档\文档\线代知识点全梳理.md', 'r', encoding='utf-8') as f:
    md = f.read()

chapter_titles = re.findall(r'^## (第[一二三四五六七八九十]+章 .+?)$', md, re.MULTILINE)
print(f"Found {len(chapter_titles)} chapters in MD:")
for t in chapter_titles:
    print(f"  {t}")

# --- Step 4: Build TOC HTML ---
toc_items = []
for i, title in enumerate(chapter_titles):
    ch_num = i + 1
    toc_items.append(f'                <li><a href="#ch{ch_num}">{title}</a></li>')

toc_html = '\n'.join(toc_items)

# --- Step 5: Build the page-header ---
page_title = "线性代数"

new_page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>线性代数 - 考研笔记</title>
    <link rel="stylesheet" href="../assets/css/style.css">
    <script src="../assets/js/main.js" defer></script>
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                packages: {{ '[+]': ['physics'] }}
            }},
            loader: {{ load: ['[tex]/physics'] }},
            options: {{ skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'], ignoreHtmlClass: 'no-math' }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main-content">跳到内容</a>
<div id="scroll-progress"></div>

    <!-- Navigation Bar -->
    <nav class="site-nav">
        <div class="site-nav-inner">
            <span class="nav-logo">考研笔记</span>
            <a href="../index.html">首页</a>
            <a href="../knowledge-base.html" class="active">知识库</a>
            <a href="../notes.html">个人笔记</a>
            <a href="../mistakes.html">错题本</a>
            <a href="../exam-types.html">常考题型及解法</a>
            <div class="nav-controls">
                <button class="theme-toggle" aria-label="切换深色/浅色模式"><span class="theme-toggle-icon">🌙</span></button>
                <button class="hamburger" aria-label="菜单" aria-expanded="false">
                    <span></span><span></span><span></span>
                </button>
            </div>
        </div>
    </nav>

<!-- 移动端菜单 -->
<div class="mobile-nav-overlay"></div>
<div class="mobile-menu" role="dialog" aria-label="导航菜单">
    <a href="../index.html">首页</a>
    <a href="../knowledge-base.html">知识库</a>
    <a href="../notes.html">个人笔记</a>
    <a href="../mistakes.html">错题本</a>
    <a href="../exam-types.html">常考题型及解法</a>
    <button class="menu-theme-toggle"><span class="menu-theme-icon">🌙</span> 切换深色/浅色模式</button>
</div>

    <!-- Page Header -->
    <div class="page-header math">
        <h1>🔢 {page_title}</h1>
        <div class="breadcrumb"><a href="../index.html">首页</a> / <a href="../knowledge-base.html">知识库</a> / 线性代数</div>
        <p style="margin-top: 0.5rem; opacity: 0.75;">编著：李永乐 | 适用：数学一/二/三 | 来源：金榜时代考研数学</p>
    </div>

    <div class="container" id="main-content">
        <!-- Table of Contents -->
        <div class="toc">
            <h3>目录</h3>
            <ul>
{toc_html}
            </ul>
        </div>

        <!-- Main Content -->
        <div class="content-card">
{raw_content.strip()}
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
</html>
'''

with open(la_path, 'w', encoding='utf-8') as f:
    f.write(new_page)

print(f"\nDone! Wrote {len(new_page)} chars to {la_path}")

# Verify
with open(la_path, 'r', encoding='utf-8') as f:
    verify = f.read()

h2_count = len(re.findall(r'<h2 id="ch\d">', verify))
toc_count = len(re.findall(r'<li><a href="#ch\d">', verify))
print(f"H2 chapters: {h2_count}")
print(f"TOC entries: {toc_count}")
print(f"Has site-nav: {'site-nav' in verify}")
print(f"Has page-header: {'page-header' in verify}")
print(f"Has content-card: {'content-card' in verify}")
print(f"Has back-top: {'back-top' in verify}")
print(f"Has site-footer: {'site-footer' in verify}")
