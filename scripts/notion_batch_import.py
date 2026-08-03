"""Notion批量导入 - 简单粗暴版"""
import os, re, json, requests, time

KEY = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
H = {"Authorization": f"Bearer {KEY}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
ROOT = "387715f9-ecd6-807f-a418-ff5520cfc38e"
BASE = "D:/my-project/kaoyan-reference"

def notion(method, url, data):
    body = json.dumps(data, ensure_ascii=False) if data else None
    for i in range(3):
        try:
            r = requests.request(method, url, headers=H, data=body, timeout=30,
                                proxies={"http": None, "https": None})  # Bypass any proxy
            if r.status_code < 300: return r.json()
            print(f"  HTTP {r.status_code}: {r.text[:200]}")
            time.sleep(2)
        except Exception as e:
            print(f"  Retry {i}: {type(e).__name__}: {e}")
            time.sleep(3)
    return None

def create_page(title, pid):
    r = notion("POST", "https://api.notion.com/v1/pages", {
        "parent": {"page_id": pid},
        "properties": {"title": [{"text": {"content": title}}]}
    })
    return r["id"] if r else None

def import_file(md_path, title, parent_id):
    page_id = create_page(title, parent_id)
    if not page_id: return False
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    lines = [l.rstrip('\n')[:1000] for l in lines]
    
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        s = line.strip()
        
        # Build a block
        block = None
        if s.startswith('#### '): block = {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":s[5:]}}]}}
        elif s.startswith('### '): block = {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":s[4:]}}]}}
        elif s.startswith('## '): block = {"object":"block","type":"heading_1","heading_1":{"rich_text":[{"type":"text","text":{"content":s[3:]}}]}}
        elif s.startswith('> '): block = {"object":"block","type":"quote","quote":{"rich_text":[{"type":"text","text":{"content":s[2:]}}]}}
        elif s == '---': block = {"object":"block","type":"divider","divider":{}}
        elif re.match(r'^\d+\.\s', s): block = {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":re.sub(r'^\d+\.\s*','',s)}}]}}
        elif s.startswith('- '): block = {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":s[2:]}}]}}
        elif s.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'): code.append(lines[i].strip()); i += 1
            block = {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":'\n'.join(code)}}],"language":"plain text"}}
        elif '|' in s and s.count('|') >= 2:
            parts = [c.strip() for c in s.split('|')[1:-1]]
            block = {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":' | '.join(parts)}}]}}
        else:
            block = {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":s}}]}}
        
        if block:
            blocks.append(block)
            # Send batch when we have enough
            if len(blocks) >= 40:
                r = notion("PATCH", f"https://api.notion.com/v1/blocks/{page_id}/children", {"children": blocks})
                if not r: return False
                blocks = []
        i += 1
    
    # Send remaining
    if blocks:
        r = notion("PATCH", f"https://api.notion.com/v1/blocks/{page_id}/children", {"children": blocks})
        if not r: return False
    
    return True

def import_subject(name, files):
    sid = create_page(name, ROOT)
    print(f"{name}: {sid}")
    for path, title in files:
        print(f"  {title} ", end="", flush=True)
        ok = import_file(f"{BASE}/{path}", title, sid)
        print("✓" if ok else "✗", flush=True)

# 408
import_subject("408", [
    ("408/知识库/408数据结构_按章节知识点.md", "数据结构"),
    ("408/知识库/计算机组成原理_按章节知识点.md", "计算机组成原理"),
    ("408/知识库/操作系统_按章节知识点.md", "操作系统"),
    ("408/知识库/计算机网络_按章节知识点.md", "计算机网络"),
    ("408/常考题型与解法/408数据结构_常考题型与解法.md", "常考题型-数据结构"),
    ("408/常考题型与解法/计算机组成原理_常考题型与解法.md", "常考题型-计组"),
    ("408/常考题型与解法/操作系统_常考题型与解法.md", "常考题型-操作系统"),
    ("408/常考题型与解法/计算机网络_常考题型与解法.md", "常考题型-计算机网络"),
])

# 政治
import_subject("政治", [
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
])

print("\nDone!")
