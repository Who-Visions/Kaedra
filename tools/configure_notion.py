"""
Auto-configure Notion IDs by searching for known pages/databases.
"""
import toml
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"

def configure():
    if not CONFIG_PATH.exists():
        print("❌ notion.toml not found")
        return

    config = toml.load(CONFIG_PATH)
    token = config["notion"]["token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    print(f"🔍 Searching Notion Workspace...")
    
    # 1. Search for Ingestion Queue (Database)
    print("   Searching for 'Ingestion Queue'...")
    resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"query": "Ingestion Queue", "filter": {"value": "database", "property": "object"}}
    )
    
    ingestion_id = None
    if resp.status_code == 200:
        results = resp.json()["results"]
        if results:
            ingestion_id = results[0]["id"]
            print(f"   ✅ Found Ingestion Queue: {ingestion_id}")
            # Map to both potential keys for compatibility
            if "mappings" not in config: config["mappings"] = {}
            if "databases" not in config: config["databases"] = {}
            
            config["mappings"]["ingestion_json"] = ingestion_id
            config["databases"]["ingestion_queue"] = ingestion_id
        else:
            print("   ⚠️ Ingestion Queue DB not found.")
    else:
        print(f"   ❌ Search failed: {resp.text}")

    # 2. Search for World Bible (Page)
    print("   Searching for 'World Bible'...")
    resp = requests.post(
        "https://api.notion.com/v1/search",
        headers=headers,
        json={"query": "World Bible", "filter": {"value": "page", "property": "object"}}
    )
    
    bible_id = None
    if resp.status_code == 200:
        results = resp.json()["results"]
        if results:
            bible_id = results[0]["id"]
            print(f"   ✅ Found World Bible: {bible_id}")
            config["pages"]["world_bible"] = bible_id
        else:
            print("   ⚠️ World Bible Page not found.")
            
    # Save Config
    with open(CONFIG_PATH, "w") as f:
        toml.dump(config, f)
        print("💾 Configuration updated.")

if __name__ == "__main__":
    configure()
