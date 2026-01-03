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

target_id = "2d90b4b40f6580189caa000b653cd487" # The one search found for "VeilVerse Universe"
print(f"Retrieving database meta for {target_id}...")
resp = requests.get(f"https://api.notion.com/v1/databases/{target_id}", headers=headers)

if resp.status_code == 200:
    print(resp.json())
else:
    print(f"Error: {resp.text}")
