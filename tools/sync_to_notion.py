"""
VeilVerse Sync Tool - Push to NEW Workspace
Reads from local SQLite and pushes entities to Dav3's Space.
"""
import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx

import os
# NEW Workspace credentials (Dav3's Space)
NEW_TOKEN = os.getenv("NOTION_TOKEN")
NEW_DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"

# Local backup path
BACKUP_DIR = Path(__file__).parent.parent / "data"
BACKUP_DB = BACKUP_DIR / "veilverse_backup.db"

# Rate limiting
REQUESTS_PER_SECOND = 3  # Notion recommends max 3 req/sec
REQUEST_DELAY = 1.0 / REQUESTS_PER_SECOND


def get_headers():
    return {
        "Authorization": f"Bearer {NEW_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }


def build_page_properties(entity: dict) -> dict:
    """Convert SQLite row to Notion page properties."""
    props = {}
    
    # Title (required)
    if entity.get("name"):
        props["Name"] = {
            "title": [{"text": {"content": entity["name"][:2000]}}]  # Notion limit
        }
    
    # Select properties
    select_props = {
        "Category": entity.get("category"),
        "Canon Status": entity.get("canon_status"),
        "Power Level": entity.get("power_level"),
        "Universe Era": entity.get("universe_era"),
    }
    for key, val in select_props.items():
        if val:
            props[key] = {"select": {"name": val}}
    
    # Status property (special type)
    if entity.get("status"):
        props["Status"] = {"status": {"name": entity["status"]}}
    
    # Rich text properties
    text_props = {
        "Description": entity.get("description"),
        "Notes": entity.get("notes"),
        "Abilities/Powers": entity.get("abilities_powers"),
    }
    for key, val in text_props.items():
        if val:
            props[key] = {
                "rich_text": [{"text": {"content": val[:2000]}}]
            }
    
    # Multi-select properties (stored as JSON arrays or plain text)
    multi_select_props = {
        "Alias": entity.get("alias"),
        "Appears In": entity.get("appears_in"),
        "Tags": entity.get("tags"),
        "Affiliation": entity.get("affiliation"),  # New DB has this as multi_select
    }
    for key, val in multi_select_props.items():
        if val:
            try:
                # Try to parse as JSON first
                if isinstance(val, str) and val.startswith("["):
                    items = json.loads(val)
                elif isinstance(val, str):
                    # Plain text - split by comma or use as single item
                    items = [v.strip() for v in val.split(",") if v.strip()]
                else:
                    items = val
                
                if items:
                    props[key] = {
                        "multi_select": [{"name": str(item)[:100]} for item in items if item]
                    }
            except:
                # Fallback: treat as single item
                props[key] = {"multi_select": [{"name": str(val)[:100]}]}
    
    # Number properties
    if entity.get("timeline_year") is not None:
        props["Timeline Year"] = {"number": entity["timeline_year"]}
    if entity.get("importance_score") is not None:
        props["Importance Score"] = {"number": entity["importance_score"]}
    
    # Date properties
    if entity.get("last_updated"):
        props["Last Updated"] = {"date": {"start": entity["last_updated"]}}
    
    return props


def sync_to_notion():
    """Push all entities from SQLite to NEW Notion workspace."""
    print("=" * 60)
    print("🔄 VEILVERSE SYNC TOOL - Push to Dav3's Space")
    print("=" * 60)
    
    # Connect to SQLite
    if not BACKUP_DB.exists():
        print(f"[!] Backup database not found: {BACKUP_DB}")
        return
    
    conn = sqlite3.connect(BACKUP_DB)
    conn.row_factory = sqlite3.Row
    
    # Get all entities
    cursor = conn.execute("SELECT * FROM entities ORDER BY category, name")
    entities = cursor.fetchall()
    print(f"\n[1] Loaded {len(entities)} entities from SQLite")
    
    # Check what already exists in NEW database
    print(f"\n[2] Checking existing entities in NEW workspace...")
    existing_names = set()
    
    with httpx.Client(timeout=30.0) as http_client:
        has_more = True
        start_cursor = None
        
        while has_more:
            payload = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            try:
                response = http_client.post(
                    f"https://api.notion.com/v1/databases/{NEW_DB_ID}/query",
                    headers=get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                for page in data.get("results", []):
                    props = page.get("properties", {})
                    name_prop = props.get("Name", {}).get("title", [])
                    if name_prop:
                        name = name_prop[0].get("text", {}).get("content", "")
                        existing_names.add(name.lower().strip())
                
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
            except httpx.HTTPStatusError as e:
                print(f"    [!] Error querying database: {e}")
                break
            except Exception as e:
                print(f"    [!] Error: {e}")
                break
    
    print(f"    Found {len(existing_names)} existing entities")
    
    # Filter new entities
    to_create = []
    for entity in entities:
        name = entity["name"] or ""
        if name.lower().strip() not in existing_names:
            to_create.append(dict(entity))
    
    print(f"\n[3] Syncing {len(to_create)} NEW entities (skipping {len(entities) - len(to_create)} duplicates)")
    
    if not to_create:
        print("    Nothing to sync!")
        conn.close()
        return
    
    # Create pages with rate limiting
    created = 0
    failed = 0
    
    with httpx.Client(timeout=30.0) as http_client:
        for i, entity in enumerate(to_create):
            try:
                props = build_page_properties(entity)
                
                payload = {
                    "parent": {"database_id": NEW_DB_ID},
                    "properties": props
                }
                
                response = http_client.post(
                    "https://api.notion.com/v1/pages",
                    headers=get_headers(),
                    json=payload
                )
                response.raise_for_status()
                created += 1
                
                # Progress
                if (i + 1) % 10 == 0 or i == len(to_create) - 1:
                    print(f"    Created {created}/{len(to_create)} ({entity.get('name', 'Unknown')[:30]}...)")
                
            except httpx.HTTPStatusError as e:
                failed += 1
                error_body = e.response.text[:200] if e.response else str(e)
                print(f"    [!] Failed: {entity.get('name', 'Unknown')[:30]} - {error_body}")
                
            except Exception as e:
                failed += 1
                print(f"    [!] Error: {entity.get('name', 'Unknown')[:30]} - {e}")
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
    
    # Log sync
    conn.execute("""
        INSERT INTO sync_log (action, details, status)
        VALUES ('PUSH_TO_NEW', ?, ?)
    """, (f"Created {created}, Failed {failed}", "SUCCESS" if failed == 0 else "PARTIAL"))
    conn.commit()
    conn.close()
    
    print(f"\n[4] Sync Summary:")
    print(f"    ✅ Created: {created}")
    print(f"    ❌ Failed: {failed}")
    print(f"    ⏭️ Skipped (duplicates): {len(entities) - len(to_create)}")
    
    print("\n" + "=" * 60)
    print("✅ SYNC COMPLETE")
    print("=" * 60)
    
    return created, failed


if __name__ == "__main__":
    sync_to_notion()
