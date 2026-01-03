import requests
import toml
from pathlib import Path

ROOT = Path(__file__).parent.parent
config = toml.load(ROOT / "kaedra" / "config" / "notion.toml")
token = config["notion"]["token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json"
}

for query in ["Codex", "Laws", "Queue"]:
    print(f"Searching for '{query}'...")
    resp = requests.post("https://api.notion.com/v1/search", headers=headers, json={
        "query": query
    })

    if resp.status_code == 200:
        results = resp.json().get("results", [])
        for r in results:
            obj_type = r.get("object")
            title_list = r.get("title", []) or r.get("properties", {}).get("title", {}).get("title", []) or r.get("properties", {}).get("Name", {}).get("title", [])
            title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
            print(f"[{obj_type}] {title} | ID: {r['id']}")
    else:
        print(f"Error: {resp.text}")
