"""Find the newest entity in Notion."""
import httpx

import os
# Both tokens
OLD_TOKEN = os.getenv("NOTION_TOKEN_OLD")
NEW_TOKEN = os.getenv("NOTION_TOKEN")

def search_newest(token: str, label: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    response = httpx.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={
            "query": "",
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 10
        },
        timeout=30.0
    )

data = response.json()
results = data.get("results", [])

print("=" * 50)
print("🔍 MOST RECENTLY EDITED (last 15)")
print("=" * 50)

for p in results:
    obj_type = p.get("object", "")
    last_edited = p.get("last_edited_time", "")[:16]
    
    # Extract title
    title = "Unknown"
    if obj_type == "page":
        props = p.get("properties", {})
        # Try Name first (database pages), then title (regular pages)
        name_prop = props.get("Name", {}) or props.get("title", {})
        title_arr = name_prop.get("title", [])
        if title_arr:
            title = title_arr[0].get("text", {}).get("content", "Unknown")
    elif obj_type == "database":
        title_arr = p.get("title", [])
        if title_arr:
            title = title_arr[0].get("text", {}).get("content", "Unknown")
    
    print(f"  [{last_edited}] {title} ({obj_type})")

print()
