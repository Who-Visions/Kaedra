"""
10-Point Sync Validation Suite
Creates new entries, tests sync, and validates until errors occur.
"""
import sqlite3
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import httpx

import os
# Config
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"
BACKUP_DB = Path(__file__).parent.parent / "data" / "veilverse_backup.db"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Test results
results = []
test_entities = []


def log_result(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  [{status}] {test_name}")
    if details and not passed:
        print(f"       → {details}")
    results.append({"test": test_name, "passed": passed, "details": details})


def create_notion_page(name: str, category: str, description: str = "") -> str:
    """Create a page in Notion and return its ID."""
    payload = {
        "parent": {"database_id": DB_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": name}}]},
            "Category": {"select": {"name": category}},
        }
    }
    if description:
        payload["properties"]["Description"] = {
            "rich_text": [{"text": {"content": description}}]
        }
    
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        return r.json().get("id")


def query_notion_by_name(name: str) -> dict:
    """Query Notion for an entity by name."""
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"https://api.notion.com/v1/databases/{DB_ID}/query",
            headers=headers,
            json={
                "filter": {
                    "property": "Name",
                    "title": {"equals": name}
                }
            }
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0] if results else None


def query_sqlite_by_name(name: str) -> dict:
    """Query SQLite for an entity by name."""
    conn = sqlite3.connect(BACKUP_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT * FROM entities WHERE name = ? LIMIT 1",
        (name,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def downsync_single(notion_id: str) -> bool:
    """Sync a single entity from Notion to SQLite."""
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            f"https://api.notion.com/v1/pages/{notion_id}",
            headers=headers
        )
        if r.status_code != 200:
            return False
        
        entity = r.json()
        props = entity.get("properties", {})
        
        # Extract data
        name_arr = props.get("Name", {}).get("title", [])
        name = name_arr[0].get("text", {}).get("content", "") if name_arr else ""
        
        cat = props.get("Category", {}).get("select")
        category = cat.get("name", "") if cat else ""
        
        stat = props.get("Status", {}).get("status")
        status = stat.get("name", "") if stat else ""
        
        canon = props.get("Canon Status", {}).get("select")
        canon_status = canon.get("name", "") if canon else ""
        
        # Upsert
        conn = sqlite3.connect(BACKUP_DB)
        conn.execute("""
            INSERT INTO entities (id, notion_id, name, category, status, canon_status, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(notion_id) DO UPDATE SET
                name = ?, category = ?, status = ?, canon_status = ?, synced_at = ?
        """, (
            notion_id, notion_id, name, category, status, canon_status, 
            datetime.now(timezone.utc).isoformat(),
            name, category, status, canon_status, 
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        conn.close()
        return True


def delete_notion_page(page_id: str) -> bool:
    """Archive a Notion page."""
    with httpx.Client(timeout=30.0) as client:
        r = client.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=headers,
            json={"archived": True}
        )
        return r.status_code == 200


def cleanup_test_entities():
    """Clean up all test entities created during validation."""
    print("\n🧹 Cleaning up test entities...")
    for entity in test_entities:
        try:
            delete_notion_page(entity["id"])
            print(f"  Archived: {entity['name']}")
        except:
            pass


# ============================================================
# TESTS
# ============================================================

print("=" * 60)
print("10-POINT SYNC VALIDATION SUITE")
print("=" * 60)
print()

# TEST 1: Create Character in Notion
print("TEST 1: Create Character in Notion")
try:
    test_name = f"Test_Character_{uuid.uuid4().hex[:6]}"
    page_id = create_notion_page(test_name, "Character", "A test character for validation")
    test_entities.append({"id": page_id, "name": test_name})
    time.sleep(0.5)
    log_result("Create Character", page_id is not None, page_id[:8] if page_id else "No ID")
except Exception as e:
    log_result("Create Character", False, str(e))

# TEST 2: Create Location in Notion
print("\nTEST 2: Create Location in Notion")
try:
    test_name = f"Test_Location_{uuid.uuid4().hex[:6]}"
    page_id = create_notion_page(test_name, "Location", "A test location for validation")
    test_entities.append({"id": page_id, "name": test_name})
    time.sleep(0.5)
    log_result("Create Location", page_id is not None)
except Exception as e:
    log_result("Create Location", False, str(e))

# TEST 3: Create Item in Notion
print("\nTEST 3: Create Item in Notion")
try:
    test_name = f"Test_Item_{uuid.uuid4().hex[:6]}"
    page_id = create_notion_page(test_name, "Item")
    test_entities.append({"id": page_id, "name": test_name})
    time.sleep(0.5)
    log_result("Create Item", page_id is not None)
except Exception as e:
    log_result("Create Item", False, str(e))

# TEST 4: Query Notion by exact name
print("\nTEST 4: Query Notion by Exact Name")
try:
    if test_entities:
        target = test_entities[0]["name"]
        result = query_notion_by_name(target)
        log_result("Query by Name", result is not None, f"Found: {target}")
except Exception as e:
    log_result("Query by Name", False, str(e))

# TEST 5: Downsync single entity to SQLite
print("\nTEST 5: Downsync Single Entity to SQLite")
try:
    if test_entities:
        target = test_entities[0]
        success = downsync_single(target["id"])
        log_result("Downsync Single", success)
except Exception as e:
    log_result("Downsync Single", False, str(e))

# TEST 6: Query SQLite for synced entity
print("\nTEST 6: Query SQLite for Synced Entity")
try:
    if test_entities:
        target = test_entities[0]["name"]
        result = query_sqlite_by_name(target)
        log_result("SQLite Query", result is not None, f"Found in SQLite: {target}")
except Exception as e:
    log_result("SQLite Query", False, str(e))

# TEST 7: Verify category match between Notion and SQLite
print("\nTEST 7: Verify Category Match (Notion ↔ SQLite)")
try:
    if test_entities:
        target_name = test_entities[0]["name"]
        notion_result = query_notion_by_name(target_name)
        sqlite_result = query_sqlite_by_name(target_name)
        
        notion_cat = notion_result.get("properties", {}).get("Category", {}).get("select", {}).get("name", "")
        sqlite_cat = sqlite_result.get("category", "") if sqlite_result else ""
        
        match = notion_cat == sqlite_cat
        log_result("Category Match", match, f"Notion: {notion_cat}, SQLite: {sqlite_cat}")
except Exception as e:
    log_result("Category Match", False, str(e))

# TEST 8: Create Event with multiple properties
print("\nTEST 8: Create Event with Multiple Properties")
try:
    test_name = f"Test_Event_{uuid.uuid4().hex[:6]}"
    page_id = create_notion_page(test_name, "Event", "A complex test event with description")
    test_entities.append({"id": page_id, "name": test_name})
    time.sleep(0.5)
    log_result("Create Complex Event", page_id is not None)
except Exception as e:
    log_result("Create Complex Event", False, str(e))

# TEST 9: Batch sync all test entities
print("\nTEST 9: Batch Sync All Test Entities")
try:
    success_count = 0
    for entity in test_entities:
        if downsync_single(entity["id"]):
            success_count += 1
    
    all_synced = success_count == len(test_entities)
    log_result("Batch Sync", all_synced, f"{success_count}/{len(test_entities)} synced")
except Exception as e:
    log_result("Batch Sync", False, str(e))

# TEST 10: Verify all test entities exist in SQLite
print("\nTEST 10: Verify All Test Entities in SQLite")
try:
    found_count = 0
    for entity in test_entities:
        if query_sqlite_by_name(entity["name"]):
            found_count += 1
    
    all_found = found_count == len(test_entities)
    log_result("All in SQLite", all_found, f"{found_count}/{len(test_entities)} found")
except Exception as e:
    log_result("All in SQLite", False, str(e))

# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

passed = sum(1 for r in results if r["passed"])
failed = len(results) - passed

print(f"\n✅ Passed: {passed}/{len(results)}")
print(f"❌ Failed: {failed}/{len(results)}")

if failed > 0:
    print("\nFailed Tests:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['test']}: {r['details']}")

# Cleanup
cleanup_test_entities()

print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
