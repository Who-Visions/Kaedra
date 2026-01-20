
import os
import sys
import time
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.append(os.getcwd())

from notion_client import Client, APIResponseError
from dotenv import load_dotenv

# Load env manually to ensure we get both
load_dotenv()

SOURCE_TOKEN = os.getenv("SOURCE_NOTION_TOKEN")
DEST_TOKEN = os.getenv("NOTION_TOKEN")

if not SOURCE_TOKEN or not DEST_TOKEN:
    print("[!] FATAL: Missing SOURCE_NOTION_TOKEN or NOTION_TOKEN in .env")
    sys.exit(1)

# Initialize Clients
source_client = Client(auth=SOURCE_TOKEN)
dest_client = Client(auth=DEST_TOKEN)

# Mappings to prevent loops and double-copies
# source_id -> dest_id
ID_MAP: Dict[str, str] = {}

def get_title(obj: Dict) -> str:
    """Extract title from page/db by finding the property with type 'title'."""
    # 1. Check properties (for Pages)
    props = obj.get("properties", {})
    for key, val in props.items():
        if val.get("type") == "title":
            title_list = val.get("title", [])
            return title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
            
    # 2. Check direct title attribute (for Databases)
    title_list = obj.get("title", [])
    if title_list:
        return title_list[0].get("plain_text", "Untitled")
        
    return "Untitled"


def copy_blocks(source_block_id: str, dest_block_id: str):
    """Recursively copy blocks from source to dest."""
    has_more = True
    start_cursor = None
    
    while has_more:
        try:
            response = source_client.blocks.children.list(block_id=source_block_id, start_cursor=start_cursor)
            blocks = response.get("results", [])
            
            # Batch process blocks
            # Note: Notion allows appending up to 100 blocks
            batch = []
            
            for block in blocks:
                b_type = block.get("type")
                
                if b_type in ["unsupported", "child_page", "child_database"]:
                    continue 

                # FIX 1: Filter Column Lists/Tables (Complex to migrate recursively in V1)
                if b_type in ["column_list", "column", "table", "table_row"]:
                    # Converting to callout to preserve awareness that something was here
                    new_block = {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{"type": "text", "text": {"content": f"[Complex Block '{b_type}' skipped in migration]"}}]
                        }
                    }
                    batch.append(new_block)
                    continue

                # FIX 2: Truncate Text to 2000 chars (Notion Config Limit)
                block_data = block.get(b_type, {})
                if "rich_text" in block_data:
                    sanitized_rt = []
                    for rt in block_data["rich_text"]:
                        # FIX 3: Sanitize Mentions (Convert to Text)
                        if rt.get("type") == "mention":
                            plain = rt.get("plain_text", "@Unknown")
                            sanitized_rt.append({
                                "type": "text",
                                "text": {"content": plain},
                                "annotations": rt.get("annotations", {})
                            })
                            continue
                            
                        # FIX 2: Truncate Text
                        if "text" in rt and "content" in rt["text"]:
                            content = rt["text"]["content"]
                            if len(content) > 2000:
                                rt["text"]["content"] = content[:1997] + "..."
                        
                        sanitized_rt.append(rt)
                    block_data["rich_text"] = sanitized_rt
                
                # Clean block for insertion (remove ID, created_by, etc)
                new_block = {
                    "object": "block",
                    "type": b_type,
                    b_type: block_data
                }
                batch.append(new_block)

            if batch:
                dest_client.blocks.children.append(block_id=dest_block_id, children=batch)
                print(f"    -> Appended {len(batch)} blocks.")

            # RECURSION: Check original blocks for children (nested lists, etc)
            # This is tricky because we need the NEW block IDs to append children to them.
            # Appending returns the NEW blocks.
            # So for exact fidelity of nested regular blocks (like indented lists), we need to append one by one 
            # or handle the return mapping.
            # FOR SPEED: We will skip deep nesting of standard text blocks in V1 
            # and focus on structural recursion (Pages/DBs).
            
            # CHECK FOR CHILD PAGES/DBS to recurse
            for block in blocks:
                b_type = block.get("type")
                if b_type == "child_page":
                    child_title = block.get("child_page", {}).get("title", "Untitled")
                    child_id = block["id"]
                    print(f"    [>] Found Child Page: {child_title}")
                    migrate_page(child_id, dest_block_id)
                elif b_type == "child_database":
                     child_title = block.get("child_database", {}).get("title", "Untitled")
                     child_id = block["id"]
                     print(f"    [>] Found Child DB: {child_title}")
                     migrate_db(child_id, dest_block_id)

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            
        except APIResponseError as e:
            print(f"[!] Error reading/writing blocks: {e}")
            break

