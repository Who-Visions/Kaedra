"""Downsync from NEW Notion workspace to SQLite."""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

import os
# NEW Workspace
TOKEN = os.getenv("NOTION_TOKEN")
DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"

BACKUP_DB = Path(__file__).parent.parent / "data" / "veilverse_backup.db"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def extract_title(props, key="Name"):
    arr = props.get(key, {}).get("title", [])
    return arr[0].get("text", {}).get("content", "") if arr else ""


def extract_select(props, key):
    sel = props.get(key, {}).get("select")
    return sel.get("name", "") if sel else ""


def extract_status(props, key):
    stat = props.get(key, {}).get("status")
    return stat.get("name", "") if stat else ""


print("=" * 60)
print("DOWNSYNC: Notion → SQLite")
print("=" * 60)

# Get before count
conn = sqlite3.connect(BACKUP_DB)
before = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
print(f"\nBefore: {before} entities")
conn.close()

# Fetch all from Notion
print(f"\nFetching from {DB_ID}...")
all_results = []
has_more = True
start_cursor = None

with httpx.Client(timeout=30.0) as client:
    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        r = client.post(
            f"https://api.notion.com/v1/databases/{DB_ID}/query",
            headers=headers,
            json=payload
        )
        r.raise_for_status()
        data = r.json()
        
        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
        print(f"  Fetched {len(all_results)}...")

print(f"\nTotal from Notion: {len(all_results)}")

# Upsert into SQLite
conn = sqlite3.connect(BACKUP_DB)
synced = 0

for entity in all_results:
    props = entity.get("properties", {})
    notion_id = entity.get("id", "")
    
    data = {
        "notion_id": notion_id,
        "name": extract_title(props),
        "category": extract_select(props, "Category"),
        "status": extract_status(props, "Status"),
        "canon_status": extract_select(props, "Canon Status"),
        "synced_at": datetime.now(timezone.utc).isoformat()
    }
    
    conn.execute("""
        INSERT INTO entities (id, notion_id, name, category, status, canon_status, synced_at)
        VALUES (:notion_id, :notion_id, :name, :category, :status, :canon_status, :synced_at)
        ON CONFLICT(notion_id) DO UPDATE SET
            name = :name,
            category = :category,
            status = :status,
            canon_status = :canon_status,
            synced_at = :synced_at
    """, data)
    synced += 1

conn.commit()

# Get after count and find new
after = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
new_count = after - before

print(f"\nAfter: {after} entities")
print(f"New: {new_count}")

# Show newest
cursor = conn.execute("SELECT name, category FROM entities ORDER BY synced_at DESC LIMIT 5")
print("\nMost recently synced:")
for r in cursor.fetchall():
    print(f"  - {r[0]} ({r[1]})")

conn.close()
print("\n" + "=" * 60)
