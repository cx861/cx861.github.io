"""导入408和政治到Notion"""
import json, re, os, requests

NOTION_KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
HEADERS = {"Authorization": f"Bearer {NOTION_KEY}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
ROOT = "387715f9-ecd6-807f-a418-ff5520cfc38e"

def create_page(title, parent_id):
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json={
        "parent": {"page_id": parent_id},
        "properties": {"title": [{"text": {"content": title}}]}
    })
    return r.json()["id"] if r.status_code == 200 else None

def md_to_blocks(text):
    blocks = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]; i += 1
        if not line.strip(): continue
        if line.startswith('#### '): blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":line[5:][:1000]}}]}})
        elif line.startswith('### '): blocks.append({"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":line[4:][:1000]}}]}})
        elif line.startswith('## '): blocks.append({"object":"block","type":"heading_1","heading_1":{"rich_text":[{"type":"text","text":{"content":line[3:][:1000]}}]}})
        elif line.startswith('# '): blocks.append({"object":"block","type":"heading_1","heading_1":{"rich_text":[{"type":"text","text":{"content":line[2:][:1000]}}]}})
        elif line.startswith('> '): blocks.append({"object":"block","type":"quote","quote":{"rich_text":[{"type":"text","text":{"content":line[2:][:1000]}}]}})
        elif line.strip() == '---': blocks.append({"object":"block","type":"divider","divider":{}})
        elif re.match(r'^\d+\.\s', line): blocks.append({"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":re.sub(r'^\d+\.\s*','',line)[:1000]}}]}})
        elif line.startswith('- '): blocks.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":line[2:][:1000]}}]}})
        elif line.startswith('```'):
            code = []; 
            while i < len(lines) and not lines[i].startswith('```'): code.append(lines[i]); i += 1
            blocks.append({"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":'\n'.join(code)[:1000]}}],"language":"plain text"}})
        elif '|' in line and line.count('|') >= 2:
            table = [line]
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2: table.append(lines[i]); i += 1
            i -= 1
            for tl in table:
                if not re.match(r'^\|[-:|\s]+\|$', tl):
                    blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":' | '.join(c.strip() for c in tl.split('|')[1:-1])[:1000]}}]}})
        else:
            txt = line.strip()
            parts = []
            for chunk in re.split(r'(\*\*[^*]+\*\*)', txt):
                if chunk.startswith('**') and chunk.endswith('**'):
                    parts.append({"type":"text","text":{"content":chunk[2:-2][:1000]},"annotations":{"bold":True}})
                elif chunk:
                    parts.append({"type":"text","text":{"content":chunk[:1000]}})
            blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":parts}})
    return blocks

def import_file(md_path, title, parent_id):
    print(f"  {title}")
    pid = create_page(title, parent_id)
    if not pid: return False
    with open(md_path, 'r', encoding='utf-8') as f:
        text = '\n'.join(l[:1500] for l in f.read().split('\n'))
    blocks = md_to_blocks(text)
    for s in range(0, len(blocks), 90):
        r = requests.patch(f"https://api.notion.com/v1/blocks/{pid}/children", headers=HEADERS, json={"children":blocks[s:s+90]})
        if r.status_code != 200: print(f"    ERROR at {s}: {r.status_code}"); return False
    print(f"    OK: {len(blocks)} blocks")
    return True

def load_subject(name, files):
    sid = create_page(name, ROOT)
    print(f"Subject: {name} ({sid})")
    for path, title in files:
        import_file(path, title, sid)

base = "D:/my-project/kaoyan-reference"

# 408
load_subject("408", [
    (f"{base}/408/知识库/408数据结构_按章节知识点.md", "数据结构"),
    (f"{base}/408/知识库/计算机组成原理_按章节知识点.md", "计算机组成原理"),
    (f"{base}/408/知识库/操作系统_按章节知识点.md", "操作系统"),
    (f"{base}/408/知识库/计算机网络_按章节知识点.md", "计算机网络"),
    (f"{base}/408/常考题型与解法/408数据结构_常考题型与解法.md", "常考题型/数据结构"),
    (f"{base}/408/常考题型与解法/计算机组成原理_常考题型与解法.md", "常考题型/计组"),
    (f"{base}/408/常考题型与解法/操作系统_常考题型与解法.md", "常考题型/操作系统"),
    (f"{base}/408/常考题型与解法/计算机网络_常考题型与解法.md", "常考题型/计算机网络"),
])

# 政治
load_subject("政治", [
    (f"{base}/政治/知识库/01-马克思主义基本原理.md", "马原"),
    (f"{base}/政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md", "毛中特"),
    (f"{base}/政治/知识库/03-习近平新时代中国特色社会主义思想概论.md", "习思想"),
    (f"{base}/政治/知识库/04-中国近现代史纲要.md", "史纲"),
    (f"{base}/政治/知识库/05-思想道德与法治.md", "思修"),
    (f"{base}/政治/知识库/06-形势与政策知识点.md", "时政"),
    (f"{base}/政治/常考题型与解法/01-马原常见题型.md", "常考题型/马原"),
    (f"{base}/政治/常考题型与解法/02-毛中特常见题型.md", "常考题型/毛中特"),
    (f"{base}/政治/常考题型与解法/03-史纲常见题型.md", "常考题型/史纲"),
    (f"{base}/政治/常考题型与解法/04-思修常见题型.md", "常考题型/思修"),
    (f"{base}/政治/常考题型与解法/05-形势与政策常见题型.md", "常考题型/时政"),
])

print("\nDone!")
