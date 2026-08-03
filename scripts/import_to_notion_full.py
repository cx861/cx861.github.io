"""
MD文档 → Notion 批量导入脚本（完整版）
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
    """创建子页面"""
    data = {
        "parent": {"page_id": parent_page_id},
        "properties": {"title": [{"text": {"content": title}}]}
    }
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=data)
    if r.status_code == 200:
        return r.json()["id"]
    print(f"  ERROR creating '{title}': {r.status_code}")
    return None


def md_to_blocks(md_text):
    """MD转Notion blocks"""
    blocks = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
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
        # 表格
        elif '|' in line and line.count('|') >= 2:
            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                table_lines.append(lines[i])
                i += 1
            i -= 1
            for tl in table_lines:
                if not re.match(r'^\|[-:|\s]+\|$', tl):
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    blocks.append(paragraph(' | '.join(cells)))
        # 普通段落
        else:
            blocks.append(rich_paragraph(line.strip()))
        i += 1
    return blocks


def heading(text, level):
    t = f"heading_{level}"
    return {"object": "block", "type": t, t: {
        "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
    }}

def paragraph(text):
    return {"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
    }}

def rich_paragraph(text):
    parts = []
    for chunk in re.split(r'(\*\*[^*]+\*\*)', text):
        if chunk.startswith('**') and chunk.endswith('**'):
            parts.append({"type": "text", "text": {"content": chunk[2:-2][:1000]}, "annotations": {"bold": True}})
        elif chunk:
            parts.append({"type": "text", "text": {"content": chunk[:1000]}})
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parts}}

def quote(text):
    return {"object": "block", "type": "quote", "quote": {
        "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
    }}

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def code_block(text):
    return {"object": "block", "type": "code", "code": {
        "rich_text": [{"type": "text", "text": {"content": text[:1000]}}],
        "language": "plain text"
    }}

def bulleted_list_item(text):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
        "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
    }}

def numbered_list_item(text):
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
        "rich_text": [{"type": "text", "text": {"content": re.sub(r'^\d+\.\s*', '', text)[:1000]}}]
    }}


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

    blocks = md_to_blocks(content)
    total = len(blocks)

    # 分批写入（每批90个）
    for start in range(0, total, 90):
        batch = blocks[start:start+90]
        r = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": batch}
        )
        if r.status_code != 200:
            print(f"    Batch error at {start}: {r.status_code}")
            return False

    print(f"    OK: {total} blocks")
    return True


def import_subject(subject, files, parent_id):
    """导入一个科目"""
    subject_id = create_page(subject, parent_id)
    print(f"Created: {subject} ({subject_id})")
    for md_path, title in files:
        import_file(md_path, title, subject_id)


def main():
    base = "D:/my-project/kaoyan-reference"

    # Skip 英语 (already imported)

    # 数学
    import_subject("数学", [
        (f"{base}/数学/知识库/高等数学知识库.md", "知识库/高等数学"),
        (f"{base}/数学/知识库/线代知识点全梳理.md", "知识库/线性代数"),
        (f"{base}/数学/知识库/概率论知识库-数学一.md", "知识库/概率论"),
        (f"{base}/数学/常考题型与解法/高等数学经典题型与解法.md", "常考题型/高等数学"),
        (f"{base}/数学/常考题型与解法/线代常考题型与解法.md", "常考题型/线性代数"),
        (f"{base}/数学/常考题型与解法/概率论常考题型与解法-数学一.md", "常考题型/概率论"),
    ], ROOT_PAGE)

    # 408
    import_subject("408", [
        (f"{base}/408/知识库/408数据结构_按章节知识点.md", "知识库/数据结构"),
        (f"{base}/408/知识库/计算机组成原理_按章节知识点.md", "知识库/计算机组成原理"),
        (f"{base}/408/知识库/操作系统_按章节知识点.md", "知识库/操作系统"),
        (f"{base}/408/知识库/计算机网络_按章节知识点.md", "知识库/计算机网络"),
        (f"{base}/408/常考题型与解法/408数据结构_常考题型与解法.md", "常考题型/数据结构"),
        (f"{base}/408/常考题型与解法/计算机组成原理_常考题型与解法.md", "常考题型/计算机组成原理"),
        (f"{base}/408/常考题型与解法/操作系统_常考题型与解法.md", "常考题型/操作系统"),
        (f"{base}/408/常考题型与解法/计算机网络_常考题型与解法.md", "常考题型/计算机网络"),
    ], ROOT_PAGE)

    # 政治
    import_subject("政治", [
        (f"{base}/政治/知识库/01-马克思主义基本原理.md", "知识库/马原"),
        (f"{base}/政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md", "知识库/毛中特"),
        (f"{base}/政治/知识库/03-习近平新时代中国特色社会主义思想概论.md", "知识库/习思想"),
        (f"{base}/政治/知识库/04-中国近现代史纲要.md", "知识库/史纲"),
        (f"{base}/政治/知识库/05-思想道德与法治.md", "知识库/思修"),
        (f"{base}/政治/知识库/06-形势与政策知识点.md", "知识库/时政"),
        (f"{base}/政治/常考题型与解法/01-马原常见题型.md", "常考题型/马原"),
        (f"{base}/政治/常考题型与解法/02-毛中特常见题型.md", "常考题型/毛中特"),
        (f"{base}/政治/常考题型与解法/03-史纲常见题型.md", "常考题型/史纲"),
        (f"{base}/政治/常考题型与解法/04-思修常见题型.md", "常考题型/思修"),
        (f"{base}/政治/常考题型与解法/05-形势与政策常见题型.md", "常考题型/时政"),
    ], ROOT_PAGE)

    print("\n全部完成！")


if __name__ == '__main__':
    main()
