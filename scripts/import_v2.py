"""批量导入408和政�到Notion"""
import os, re, json, requests

key = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
H = {"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
ROOT = "387715f9-ecd6-807f-a418-ff5520cfc38e"
BASE = "D:/my-project/kaoyan-reference"

def api(method, url, data=None):
    for attempt in range(3):
        try:
            r = requests.request(method, url, headers=H, json=data, timeout=30)
            if r.status_code in (200, 201):
                return r
        except requests.exceptions.Timeout:
            print(f"  Timeout (attempt {attempt+1})")
        except Exception as e:
            print(f"  Error: {e}")
    return r

def create_page(title, parent_id):
    r = api("POST", "https://api.notion.com/v1/pages", {
        "parent": {"page_id": parent_id},
        "properties": {"title": [{"text": {"content": title}}]}
    })
    return r.json()["id"] if r.status_code in (200, 201) else None

def b(level=None, text="", bullet=False, numbered=False, quote=False, code=False):
    """Build a Notion block"""
    rt = [{"type": "text", "text": {"content": text[:1000]}}] if not isinstance(text, list) else text
    if level:
        return {"object": "block", "type": f"heading_{level}", f"heading_{level}": {"rich_text": rt}}
    if bullet:
        return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt}}
    if numbered:
        return {"object": "block", "type": "numbered_list_item", "numbered_list_item": {"rich_text": rt}}
    if quote:
        return {"object": "block", "type": "quote", "quote": {"rich_text": rt}}
    if code:
        return {"object": "block", "type": "code", "code": {"rich_text": rt, "language": "plain text"}}
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rt}}

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def rich_text(line):
    """Parse **bold** in text"""
    parts = []
    for i, chunk in enumerate(re.split(r'(\*\*[^*]+\*\*)', line)):
        if not chunk: continue
        if chunk.startswith('**') and chunk.endswith('**'):
            parts.append({"type": "text", "text": {"content": chunk[2:-2][:1000]}, "annotations": {"bold": True}})
        else:
            parts.append({"type": "text", "text": {"content": chunk[:1000]}})
    return parts if parts else [{"type": "text", "text": {"content": line[:1000]}}]

def md_to_blocks(text):
    blocks = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        s = line.strip()

        if s.startswith('#### '): blocks.append(b(level=3, text=s[5:]))
        elif s.startswith('### '): blocks.append(b(level=2, text=s[4:]))
        elif s.startswith('## '): blocks.append(b(level=1, text=s[3:]))
        elif s.startswith('# '): blocks.append(b(level=1, text=s[2:]))
        elif s.startswith('> '): blocks.append(b(quote=True, text=s[2:]))
        elif s == '---': blocks.append(divider())
        elif re.match(r'^\d+\.\s', s): blocks.append(b(numbered=True, text=re.sub(r'^\d+\.\s*', '', s)))
        elif s.startswith('- '): blocks.append(b(bullet=True, text=s[2:]))
        elif s.startswith('```'):
            code_lines = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'): code_lines.append(lines[i]); i += 1
            blocks.append(b(code=True, text='\n'.join(code_lines)))
        elif '|' in s and s.count('|') >= 2:
            tbl = [s]; i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2: tbl.append(lines[i]); i += 1
            i -= 1
            for t in tbl:
                if not re.match(r'^\|[-:|\s]+\|$', t):
                    cells = ' | '.join(c.strip() for c in t.split('|')[1:-1])
                    blocks.append(b(text=cells))
        else:
            blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(s)}})
        i += 1
    return blocks

def import_file(path, title, parent_id):
    print(f"  {title}", end=" ", flush=True)
    pid = create_page(title, parent_id)
    if not pid: return False
    with open(path, 'r', encoding='utf-8') as f:
        text = '\n'.join(l[:1200] for l in f.read().split('\n'))
    blocks = md_to_blocks(text)
    total = len(blocks)
    for start in range(0, total, 50):
        batch = blocks[start:start+50]
        r = api("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", {"children": batch})
        if r.status_code not in (200, 201):
            print(f" FAIL:{r.status_code}")
            return False
    print(f"✓ {total} blocks", flush=True)

# 清理已存在的408页面
print("Cleaning...")
r = api("GET", f"https://api.notion.com/v1/blocks/{ROOT}/children?page_size=20")
for c in r.json().get("results", []):
    if c["type"] == "child_page" and c["child_page"]["title"] == "408":
        api("PATCH", f"https://api.notion.com/v1/pages/{c['id']}", {"archived": True})

# 408
print("\n=== 408 ===")
s408 = create_page("408", ROOT)
for path, title in [
    ("408/知识库/408数据结构_按章节知识点.md", "数据结构"),
    ("408/知识库/计算机组成原理_按章节知识点.md", "计算机组成原理"),
    ("408/知识库/操作系统_按章节知识点.md", "操作系统"),
    ("408/知识库/计算机网络_按章节知识点.md", "计算机网络"),
    ("408/常考题型与解法/408数据结构_常考题型与解法.md", "常考题型-数据结构"),
    ("408/常考题型与解法/计算机组成原理_常考题型与解法.md", "常考题型-计组"),
    ("408/常考题型与解法/操作系统_常考题型与解法.md", "常考题型-操作系统"),
    ("408/常考题型与解法/计算机网络_常考题型与解法.md", "常考题型-计算机网络"),
]:
    import_file(f"{BASE}/{path}", title, s408)

# 政治
print("\n=== 政治 ===")
sPoli = create_page("政治", ROOT)
for path, title in [
    ("政治/知识库/01-马克思主义基本原理.md", "马原"),
    ("政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md", "毛中特"),
    ("政治/知识库/03-习近平新时代中国特色社会主义思想概论.md", "习思想"),
    ("政治/知识库/04-中国近现代史纲要.md", "史纲"),
    ("政治/知识库/05-思想道德与法治.md", "思修"),
    ("政治/知识库/06-形势与政策知识点.md", "时政"),
    ("政治/常考题型与解法/01-马原常见题型.md", "常考题型-马原"),
    ("政治/常考题型与解法/02-毛中特常见题型.md", "常考题型-毛中特"),
    ("政治/常考题型与解法/03-史纲常见题型.md", "常考题型-史纲"),
    ("政治/常考题型与解法/04-思修常见题型.md", "常考题型-思修"),
    ("政治/常考题型与解法/05-形势与政策常见题型.md", "常考题型-时政"),
]:
    import_file(f"{BASE}/{path}", title, sPoli)

print("\n全部完成!")