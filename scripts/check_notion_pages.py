"""查看 Notion root 下的子页面"""
import os, requests

key = open(os.path.expanduser('~/.config/notion/api_key')).read().strip()
H = {"Authorization": f"Bearer {key}", "Notion-Version": "2025-09-03"}
ROOT = "387715f9-ecd6-807f-a418-ff5520cfc38e"

r = requests.get(f"https://api.notion.com/v1/blocks/{ROOT}/children?page_size=30", headers=H)
for c in r.json().get("results", []):
    if c["type"] == "child_page":
        title = c["child_page"]["title"]
        aid = c["id"]
        archived = c.get("archived", False)
        print(f"  {'[X]' if archived else '[ ]'} {aid} | {title}")
