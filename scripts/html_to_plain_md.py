"""
HTML → 纯文本Markdown（不含LaTeX $...$包裹，用Unicode数学符号）
直接提取文本，保留HTML中已渲染的Unicode数学符号。
"""
import sys
from bs4 import BeautifulSoup


def extract_md(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    content = soup.find('div', class_='content-card')
    for tag in content.find_all(['script', 'style']):
        tag.decompose()

    lines = []

    def walk(el):
        for child in el.children:
            if hasattr(child, 'name'):
                t = child.name
                txt = child.get_text().strip()
                if not txt:
                    continue
                if t in ('h2', 'h3', 'h4'):
                    level = int(t[1]) + 1
                    lines.append(f"{'#' * level} {txt}")
                elif t == 'hr':
                    lines.append('---')
                elif t == 'blockquote':
                    for line in txt.split('\n'):
                        s = line.strip()
                        if s:
                            lines.append(f'> {s}')
                elif t == 'p':
                    lines.append(txt)
                elif t == 'table':
                    rows = child.find_all('tr')
                    for ri, row in enumerate(rows):
                        cells = [c.get_text().strip() for c in row.find_all(['th', 'td'])]
                        lines.append('| ' + ' | '.join(cells) + ' |')
                        if ri == 0:
                            lines.append('|' + '|'.join(['------'] * len(cells)) + '|')
                elif t in ('ol', 'ul'):
                    prefix = '1. ' if t == 'ol' else '- '
                    for li in child.find_all('li', recursive=False):
                        lines.append(f"{prefix}{li.get_text().strip()}")
                elif t in ('pre',):
                    lines.append('```')
                    lines.append(txt)
                    lines.append('```')
                elif t == 'div':
                    walk(child)
                else:
                    lines.append(txt)
            else:
                txt = str(child).strip()
                if txt:
                    lines.append(txt)

    walk(content)

    cleaned = []
    prev_empty = False
    for line in lines:
        line = line.rstrip()
        is_empty = line == ''
        if is_empty and prev_empty:
            continue
        prev_empty = is_empty
        cleaned.append(line)
    return '\n'.join(cleaned)


if __name__ == '__main__':
    print(extract_md(sys.argv[1]))
