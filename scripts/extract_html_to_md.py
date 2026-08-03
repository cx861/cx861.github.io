"""
HTML 内容提取 → Markdown 转换脚本
从 kaoyan-notes 网站的 HTML 页面提取 <div class="content-card"> 内容，转为干净 Markdown。
"""
import sys
import re
from html import unescape
from bs4 import BeautifulSoup, NavigableString, Tag


def html_to_md(html_filepath):
    """读取 HTML 文件，提取 content-card 并转为 Markdown"""
    with open(html_filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')

    content = soup.find('div', class_='content-card')
    if not content:
        raise ValueError(f"未找到 content-card 元素: {html_filepath}")

    lines = []
    _process_children(content, lines, depth=0)
    return '\n'.join(lines)


def _process_children(element, lines, depth=0):
    """递归处理子元素"""
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                lines.append(text)
        elif isinstance(child, Tag):
            tag_name = child.name
            if tag_name in ('h2', 'h3', 'h4', 'h5', 'h6'):
                level = int(tag_name[1])
                text = child.get_text(strip=True)
                lines.append(f"{'#' * level} {text}")
            elif tag_name == 'hr':
                lines.append('---')
            elif tag_name == 'blockquote':
                _process_blockquote(child, lines)
            elif tag_name == 'p':
                _process_paragraph(child, lines)
            elif tag_name == 'table':
                _process_table(child, lines)
            elif tag_name == 'ol':
                _process_list(child, lines, ordered=True, start=0)
            elif tag_name == 'ul':
                _process_list(child, lines, ordered=False, start=0)
            elif tag_name == 'pre':
                code = child.find('code')
                if code:
                    lang = code.get('class', [''])[0].replace('language-', '') if code.get('class') else ''
                    lines.append(f'```{lang}')
                    lines.append(code.get_text().rstrip())
                    lines.append('```')
                else:
                    lines.append('```')
                    lines.append(child.get_text().rstrip())
                    lines.append('```')
            elif tag_name == 'div':
                # 穿透 table-wrapper / vocab-list 等包装 div
                if child.get('class') and 'table-wrapper' in child.get('class'):
                    inner_table = child.find('table')
                    if inner_table:
                        _process_table(inner_table, lines)
                else:
                    _process_children(child, lines, depth+1)
            elif tag_name == 'code':
                lines.append(f'`{child.get_text(strip=True)}`')
            elif tag_name == 'strong':
                lines.append(f'**{child.get_text(strip=True)}**')
            elif tag_name == 'em':
                lines.append(f'*{child.get_text(strip=True)}*')
            elif tag_name == 'br':
                pass  # 换行处理在段落中
            elif tag_name in ('span', 'a'):
                lines.append(child.get_text(strip=True))
            else:
                _process_children(child, lines, depth+1)

    # 元素结束后加空行
    if depth == 0 and lines and lines[-1] != '':
        lines.append('')


def _process_blockquote(blockquote, lines):
    """处理 blockquote，保持内部结构"""
    inner_lines = []
    _process_deep_text(blockquote, inner_lines)
    for line in inner_lines:
        if line.strip():
            lines.append(f'> {line}')
        else:
            lines.append('>')


def _process_deep_text(element, lines):
    """深度提取文本，保留 strong/em/code 格式"""
    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                lines.append(text)
        elif isinstance(child, Tag):
            if child.name in ('p', 'br'):
                _process_deep_text(child, lines)
            elif child.name == 'strong':
                lines.append(f'**{child.get_text(strip=True)}**')
            elif child.name == 'em':
                lines.append(f'*{child.get_text(strip=True)}*')
            elif child.name == 'code':
                lines.append(f'`{child.get_text(strip=True)}`')
            elif child.name == 'a':
                lines.append(child.get_text(strip=True))
            else:
                _process_deep_text(child, lines)


def _process_paragraph(p, lines):
    """处理段落，保留内联格式（strong, em, code, a）"""
    text = _inline_to_md(p)
    if text:
        lines.append(text)


def _inline_to_md(element):
    """将元素内容转为内联 Markdown"""
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            if child.name == 'strong':
                parts.append(f'**{child.get_text(strip=True)}**')
            elif child.name == 'em':
                parts.append(f'*{child.get_text(strip=True)}*')
            elif child.name == 'code':
                parts.append(f'`{child.get_text(strip=True)}`')
            elif child.name == 'a':
                parts.append(child.get_text(strip=True))
            elif child.name == 'br':
                parts.append('\n')
            elif child.name == 'img':
                alt = child.get('alt', '')
                src = child.get('src', '')
                parts.append(f'![{alt}]({src})')
            elif child.name == 'span':
                parts.append(child.get_text(strip=True))
            else:
                parts.append(child.get_text(strip=True))
    text = ''.join(parts).strip()
    # 解码 HTML 实体
    text = unescape(text)
    return text


def _process_table(table, lines):
    """处理表格，转为 Markdown 表格"""
    rows = table.find_all('tr')
    if not rows:
        return

    # 提取所有行
    table_data = []
    max_cols = 0
    for row in rows:
        cells = row.find_all(['th', 'td'])
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        table_data.append(cell_texts)
        max_cols = max(max_cols, len(cell_texts))

    # 补齐列
    for row in table_data:
        while len(row) < max_cols:
            row.append('')

    # 输出表格
    header = table_data[0]
    lines.append('| ' + ' | '.join(header) + ' |')
    lines.append('|' + '|'.join(['------' for _ in range(max_cols)]) + '|')

    for row in table_data[1:]:
        lines.append('| ' + ' | '.join(row) + ' |')


def _process_list(list_elem, lines, ordered=False, start=0):
    """处理有序/无序列表"""
    counter = start
    for li in list_elem.find_all('li', recursive=False):
        text = _inline_to_md(li)
        if ordered:
            counter += 1
            prefix = f'{counter:02d}.' if start == 0 else f'{counter}.'
            lines.append(f'{prefix} {text}')
        else:
            lines.append(f'- {text}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_html_to_md.py <html_file>")
        sys.exit(1)

    md = html_to_md(sys.argv[1])
    print(md)
