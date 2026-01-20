import requests
import toml
import json
from pathlib import Path

# Config
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"

def discover_ids():
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

    url = "https://api.notion.com/v1/search"
    payload = {
        "query": "", # Empty query searches everything
        "sort": {
            "direction": "descending",
            "timestamp": "last_edited_time"
        }
    }

    # The prefix user observed: 2e5ca671-311e-81...
    # Normalized (no dashes): 2e5ca671311e81
    target_prefix_hex = "2e5ca671311e81"
    
    print(f"🕵️  Scanning Notion Workspace for IDs starting with: {target_prefix_hex} ...")

    has_more = True
    next_cursor = None
    matches = []
    total_scanned = 0

    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor
            print(f"   ... Fetching next page (scanned {total_scanned}, found {len(matches)})")

        try:
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results = data.get("results", [])
            total_scanned += len(results)
            
            for item in results:
                item_id = item["id"].replace("-", "")
                if item_id.startswith(target_prefix_hex):
                    
                    # Extract Title
                    title = "Untitled"
                    icon = ""
                    
                    if item["object"] == "database":
                        if item.get("title"):
                            title = "".join([t["plain_text"] for t in item["title"]])
                        if item.get("icon"):
                            icon = item["icon"].get("emoji", "🗄️")
                            
                    elif item["object"] == "page":
                        # Page title is tricky, usually in properties
                        props = item.get("properties", {})
                        # Try to find the 'title' type property
                        for prop_val in props.values():
                            if prop_val["type"] == "title":
                                title = "".join([t["plain_text"] for t in prop_val["title"]])
                                break
                        if item.get("icon"):
                            icon = item["icon"].get("emoji", "📄")

                    matches.append({
                        "id": item["id"],
                        "type": item["object"],
                        "title": title,
                        "url": item.get("url"),
                        "icon": icon
                    })

            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            break

    # Sort matches by type then title
    matches.sort(key=lambda x: (x['type'], x['title']))

    # Output Report
    md_lines = ["# 🕵️ Notion ID Discovery Report"]
    md_lines.append(f"**Target Pattern**: `{target_prefix_hex}...`")
    md_lines.append(f"**Total Scanned**: {total_scanned}")
    md_lines.append(f"**Matches Found**: {len(matches)}\n")
    
    md_lines.append(f"## Found Databases ({len([m for m in matches if m['type'] == 'database'])})")
    for m in matches:
        if m['type'] == "database":
            md_lines.append(f"- {m.get('icon', '')} **[{m['title']}]({m['url']})**")
            md_lines.append(f"  - `{m['id']}`")

    md_lines.append(f"\n## Found Pages ({len([m for m in matches if m['type'] == 'page'])})")
    for m in matches:
        if m['type'] == "page":
            md_lines.append(f"- {m.get('icon', '')} **[{m['title']}]({m['url']})**")
            md_lines.append(f"  - `{m['id']}`")

    out_path = ROOT / "NOTION_DISCOVERY_REPORT.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    print(f"\n✅ Scan Complete. Found {len(matches)} matches.")
    print(f"💾 Report saved to {out_path}")

if __name__ == "__main__":
    discover_ids()