def migrate_page(source_id: str, dest_parent_id: str):
    """Copy a page and its contents."""
    if source_id in ID_MAP:
        print(f"[-] Skipping already migrated page: {source_id}")
        return ID_MAP[source_id]

    try:
        # 1. Get Source Info
        page = source_client.pages.retrieve(source_id)
        title = get_title(page)
        print(f"[+] Migrating Page: '{title}'...")

        # 2. Create Destination Page
        # Note: We can only set Title and Parent initially. 
        # Complex properties are hard to map 1:1 without DB context.
        new_page = dest_client.pages.create(
            parent={"page_id": dest_parent_id} if "database_id" not in dest_parent_id else {"database_id": dest_parent_id}, 
            # Fix: parent logic depends on if dest_parent is a page or DB. 
            # For this script, we assume page-to-page tree.
            # If parent is page: {"page_id": ...}
            
            properties={
                "title": {
                    "title": [{"text": {"content": title}}]
                }
            }
        )
        new_id = new_page["id"]
        ID_MAP[source_id] = new_id
        print(f"    -> Created New Page: {new_id}")

        # 3. Copy Content
        copy_blocks(source_id, new_id)
        
        return new_id

    except APIResponseError as e:
        print(f"[!] Page Migration Failed ({source_id}): {e}")
        return None

def map_schema(source_props: Dict) -> Dict:
    """Map source DB properties to destination creation schema."""
    new_schema = {}
    for name, prop in source_props.items():
        p_type = prop.get("type")
        
        # 1. Title (Mandatory, usually 'Name' or 'title')
        if p_type == "title":
            new_schema[name] = {"title": {}}
            continue
            
        # 2. Select / Multi-Select (Copy Options)
        if p_type in ["select", "multi_select"]:
            options = []
            for opt in prop.get(p_type, {}).get("options", []):
                options.append({"name": opt["name"], "color": opt.get("color", "default")})
            new_schema[name] = {p_type: {"options": options}}
            continue
            
        # 3. Simple Types (Direct Mapping)
        if p_type in ["rich_text", "number", "date", "checkbox", "url", "email", "phone_number"]:
            new_schema[name] = {p_type: {}}
            continue
            
        # 4. Complex/Unsupported -> Convert to Rich Text to preserve data if possible?
        # Creating 'relation', 'rollup', 'formula', 'people', 'files' is complex.
        # For 'people', we can try creating it if we have common users, but it often fails.
        # Strategy: Skip for schema creation to avoid errors, OR convert to Text.
        # Converting to Text requires changing the type, which might confuse the user.
        # Let's SKIP unsupported schema props for now to ensure stability, 
        # but we might lose that column.
        # Better: Create as Rich Text so we can dump the string value into it.
        new_schema[f"{name} (Ref)"] = {"rich_text": {}}
        
    return new_schema

def map_page_properties(source_props: Dict, schema: Dict) -> Dict:
    """Map page property VALUES to the new schema."""
    new_props = {}
    for name, prop in source_props.items():
        p_type = prop.get("type")
        
        # 1. Check if this property exists in our new schema (Title is always kept)
        if name not in schema and p_type != "title" and f"{name} (Ref)" not in schema:
            continue
            
        val = prop.get(p_type)
        if val is None: continue

        # Handle specific value formatting
        if p_type == "title":
            # Sanitize title
            new_props[name] = val
        elif p_type in ["select", "multi_select", "date", "number", "url", "email", "phone_number", "checkbox"]:
             # These usually map 1:1 structure-wise for creation
             # EXCEPT Select colors? No, just passing the name/option is enough usually.
             # API expects {'select': {'name': 'Foo'}}
             if p_type == 'select': 
                 if val: new_props[name] = {"select": {"name": val.get("name")}}
             elif p_type == 'multi_select':
                 new_props[name] = {"multi_select": [{"name": v.get("name")} for v in val]}
             else:
                 new_props[name] = prop # sending the whole 'date': {...} object usually works if valid
        elif p_type == "rich_text":
            # Sanitize mentions
            sanitized = []
            for rt in val:
                if rt.get("type") == "mention":
                    sanitized.append({"type": "text", "text": {"content": rt.get("plain_text", "")}})
                else: 
                     # Truncate
                     if "text" in rt:
                         rt["text"]["content"] = rt["text"]["content"][:2000]
                     sanitized.append(rt)
            new_props[name] = {"rich_text": sanitized}
            
        # Fallback for complex types mapped to (Ref)
        elif f"{name} (Ref)" in schema:
            # Flatten to string
            flat_val = "Unknown"
            if p_type == "relation": flat_val = f"Rel: {len(val)} items"
            elif p_type == "people": flat_val = ", ".join([p.get("name", "User") for p in val])
            elif p_type == "files": flat_val = f"Files: {len(val)}"
            elif p_type == "formula": flat_val = str(val.get(val.get("type"))) # Value of formula
            
            new_props[f"{name} (Ref)"] = {
                "rich_text": [{"type": "text", "text": {"content": str(flat_val)[:2000]}}]
            }
            
    return new_props

