import requests
import toml
import json
from pathlib import Path
from collections import defaultdict

# Config
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"

def analyze_deep():
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
        "query": "", 
        "sort": {"direction": "descending", "timestamp": "last_edited_time"}
    }
    
    target_prefix_hex = "2e5ca671311e81"
    print(f"🕵️  Deep Scanning IDs starting with: {target_prefix_hex} ...")

    items = []
    has_more = True
    next_cursor = None
    
    # 1. Fetch All Matches
    while has_more:
        if next_cursor:
            payload["start_cursor"] = next_cursor
            print(f"   ... Fetching page (total found: {len(items)})")

        try:
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            for item in data.get("results", []):
                item_id = item["id"].replace("-", "")
                if item_id.startswith(target_prefix_hex):
                    items.append(item)

            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"❌ Search Error: {e}")
            break

    print(f"✅ Found {len(items)} items. Analyzing Topology...")

    # 2. Analyze Topology
    usage_map = defaultdict(list) # ParentID -> [Items]
    parent_meta = {} # ParentID -> Name/Type
    databases = {}   # ID -> DB Details
    
    # Pre-pass to identify Databases
    for item in items:
        if item["object"] == "database":
            title = "".join([t["plain_text"] for t in item.get("title", [])])
            databases[item["id"]] = {
                "title": title,
                "props": list(item.get("properties", {}).keys())
            }
            parent_meta[item["id"]] = f"🗄️ {title}"

    # Main Pass to Map Parents
    for item in items:
        parent = item.get("parent", {})
        parent_type = parent.get("type")
        parent_id = "UNKNOWN"
        
        if parent_type == "database_id":
            parent_id = parent.get("database_id")
        elif parent_type == "page_id":
            parent_id = parent.get("page_id")
        elif parent_type == "workspace":
            parent_id = "WORKSPACE_ROOT"
            parent_meta[parent_id] = "🏠 Workspace Root"
            
        # Title Extraction
        title = "Untitled"
        if item["object"] == "database":
             title = "".join([t["plain_text"] for t in item.get("title", [])])
        elif item["object"] == "page":
            props = item.get("properties", {})
            # Variable title extraction based on property type
            for key, val in props.items():
                if val["type"] == "title":
                    title = "".join([t["plain_text"] for t in val.get("title", [])])
                    break
        
        usage_map[parent_id].append({
            "id": item["id"],
            "type": item["object"],
            "title": title,
            "url": item.get("url")
        })

    # 3. Generate Report
    md_lines = ["# 🗺️ Notion Deep Topology Map", ""]
    
    # Section A: Databases Found
    md_lines.append(f"## 🗄️ Discovered Databases ({len(databases)})")
    for db_id, meta in databases.items():
        md_lines.append(f"### {meta['title']}")
        md_lines.append(f"- **ID**: `{db_id}`")
        md_lines.append(f"- **Property Count**: {len(meta['props'])}")
        md_lines.append(f"- **Key Props**: {', '.join(meta['props'][:5])}...")
        md_lines.append("")

    # Section B: Hierarchy Clusters
    md_lines.append("## 🌳 Hierarchy Clusters")
    
    # Sort parents: Workspace first, then Databases, then Pages
    sorted_parents = sorted(usage_map.keys(), key=lambda k: (
        0 if k == "WORKSPACE_ROOT" else 
        1 if k in databases else 
        2
    ))

    for pid in sorted_parents:
        # Resolve Parent Name
        p_name = parent_meta.get(pid, pid)
        if pid in databases:
             p_name = f"🗄️ {databases[pid]['title']}"
        elif pid not in parent_meta:
             # Try to find if this parent is one of our items
             matches = [i for i in items if i["id"] == pid]
             if matches:
                 title = "Untitled"
                 # Extract title logic again... simplified for report
                 p_name = f"📄 Page: {pid}"
        
        children = usage_map[pid]
        md_lines.append(f"### Parent: {p_name} ({len(children)} items)")
        md_lines.append(f"**Parent ID**: `{pid}`")
        
        for child in sorted(children, key=lambda x: x['title']):
            icon = "🗄️" if child['type'] == 'database' else "📄"
            md_lines.append(f"- {icon} [{child['title']}]({child['url']})")
            
        md_lines.append("")

    out_path = ROOT / "NOTION_TOPOLOGY_MAP.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"💾 Saved Topology Map to {out_path}")

if __name__ == "__main__":
    analyze_deep()
