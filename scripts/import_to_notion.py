"""
MD文档 → Notion 批量导入脚本
创建页面结构，将MD文件内容导入到Notion页面
"""
import sys, json, re, os
import requests

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json"
}
ROOT_PAGE = "387715f9-ecd6-807f-a418-ff5520cfc38e"


def create_page(title, parent_page_id):
    """在父页面下创建子页面，返回页面ID"""
    data = {
        "parent": {"page_id": parent_page_id},
        "properties": {"title": [{"text": {"content": title}}]}
    }
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
    if r.status_code == 200:
        return r.json()["id"]
    else:
        print(f"  ERROR creating page '{title}': {r.status_code} {r.text[:200]}")
        return None


def md_to_blocks(md_text):
    """将Markdown文本转为Notion blocks（简化版）"""
    blocks = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # 空行跳过
        if not line.strip():
            i += 1
            continue

        # 标题
        if line.startswith('#### '):
            blocks.append(heading(line[5:], 3))
        elif line.startswith('### '):
            blocks.append(heading(line[4:], 2))
        elif line.startswith('## '):
            blocks.append(heading(line[3:], 1))
        elif line.startswith('# '):
            blocks.append(heading(line[2:], 1))

        # 引用
        elif line.startswith('> '):
            blocks.append(quote(line[2:]))

        # 分隔线
        elif line.strip() == '---':
            blocks.append(divider())

        # 有序列表
        elif re.match(r'^\d+\.\s', line):
            blocks.append(numbered_list_item(line))

        # 无序列表
        elif line.startswith('- '):
            blocks.append(bulleted_list_item(line[2:]))

        # 代码块
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append(code_block('\n'.join(code_lines)))

        # 表格（简单处理：转为段落格式）
        elif '|' in line and line.count('|') >= 2:
            # 收集连续表格行
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                table_lines.append(lines[i])
                i += 1
            i -= 1  # 回退
            # 简化处理：转为列表格式
            for tl in table_lines:
                if not re.match(r'^\|[-:|\s]+\|$', tl):  # 跳过分隔行
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    blocks.append(paragraph(' | '.join(cells)))

        # 普通段落
        else:
            text = line.strip()
            # 处理粗体 **text**
            blocks.append(rich_paragraph(text))

        i += 1

        # 每100个block分一组（API限制）
        if len(blocks) >= 90:
            break

    return blocks


def heading(text, level):
    t = "heading_" + str(level)
    return {"object": "block", "type": t, t: {
        "rich_text": [{"type": "text", "text": {"content": safe_text(text)[:1000]}}]
    }}


def paragraph(text):
    return {"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": safe_text(text)[:1000]}}]
    }}


def rich_paragraph(text):
    """处理含**粗体**的文本"""
    parts = []
    for chunk in re.split(r'(\*\*[^*]+\*\*)', text):
        if chunk.startswith('**') and chunk.endswith('**'):
            parts.append({"type": "text", "text": {"content": chunk[2:-2][:1000]},
                         "annotations": {"bold": True}})
        elif chunk:
            parts.append({"type": "text", "text": {"content": chunk[:1000]}})
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parts}}


def quote(text):
    return {"object": "block", "type": "quote", "quote": {
        "rich_text": [{"type": "text", "text": {"content": safe_text(text)[:1000]}}]
    }}


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def code_block(text):
    return {"object": "block", "type": "code", "code": {
        "rich_text": [{"type": "text", "text": {"content": safe_text(text)[:1000]}}],
        "language": "plain text"
    }}


def bulleted_list_item(text):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
        "rich_text": [{"type": "text", "text": {"content": safe_text(text)[:1000]}}]
    }}


def numbered_list_item(text):
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
        "rich_text": [{"type": "text", "text": {"content": safe_text(re.sub(r'^\d+\.\s*', '', text))[:1000]}}]
    }}


def safe_text(text):
    return text.replace('\x00', '')


def append_blocks(page_id, blocks):
    """分批追加blocks到页面"""
    for i in range(0, len(blocks), 90):
        batch = blocks[i:i+90]
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": batch}
        )
        if r.status_code != 200:
            print(f"  ERROR appending blocks: {r.status_code} {r.text[:200]}")
            return False
    return True


def import_file(md_path, page_title, parent_id):
    """导入单个MD文件"""
    print(f"  Importing: {page_title}")
    page_id = create_page(page_title, parent_id)
    if not page_id:
        return False

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 截断超长行
    lines = content.split('\n')
    lines = [l[:1500] for l in lines]
    content = '\n'.join(lines)

    # 生成blocks并分批写入
    all_blocks = md_to_blocks(content)
    total = len(all_blocks)

    # 大批量分批次处理
    for start in range(0, total, 90):
        batch = all_blocks[start:start+90]
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": batch}
        )
        if r.status_code != 200:
            print(f"    Batch error: {r.status_code}")
            return False

    print(f"    OK: {total} blocks")
    return True


def main():
    base = "D:/my-project/kaoyan-reference"

    # 英语（5个文件）
    subject = "英语"
    subject_id = create_page(subject, ROOT_PAGE)
    print(f"Created: {subject} ({subject_id})")

    files = [
        (f"{base}/英语/词汇.md", "词汇"),
        (f"{base}/英语/高分写作.md", "高分写作"),
        (f"{base}/英语/真题方法篇.md", "真题方法篇"),
        (f"{base}/英语/真题语法篇.md", "真题语法篇"),
        (f"{base}/英语/真题长难句篇.md", "真题长难句篇"),
    ]

    for md_path, title in files:
        import_file(md_path, title, subject_id)

    print("\nDone!")


if __name__ == '__main__':
    main()
