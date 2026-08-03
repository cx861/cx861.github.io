"""
修复 Notion 408 编码问题：清理乱码页面，用正确 UTF-8 重新导入
根因: import_v4.ps1 的 PowerShell ConvertTo-Json 损坏了中文编码
修复: 使用 Python requests + json 直接发送 (UTF-8 native)
"""
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
    """Send API request with retry"""
    for attempt in range(3):
        try:
            r = requests.request(method, url, headers=HEADERS, json=data, timeout=30)
            if r.status_code in (200, 201):
                return r
            if r.status_code == 429:
                time.sleep(2)
                continue
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
    return r


def find_child_page_by_title(parent_id, title):
    """Find a child page by title (returns page id or None)"""
    r = api("GET", f"https://api.notion.com/v1/blocks/{parent_id}/children?page_size=50")
    if r and r.status_code == 200:
        for child in r.json().get("results", []):
            if child.get("type") == "child_page":
                ct = child["child_page"].get("title", "")
                if ct == title:
                    return child["id"]
    return None


def delete_page(page_id):
    """Archive (soft-delete) a page"""
    r = api("PATCH", f"https://api.notion.com/v1/pages/{page_id}", {"archived": True})
    return r and r.status_code == 200


def create_page(title, parent_id):
    """Create a sub-page"""
    data = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    }
    r = api("POST", "https://api.notion.com/v1/pages", data)
    if r and r.status_code in (200, 201):
        return r.json()["id"]
    print(f"  ERROR creating '{title}': {r.status_code if r else 'None'}")
    return None


# ==================== Block builders ====================

def heading(text, level):
    t = f"heading_{level}"
    return {
        "object": "block", "type": t, t: {
            "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
        }
    }

def paragraph(text):
    return {
        "object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
        }
    }

def rich_paragraph(text):
    parts = []
    for chunk in re.split(r'(\*\*[^*]+\*\*)', text):
        if chunk.startswith('**') and chunk.endswith('**'):
            parts.append({
                "type": "text",
                "text": {"content": chunk[2:-2][:1000]},
                "annotations": {"bold": True}
            })
        elif chunk:
            parts.append({"type": "text", "text": {"content": chunk[:1000]}})
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": parts}}

def quote(text):
    return {
        "object": "block", "type": "quote", "quote": {
            "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
        }
    }

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def code_block(text):
    return {
        "object": "block", "type": "code", "code": {
            "rich_text": [{"type": "text", "text": {"content": text[:1000]}}],
            "language": "plain text"
        }
    }

def bullet(text):
    return {
        "object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:1000]}}]
        }
    }

def numbered(text):
    return {
        "object": "block", "type": "numbered_list_item", "numbered_list_item": {
            "rich_text": [{"type": "text", "text": {"content": re.sub(r'^\d+\.\s*', '', text)[:1000]}}]
        }
    }


def md_to_blocks(md_text):
    """Convert Markdown to Notion blocks"""
    blocks = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        s = line.strip()

        if s.startswith('#### '):
            blocks.append(heading(s[5:], 3))
        elif s.startswith('### '):
            blocks.append(heading(s[4:], 2))
        elif s.startswith('## '):
            blocks.append(heading(s[3:], 1))
        elif s.startswith('# '):
            blocks.append(heading(s[2:], 1))
        elif s.startswith('> '):
            blocks.append(quote(s[2:]))
        elif s == '---':
            blocks.append(divider())
        elif re.match(r'^\d+\.\s', s):
            blocks.append(numbered(s))
        elif s.startswith('- '):
            blocks.append(bullet(s[2:]))
        elif s.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            blocks.append(code_block('\n'.join(code_lines)))
        elif '|' in s and s.count('|') >= 2:
            table_lines = [s]
            i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].count('|') >= 2:
                table_lines.append(lines[i])
                i += 1
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
    """Import a single MD file"""
    print(f"  {page_title}", end=" ", flush=True)

    page_id = create_page(page_title, parent_id)
    if not page_id:
        return False

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Truncate long lines
    lines = [l[:1500] for l in content.split('\n')]
    content = '\n'.join(lines)

    blocks = md_to_blocks(content)
    total = len(blocks)

    for start in range(0, total, 80):
        batch = blocks[start:start + 80]
        r = api("PATCH", f"https://api.notion.com/v1/blocks/{page_id}/children", {"children": batch})
        if not r or r.status_code not in (200, 201):
            print(f"FAIL batch {start}/{total} (status={r.status_code if r else 'None'})")
            return False

    print(f"OK ({total} blocks)")
    return True


def import_subject(subject, files, parent_id):
    """Import a whole subject category"""
    subject_id = create_page(subject, parent_id)
    print(f"\n=== {subject} ({subject_id}) ===")
    if not subject_id:
        return
    for path, title in files:
        import_file(path, title, subject_id)


def main():
    print("=" * 50)
    print("Notion 408 乱码修复脚本")
    print("=" * 50)

    # Step 1: Clean broken 408 page
    print("\n[1/3] 清理已损坏的 408 页面...")
    old_408_id = find_child_page_by_title(ROOT_PAGE, "408")
    if old_408_id:
        print(f"  找到旧 408 页面: {old_408_id}")
        if delete_page(old_408_id):
            print("  已归档")
        else:
            print("  归档失败，请手动删除")
    else:
        print("  未找到旧 408 页面，跳过")

    # Step 2: Clean broken 政治 page (also imported via PowerShell)
    print("\n[2/3] 清理已损坏的 政治 页面...")
    old_poli_id = find_child_page_by_title(ROOT_PAGE, "政治")
    if old_poli_id:
        print(f"  找到旧 政治 页面: {old_poli_id}")
        if delete_page(old_poli_id):
            print("  已归档")
        else:
            print("  归档失败，请手动删除")
    else:
        print("  未找到旧 政治 页面，跳过")

    # Step 3: Re-import 408 with correct encoding
    print("\n[3/3] 重新导入 408...")
    import_subject("408", [
        (f"{BASE}/408/知识库/408数据结构_按章节知识点.md", "知识库-数据结构"),
        (f"{BASE}/408/知识库/计算机组成原理_按章节知识点.md", "知识库-计算机组成原理"),
        (f"{BASE}/408/知识库/操作系统_按章节知识点.md", "知识库-操作系统"),
        (f"{BASE}/408/知识库/计算机网络_按章节知识点.md", "知识库-计算机网络"),
        (f"{BASE}/408/常考题型与解法/408数据结构_常考题型与解法.md", "常考题型-数据结构"),
        (f"{BASE}/408/常考题型与解法/计算机组成原理_常考题型与解法.md", "常考题型-计组"),
        (f"{BASE}/408/常考题型与解法/操作系统_常考题型与解法.md", "常考题型-操作系统"),
        (f"{BASE}/408/常考题型与解法/计算机网络_常考题型与解法.md", "常考题型-计算机网络"),
    ], ROOT_PAGE)

    print("\n全部完成!")


if __name__ == '__main__':
    main()
