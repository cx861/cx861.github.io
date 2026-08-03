"""补充导入: 408常考题型-计算机网络 + 政治全部"""
import os, sys, json, re, time
import requests

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json"
}
ROOT_PAGE = "387715f9-ecd6-807f-a418-ff5520cfc38e"
BASE = "D:/my-project/kaoyan-reference"


def api(method, url, data=None):
    for attempt in range(3):
        try:
            r = requests.request(method, url, headers=HEADERS, json=data, timeout=60)
            if r.status_code in (200, 201):
                return r
            print(f"  API {r.status_code}: {r.text[:200] if r.text else ''}")
            if r.status_code == 429:
                time.sleep(3)
        except Exception as e:
            print(f"  API error: {e}")
            time.sleep(2)
    return None


def get_child_page_id(parent_id, title):
    """Find child page by exact title"""
    r = api("GET", f"https://api.notion.com/v1/blocks/{parent_id}/children?page_size=30")
    if r:
        for c in r.json().get("results", []):
            if c.get("type") == "child_page":
                if c["child_page"].get("title", "") == title:
                    return c["id"]
    return None


def create_page(title, parent_id):
    """Create sub-page, return page_id"""
    r = api("POST", "https://api.notion.com/v1/pages", {
        "parent": {"page_id": parent_id},
        "properties": {"title": [{"type": "text", "text": {"content": title}}]}
    })
    if r:
        return r.json()["id"]
    return None


# Block builders
def heading(text, level):
    t = f"heading_{level}"
    return {"object": "block", "type": t, t: {"rich_text": [{"type": "text", "text": {"content": text[:1000]}}]}}

def paragraph(text):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:1000]}}]}}

def rich_paragraph(text):
    parts = []
    for chunk in re.split(r'(\*\*[^*]+\*\*)', text):
        if chunk.startswith('**') and chunk.endswith('**'):
            parts.append({"type": "text", "text": {"content": chunk[2:-2][:1000]}, "annotations": {"bold": True}})
        elif chunk:
            parts.append({"type": "text", "text": {"content": chunk[:1000]}})
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parts}}

def quote(text):
    return {"object": "block", "type": "quote", "quote": {"rich_text": [{"type": "text", "text": {"content": text[:1000]}}]}}

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def code_block(text):
    return {"object": "block", "type": "code", "code": {"rich_text": [{"type": "text", "text": {"content": text[:1000]}}], "language": "plain text"}}

def bullet(text):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text[:1000]}}]}}

def numbered(text):
    return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": re.sub(r'^\d+\.\s*', '', text)[:1000]}}]}}


def md_to_blocks(md_text):
    blocks = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        s = line.strip()
        if s.startswith('#### '): blocks.append(heading(s[5:], 3))
        elif s.startswith('### '): blocks.append(heading(s[4:], 2))
        elif s.startswith('## '): blocks.append(heading(s[3:], 1))
        elif s.startswith('# '): blocks.append(heading(s[2:], 1))
        elif s.startswith('> '): blocks.append(quote(s[2:]))
        elif s == '---': blocks.append(divider())
        elif re.match(r'^\d+\.\s', s): blocks.append(numbered(s))
        elif s.startswith('- '): blocks.append(bullet(s[2:]))
        elif s.startswith('```'):
            code_lines = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i]); i += 1
            blocks.append(code_block('\n'.join(code_lines)))
        elif '|' in s and s.count('|') >= 2:
            table_lines = [s]; i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                table_lines.append(lines[i]); i += 1
            i -= 1
            for tl in table_lines:
                if not re.match(r'^\|[-:|\s]+\|$', tl):
                    cells = [c.strip() for c in tl.split('|')[1:-1]]
                    blocks.append(paragraph(' | '.join(cells) if cells else ''))
        else:
            blocks.append(rich_paragraph(s))
        i += 1
    return blocks


def import_file(md_path, page_title, parent_id):
    print(f"  {page_title}", end=" ", flush=True)
    pid = create_page(page_title, parent_id)
    if not pid:
        return False
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = [l[:1500] for l in content.split('\n')]
    blocks = md_to_blocks('\n'.join(lines))
    total = len(blocks)
    for start in range(0, total, 80):
        batch = blocks[start:start+80]
        r = api("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", {"children": batch})
        if not r:
            print(f"FAIL batch {start}")
            return False
    print(f"OK ({total} blocks)")
    return True


# ======== Main ========

# 1. Import last 408 file
s408 = get_child_page_id(ROOT_PAGE, "408")
if s408:
    print("=== 补充 408 ===")
    import_file(
        f"{BASE}/408/常考题型与解法/计算机网络_常考题型与解法.md",
        "常考题型-计算机网络", s408
    )
else:
    print("ERROR: 408 page not found!")
    sys.exit(1)

# 2. Re-import 政治
print("\n=== 重新导入 政治 ===")
sPoli = create_page("政治", ROOT_PAGE)
if sPoli:
    for path, title in [
        ("政治/知识库/01-马克思主义基本原理.md", "知识库-马原"),
        ("政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md", "知识库-毛中特"),
        ("政治/知识库/03-习近平新时代中国特色社会主义思想概论.md", "知识库-习思想"),
        ("政治/知识库/04-中国近现代史纲要.md", "知识库-史纲"),
        ("政治/知识库/05-思想道德与法治.md", "知识库-思修"),
        ("政治/知识库/06-形势与政策知识点.md", "知识库-时政"),
        ("政治/常考题型与解法/01-马原常见题型.md", "常考题型-马原"),
        ("政治/常考题型与解法/02-毛中特常见题型.md", "常考题型-毛中特"),
        ("政治/常考题型与解法/03-史纲常见题型.md", "常考题型-史纲"),
        ("政治/常考题型与解法/04-思修常见题型.md", "常考题型-思修"),
        ("政治/常考题型与解法/05-形势与政策常见题型.md", "常考题型-时政"),
    ]:
        import_file(f"{BASE}/{path}", title, sPoli)

print("\n全部完成!")
