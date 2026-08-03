"""验证408页面内容 - 检查第一段文本是否有中文"""
import os, requests

key = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
H = {"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03"}
ROOT = "387715f9-ecd6-807f-a418-ff5520cfc38e"

# Find 408 page
r = requests.get(f"https://api.notion.com/v1/blocks/{ROOT}/children?page_size=30", headers=H)
s408 = None
for c in r.json().get("results", []):
    if c.get("type") == "child_page" and c["child_page"]["title"] == "408":
        s408 = c["id"]
        break

if not s408:
    print("ERROR: 408 page not found!")
    exit(1)

# Get 408 children
r = requests.get(f"https://api.notion.com/v1/blocks/{s408}/children?page_size=20", headers=H)
pages = []
for c in r.json().get("results", []):
    if c.get("type") == "child_page":
        title = c["child_page"]["title"]
        pid = c["id"]
        pages.append((pid, title))
        print(f"  {title}")

# Check first child page content
if pages:
    pid, title = pages[0]
    print(f"\n--- 验证: {title} ---")
    r = requests.get(f"https://api.notion.com/v1/blocks/{pid}/children?page_size=5", headers=H)
    for b in r.json().get("results", []):
        text = str(b)
        # Check for Chinese characters
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        has_garbled = '??' in text or '�' in text
        status = "✓ 正常" if has_chinese and not has_garbled else "✗ 异常"
        print(f"  {status}: {text[:100]}...")

print("\n验证完成!")
