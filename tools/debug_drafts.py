import requests
import toml
from pathlib import Path

ROOT = Path("c:/Users/super/kaedra_proper")
config = toml.load(ROOT / "kaedra" / "config" / "notion.toml")
token = config["notion"]["token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2025-09-03"
}

# The Architects Draft
page_id = "3afdc6e85dc34633bb3e4113292b49e5"

resp = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
print(f"Page Fetch: {resp.status_code}")
if resp.status_code == 200:
    print(f"Title: {resp.json().get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text')}")
else:
    print(resp.text)

# Check children
resp = requests.get(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers)
print(f"Children Fetch: {resp.status_code}")
if resp.status_code == 200:
    print(f"Found {len(resp.json().get('results', []))} blocks")
