"""清理408下重复的 常考题型-计算机网络 页面"""
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

# Find duplicate 常考题型-计算机网络
r = requests.get(f"https://api.notion.com/v1/blocks/{s408}/children?page_size=20", headers=H)
pages = {}
for c in r.json().get("results", []):
    if c.get("type") == "child_page":
        title = c["child_page"]["title"]
        if title not in pages:
            pages[title] = []
        pages[title].append(c["id"])

for title, ids in pages.items():
    if len(ids) > 1:
        print(f"Duplicate found: {title} ({len(ids)} copies)")
        # Keep first, archive rest
        for pid in ids[1:]:
            r = requests.patch(
                f"https://api.notion.com/v1/pages/{pid}",
                headers=H,
                json={"archived": True}
            )
            print(f"  Archived: {pid} -> {'OK' if r.status_code == 200 else 'FAIL'}")
    else:
        print(f"  OK: {title}")

print("\nDone!")
