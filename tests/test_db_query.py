"""Test database query."""
import httpx
import os

DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"
TOKEN = os.getenv("NOTION_TOKEN")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Test query
r = httpx.post(
    f"https://api.notion.com/v1/databases/{DB_ID}/query",
    headers=headers,
    json={"page_size": 5},
    timeout=30
)

print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    results = data.get("results", [])
    print(f"Found {len(results)} entries")
    for p in results:
        props = p.get("properties", {})
        name = props.get("Name", {}).get("title", [{}])[0].get("text", {}).get("content", "?")
        print(f"  - {name}")
else:
    print(r.text[:500])
