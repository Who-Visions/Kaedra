import requests
import toml
import json
from pathlib import Path

# Config
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"

def inspect_ids(ids):
    if not CONFIG_PATH.exists():
        print("Config not found")
        return

    config = toml.load(CONFIG_PATH)
    token = config["notion"]["token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    results = []

    for notion_id in ids:
        print(f"🔍 Inspecting ID: {notion_id}")
        
        # 1. Try as Database
        try:
            url = f"https://api.notion.com/v1/databases/{notion_id}"
            resp = requests.get(url, headers=headers)
            
            if resp.ok:
                db_data = resp.json()
                title = "Untitled"
                if db_data.get("title"):
                    title = "".join([t["plain_text"] for t in db_data["title"]])
                
                print(f"   ✅ Found Database: {title}")
                results.append({
                    "id": notion_id,
                    "type": "database",
                    "title": title,
                    "schema": db_data["properties"]
                })
                continue
        except Exception as e:
            print(f"   ⚠️ DB Fetch Error: {e}")

        # 2. Try as Page
        try:
            url = f"https://api.notion.com/v1/pages/{notion_id}"
            resp = requests.get(url, headers=headers)
            
            if resp.ok:
                page_data = resp.json()
                # Get title (often in properties)
                print(f"   ✅ Found Page: {page_data['id']}")
                results.append({
                    "id": notion_id,
                    "type": "page",
                    "data": page_data
                })
                continue
        except Exception as e:
            print(f"   ⚠️ Page Fetch Error: {e}")

        print("   ❌ ID not accessible as Database or Page (check permissions?)")

    # Save Report
    md_lines = ["# Notion Links Inspection"]
    for res in results:
        md_lines.append(f"\n## [{res['type'].upper()}] {res.get('title', res['id'])}")
        md_lines.append(f"**ID**: `{res['id']}`")
        if res['type'] == 'database':
            md_lines.append("### Properties")
            for name, prop in res['schema'].items():
                ptype = prop['type']
                md_lines.append(f"- **{name}** (`{ptype}`)")
                if ptype in ['select', 'multi_select', 'status']:
                    options = prop.get(ptype, {}).get('options', [])
                    if options:
                         md_lines.append(f"  - Options: {', '.join([o['name'] for o in options])}")
    
    out_path = ROOT / "NOTION_LINKED_SCHEMAS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"\n💾 Saved report to {out_path}")

if __name__ == "__main__":
    # Extracted IDs from user links
    # Link 1: 2e5ca671311e816384e6dfd56a5306fe
    # Link 2: 2e5ca671311e81e1aca3ee6936a11490
    target_ids = [
        "2e5ca671311e816384e6dfd56a5306fe", # Link 1
        "2e5ca671311e81e1aca3ee6936a11490", # Link 2
        "2e5ca671311e81bca466f254e515a7f7", # Link 3
        "2e5ca671311e816fbb30d898aa7de7c9", # Link 4
        "2e5ca671311e81c781bbd5a3bb857f4c", # Link 5
        "2e5ca671311e81d2af92cfbd6074f04a", # Link 6 (News Injector)
        "2e5ca671311e8146801edc1801ebad78", # Link 7
        "2e5ca671311e81ae885ac535308c72c1", # Link 8
        "2e5ca671311e8130aee3fec81576cc01", # Link 9
        "2e5ca671311e81368083ecd615826400", # Link 10
        "2e5ca671311e813f884ce2f606069dfa", # Link 11 (Teamspace Home)
        "2e5ca671311e81c1a1e9c84bcf4ee95d", # Link 12 (Yasuke)
        "2e5ca671311e81c9a381d50da194f4df", # Link 13 (Audit Task List)
        "2e5ca671311e81d4bbf1d9a470a3a4ec", # Page: Causal Fracture Prayer
        "2e5ca671311e81548a85fbda79c83f38", # News Projects
        "2e5ca671311e81eb9b5eed4a4ba7ffd9", # VeilVerse Goals (1)
        "2e5ca671311e81368004c1a40c809070", # VeilVerse Goals (2)
        "2e5ca671311e8187bd69f8768b4b6218", # Link 15 (Build Ops)
        "2e5ca671311e815bac95ff6269578ff3", # Link 16 (Zeitgeist)
        "2e5ca671311e81e2ae43d3d78b3881ad", # Link 17 (Xoah Character Hub)
        "2e5ca671311e81cb89b8c19821907cce", # Link 18 (API Contract Rulebook)
        "2e5ca671311e811fb3d7c7f3b9150afe"  # Original DB (for comparison)
    ]
    inspect_ids(target_ids)
