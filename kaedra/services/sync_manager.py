"""
SyncManager - Lifecycle sync for SQLite ↔ Notion
Handles downsync on startup and upsync on exit.
"""
import sqlite3
import time
import atexit
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import httpx

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
BACKUP_DB = DATA_DIR / "veilverse_backup.db"

# Notion credentials (loaded from config)
try:
    from kaedra.core.config import NOTION_TOKEN
except ImportError:
    NOTION_TOKEN = None

# Database IDs (from notion.py)
UNIVERSE_DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"
NOTION_VERSION = "2022-06-28"


class SyncManager:
    """
    Manages SQLite ↔ Notion synchronization lifecycle.
    
    Usage:
        sync = SyncManager()
        sync.downsync()  # On startup: Notion → SQLite
        # ... app runs ...
        sync.upsync()    # On exit: SQLite → Notion (auto via atexit)
    """
    
    def __init__(self, auto_register_exit: bool = True):
        self.db_path = BACKUP_DB
        self._dirty_ids: set = set()  # Track modified entities locally
        self._last_sync: Optional[float] = None
        self._sync_lock = threading.Lock()
        
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Register upsync on exit
        if auto_register_exit:
            atexit.register(self.upsync)
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
    
    def downsync(self, full: bool = False) -> int:
        """
        Pull updates from Notion → SQLite.
        
        Args:
            full: If True, do full sync. If False, only sync changes since last sync.
            
        Returns:
            Number of entities synced.
        """
        if not NOTION_TOKEN:
            print("[SyncManager] No Notion token, skipping downsync")
            return 0
        
        with self._sync_lock:
            print("[SyncManager] ⬇️ Starting downsync (Notion → SQLite)...")
            start = time.time()
            
            try:
                synced = self._do_downsync(full)
                self._last_sync = time.time()
                elapsed = (time.time() - start) * 1000
                print(f"[SyncManager] ✅ Downsync complete: {synced} entities in {elapsed:.0f}ms")
                return synced
            except Exception as e: # pylint: disable=broad-exception-caught
                print(f"[SyncManager] ❌ Downsync failed: {e}")
                return 0
    
    def _do_downsync(self, _full: bool) -> int:
        """Actual downsync implementation."""
        # Query Notion for all entities
        all_results = []
        has_more = True
        start_cursor = None
        
        with httpx.Client(timeout=30.0) as client:
            while has_more:
                payload = {"page_size": 100}
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                response = client.post(
                    f"https://api.notion.com/v1/databases/{UNIVERSE_DB_ID}/query",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                all_results.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")
        
        if not all_results:
            return 0
        
        # Update SQLite
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                notion_id TEXT UNIQUE,
                name TEXT,
                category TEXT,
                status TEXT,
                canon_status TEXT,
                description TEXT,
                notes TEXT,
                abilities_powers TEXT,
                affiliation TEXT,
                alias TEXT,
                appears_in TEXT,
                tags TEXT,
                power_level TEXT,
                timeline_year INTEGER,
                universe_era TEXT,
                importance_score REAL,
                last_updated TEXT,
                connected_to TEXT,
                raw_properties TEXT,
                synced_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        synced = 0
        for entity in all_results:
            props = entity.get("properties", {})
            notion_id = entity.get("id", "")
            
            data = {
                "notion_id": notion_id,
                "name": self._extract_title(props.get("Name", {})),
                "category": self._extract_select(props.get("Category", {})),
                "status": self._extract_status(props.get("Status", {})),
                "canon_status": self._extract_select(props.get("Canon Status", {})),
                "description": self._extract_text(props.get("Description", {})),
                "synced_at": datetime.now(timezone.utc).isoformat()
            }
            
            conn.execute("""
                INSERT INTO entities (id, notion_id, name, category, status, canon_status, description, synced_at)
                VALUES (:notion_id, :notion_id, :name, :category, :status, :canon_status, :description, :synced_at)
                ON CONFLICT(notion_id) DO UPDATE SET
                    name = :name,
                    category = :category,
                    status = :status,
                    canon_status = :canon_status,
                    description = :description,
                    synced_at = :synced_at
            """, data)
            synced += 1
        
        conn.commit()
        conn.close()
        return synced
    
    def upsync(self, force: bool = False) -> int:
        """
        Push local changes SQLite → Notion.
        
        Called automatically on exit via atexit.
        Only syncs entities marked as dirty.
        
        Returns:
            Number of entities synced.
        """
        if not NOTION_TOKEN:
            print("[SyncManager] No Notion token, skipping upsync")
            return 0
        
        if not self._dirty_ids and not force:
            print("[SyncManager] No dirty entities, skipping upsync")
            return 0
        
        with self._sync_lock:
            print("[SyncManager] ⬆️ Starting upsync (SQLite → Notion)...")
            start = time.time()
            
            try:
                synced = self._do_upsync()
                elapsed = (time.time() - start) * 1000
                print(f"[SyncManager] ✅ Upsync complete: {synced} entities in {elapsed:.0f}ms")
                return synced
            except Exception as e:
                print(f"[SyncManager] ❌ Upsync failed: {e}")
                return 0
    
    def _do_upsync(self) -> int:
        """Actual upsync implementation."""
        if not self._dirty_ids:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        synced = 0
        with httpx.Client(timeout=30.0) as client:
            for entity_id in list(self._dirty_ids):
                cursor = conn.execute(
                    "SELECT * FROM entities WHERE notion_id = ?",
                    (entity_id,)
                )
                row = cursor.fetchone()
                if not row:
                    continue
                
                # Build Notion update payload
                props = self._build_notion_props(dict(row))
                
                try:
                    response = client.patch(
                        f"https://api.notion.com/v1/pages/{entity_id}",
                        headers=self._get_headers(),
                        json={"properties": props}
                    )
                    response.raise_for_status()
                    self._dirty_ids.discard(entity_id)
                    synced += 1
                except Exception as e:
                    print(f"[SyncManager] Failed to upsync {entity_id}: {e}")
        
        conn.close()
        return synced
    
    def mark_dirty(self, entity_id: str):
        """Mark an entity as modified locally (needs upsync)."""
        self._dirty_ids.add(entity_id)

    def find_local(self, query: str) -> Optional[dict]:
        """Search for an entity in the local SQLite database by name or alias."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? OR alias LIKE ?",
            (f"%{query}%", f"%{query}%")
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def _extract_title(self, prop: dict) -> str:
        arr = prop.get("title", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""
    
    def _extract_select(self, prop: dict) -> str:
        sel = prop.get("select")
        return sel.get("name", "") if sel else ""
    
    def _extract_status(self, prop: dict) -> str:
        stat = prop.get("status")
        return stat.get("name", "") if stat else ""
    
    def _extract_text(self, prop: dict) -> str:
        arr = prop.get("rich_text", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""
    
    def _build_notion_props(self, entity: dict) -> dict:
        """Build Notion properties from SQLite row."""
        props = {}
        
        if entity.get("name"):
            props["Name"] = {"title": [{"text": {"content": entity["name"][:2000]}}]}
        if entity.get("category"):
            props["Category"] = {"select": {"name": entity["category"]}}
        if entity.get("status"):
            props["Status"] = {"status": {"name": entity["status"]}}
        if entity.get("canon_status"):
            props["Canon Status"] = {"select": {"name": entity["canon_status"]}}
        if entity.get("description"):
            props["Description"] = {"rich_text": [{"text": {"content": entity["description"][:2000]}}]}
        
        return props


# Singleton instance
_instance: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    """Get singleton SyncManager instance."""
    global _instance
    if _instance is None:
        _instance = SyncManager()
    return _instance


def downsync(full: bool = False) -> int:
    """Quick access to downsync."""
    return get_sync_manager().downsync(full)


def upsync(force: bool = False) -> int:
    """Quick access to upsync."""
    return get_sync_manager().upsync(force)
