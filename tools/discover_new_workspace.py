"""
Notion Teamspace Discovery Script
Discovers all databases and key pages in the new Dav3's Space workspace.
"""
from notion_client import Client

import os

# NEW Workspace
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"

def discover_workspace():
    client = Client(auth=TOKEN)
    
    print("=" * 60)
    print("🔍 NOTION TEAMSPACE DISCOVERY")
    print("=" * 60)
    
    # 1. List all users (verify connection)
    print("\n[1] WORKSPACE USERS:")
    try:
        users = client.users.list().get("results", [])
        for u in users:
            print(f"  - {u.get('name', 'Unknown')} ({u.get('type', 'N/A')})")
    except Exception as e:
        print(f"  [!] Error: {e}")
    
    # 2. Paginated search for ALL objects
    print("\n[2] ALL ACCESSIBLE OBJECTS (Databases + Pages):")
    databases = []
    pages = []
    
    try:
        has_more = True
        start_cursor = None
        
        while has_more:
            response = client.search(page_size=100, start_cursor=start_cursor)
            results = response.get("results", [])
            
            for r in results:
                obj_type = r.get("object")
                if obj_type == "database":
                    title_list = r.get("title", [])
                    title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
                    databases.append({"id": r["id"], "title": title})
                elif obj_type == "page":
                    props = r.get("properties", {})
                    title_prop = props.get("title") or props.get("Name") or {}
                    title_list = title_prop.get("title", [])
                    title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
                    pages.append({"id": r["id"], "title": title})
            
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            if not start_cursor:
                break
                
    except Exception as e:
        print(f"  [!] Error during search: {e}")
    
    # Print databases
    print(f"\n  📊 DATABASES ({len(databases)}):")
    for db in databases:
        print(f"    - {db['title']}")
        print(f"      ID: {db['id']}")
    
    # Print a sample of key pages
    print(f"\n  📄 KEY PAGES (showing first 20 of {len(pages)}):")
    key_terms = ["veil", "universe", "codex", "bible", "ingestion", "character", "lore", "timeline"]
    
    # First show pages matching key terms
    matched_pages = [p for p in pages if any(t in p['title'].lower() for t in key_terms)]
    for page in matched_pages[:20]:
        print(f"    - {page['title']}")
        print(f"      ID: {page['id']}")
    
    print("\n" + "=" * 60)
    print(f"✅ DISCOVERY COMPLETE: {len(databases)} DBs, {len(pages)} Pages")
    print("=" * 60)

if __name__ == "__main__":
    discover_workspace()
