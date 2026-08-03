"""
HTML 内容提取 → Markdown 转换 v3
使用 markdownify + BeautifulSoup，简洁可靠。
"""
import sys
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def fix_math_escapes(text):
    """还原数学块内被 markdownify 过度转义的 _ 和 *"""
    def fix_display(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_').replace(r'\*', '*')
        return f'$${inner}$$'
    text = re.sub(r'\$\$(.+?)\$\$', fix_display, text, flags=re.DOTALL)

    def fix_inline(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_').replace(r'\*', '*')
        return f'${inner}$'
    text = re.sub(r'\$(.+?)\$', fix_inline, text)

    return text


def html_to_md(html_filepath):
    with open(html_filepath, 'r', encoding='utf-8') as f:
        raw = f.read()

    soup = BeautifulSoup(raw, 'lxml')
    content = soup.find('div', class_='content-card')
    if not content:
        raise ValueError(f"未找到 content-card: {html_filepath}")

    # 移除 script/style
    for tag in content.find_all(['script', 'style']):
        tag.decompose()

    result = md(str(content), heading_style='atx', strip=['a', 'span'], bullets='-')
    result = fix_math_escapes(result)

    # 去连续空行
    lines = result.split('\n')
    cleaned = []
    prev_empty = False
    for line in lines:
        stripped = line.rstrip()
        is_empty = stripped == ''
        if is_empty and prev_empty:
            continue
        prev_empty = is_empty
        cleaned.append(stripped)

    return '\n'.join(cleaned)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_html_to_md_v3.py <html_file>")
        sys.exit(1)
    print(html_to_md(sys.argv[1]))
