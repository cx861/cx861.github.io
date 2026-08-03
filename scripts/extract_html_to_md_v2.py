"""
HTML 内容提取 → Markdown 转换脚本 v2
使用 markdownify 库，正确处理复杂HTML结构。
"""
import sys
import re
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def fix_math_escapes(text):
    """在 $...$ 和 $$...$$ 数学块内，将 \_ 还原为 _"""
    # $$...$$ display math
    def fix_display(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_')
        inner = inner.replace(r'\*', '*')
        return f'$${inner}$$'
    text = re.sub(r'\$\$(.+?)\$\$', fix_display, text, flags=re.DOTALL)

    # $...$ inline math
    def fix_inline(m):
        inner = m.group(1)
        inner = inner.replace(r'\_', '_')
        inner = inner.replace(r'\*', '*')
        return f'${inner}$'
    text = re.sub(r'\$(.+?)\$', fix_inline, text)

    # 非数学块内的 \_ 也应该还原（markdownify 过度转义）
    text = text.replace(r'\_', '_')

    return text


def escape_math_in_html(raw_html):
    """保护 $...$ 块内的 < >"""
    def protect(m):
        inner = m.group(0)
        inner = inner.replace('<', '\uFF1C')  # ＜
        inner = inner.replace('>', '\uFF1E')  # ＞
        return inner
    # 只处理 inline math $...$, 不碰 $$...$$ (它们已在 <div> 中，不会被误解析)
    raw_html = re.sub(r'\$[^$]+?\$', protect, raw_html)
    return raw_html


def unprotect_math(text):
    text = text.replace('\uFF1C', '<')
    text = text.replace('\uFF1E', '>')
    return text


def html_to_md(html_filepath):
    with open(html_filepath, 'r', encoding='utf-8') as f:
        raw_html = f.read()

    # 先移除 script/style 标签（避免 JS 中的 $ 被误匹配）
    raw_html = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL)
    raw_html = re.sub(r'<style[^>]*>.*?</style>', '', raw_html, flags=re.DOTALL)

    # 预处理：保护数学块内的 < > 防止被HTML解析器当成标签
    raw_html = escape_math_in_html(raw_html)

    soup = BeautifulSoup(raw_html, 'lxml')

    content = soup.find('div', class_='content-card')
    if not content:
        raise ValueError(f"未找到 content-card: {html_filepath}")

    # 转换
    html_str = str(content)
    result = md(html_str, heading_style='atx', strip=['a', 'span'], bullets='-')

    # 修复数学块内的转义
    result = fix_math_escapes(result)

    # 还原 < > 
    result = unprotect_math(result)

    # 后处理
    lines = result.split('\n')
    cleaned = []
    in_code_block = False
    prev_empty = False

    for line in lines:
        stripped = line.rstrip()

        if stripped.startswith('```'):
            in_code_block = not in_code_block

        # 去连续空行
        is_empty = stripped == ''
        if is_empty and prev_empty and not in_code_block:
            continue
        prev_empty = is_empty

        # 修复有序列表编号（保持01. 02. 格式）
        if not in_code_block:
            cleaned.append(stripped)
        else:
            cleaned.append(stripped)

    return '\n'.join(cleaned)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_html_to_md_v2.py <html_file>")
        sys.exit(1)

    result = html_to_md(sys.argv[1])
    print(result)