def migrate_db(source_id: str, dest_parent_id: str):
    """Best-effort DB migration (Schema + Content)."""
    if source_id in ID_MAP: return ID_MAP[source_id]

    try:
        db = source_client.databases.retrieve(source_id)
        title = get_title(db)
        print(f"[+] Migrating Database: '{title}'...")
        
        # 1. Map Schema
        source_schema = db.get("properties", {})
        creation_schema = map_schema(source_schema)
        
        # 2. Create DB in Dest
        new_db = dest_client.databases.create(
             parent={"page_id": dest_parent_id},
             title=[{"type": "text", "text": {"content": title}}],
             properties=creation_schema
        )
        new_id = new_db["id"]
        ID_MAP[source_id] = new_id
        
        # 3. Query all pages and move them
        # Pagination for DB query
        has_more = True
        next_cursor = None
        
        while has_more:
            query = source_client.databases.query(database_id=source_id, start_cursor=next_cursor)
            rows = query.get("results", [])
            
            for row in rows:
                 row_title = get_title(row)
                 try:
                     # Map Properties
                     row_props = map_page_properties(row.get("properties", {}), creation_schema)
                     
                     new_row = dest_client.pages.create(
                         parent={"database_id": new_id},
                         properties=row_props
                     )
                     # Copy content of the row
                     copy_blocks(row["id"], new_row["id"])
                 except Exception as row_err:
                     print(f"    [!] Failed to row '{row_title}': {row_err}")
            
            has_more = query.get("has_more", False)
            next_cursor = query.get("next_cursor")

    except APIResponseError as e:
        print(f"[!] DB Migration Failed ({source_id}): {e}")
        return None

def main():
    print("🦅 PEGASUS MIGRATION protocol initiated...")
    print(f"[-] Source: ...{SOURCE_TOKEN[-5:]}")
    print(f"[-] Dest:   ...{DEST_TOKEN[-5:]}")
    
    # 1. Search for EVERYTHING (Pages + Databases)
    print("[-] Scanning Source for ALL Visible Content...")
    # Search does not support OR filter for objects easily in one go for search() endpoint?
    # Actually search() with no filter returns everything.
    all_results = []
    has_more = True
    next_cursor = None
    
    while has_more:
        res = source_client.search(query="", start_cursor=next_cursor)
        all_results.extend(res.get("results", []))
        has_more = res.get("has_more", False)
        next_cursor = res.get("next_cursor")
    
    print(f"[+] Found {len(all_results)} total entities.")
    
    # 2. Build Tree to find ROOTS
    # A "Root" is an item whose parent is NOT in our visible list.
    visible_ids = set(r["id"] for r in all_results)
    roots = []
    
    for item in all_results:
        parent = item.get("parent", {})
        p_type = parent.get("type")
        p_id = parent.get(p_type) # e.g. parent.page_id or parent.database_id
        
        # If parent is visible, this is a child node, skip it (recursion will handle it)
        if p_type in ["page_id", "database_id"] and p_id in visible_ids:
            continue
            
        # If parent is workspace, block, or invisible, this is a Root
        roots.append(item)

    print(f"[+] Identified {len(roots)} Forest Roots to migrate.")
    
    # 3. Identify/Create Dest Root
    # ... (Keep existing logic to find/create migration root)
    try:
        master_page = dest_client.pages.create(
            parent={"page_id": "a9d1159c-2c3e-4c3d-aa78-c93020b95fb6"},
             properties={"title": {"title": [{"text": {"content": "PEGASUS_FULL_MIGRATION"}}]}}
        )
    except:
        print("[!] Could not create root. Searching for ANY existing page to anchor...")
        dest_search = dest_client.search(filter={"property":"object","value":"page"}).get("results", [])
        if dest_search:
            anchor_id = dest_search[0]["id"]
            print(f"[+] Found anchor page: {get_title(dest_search[0])} ({anchor_id})")
            # Create our folder there
            master_page = dest_client.pages.create(
                parent={"page_id": anchor_id},
                 properties={"title": {"title": [{"text": {"content": "PEGASUS_FULL_MIGRATION"}}]}}
            )
        else:
             print("[!] FATAL: Destination workspace is empty.")
             return

    master_id = master_page["id"]
    print(f"[+] Migration Target Prepared: {master_id}")

    # 4. Run Migration
    for root in roots:
        obj = root.get("object")
        if obj == "page":
            migrate_page(root["id"], master_id)
        elif obj == "database":
            migrate_db(root["id"], master_id)



if __name__ == "__main__":
    main()
