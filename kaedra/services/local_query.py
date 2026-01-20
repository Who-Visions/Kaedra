"""
LocalQueryService - Fast SQLite Query Layer for VeilVerse
Provides ~5ms entity lookups vs ~500ms Notion API calls.
"""
import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache

# Default database path
DEFAULT_DB = Path(__file__).parent.parent.parent / "data" / "veilverse_backup.db"

# Connection pool (thread-local storage)
_thread_local = threading.local()

# Query cache TTL
CACHE_TTL = 300  # 5 minutes


class LocalQueryService:
    """
    Fast SQLite query layer with connection pooling and caching.
    
    Usage:
        lqs = LocalQueryService()
        entity = lqs.find_entity("Yasuke", "Character")
        results = lqs.search("shadow blade")
    """
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DEFAULT_DB
        self._cache: Dict[str, tuple] = {}  # key -> (timestamp, value)
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection (pooled)."""
        if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
            _thread_local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=5.0
            )
            _thread_local.connection.row_factory = sqlite3.Row
        return _thread_local.connection
    
    def _cached(self, key: str) -> Optional[Any]:
        """Check cache and return value if valid."""
        if key in self._cache:
            ts, value = self._cache[key]
            if time.time() - ts < CACHE_TTL:
                return value
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set cache value."""
        self._cache[key] = (time.time(), value)
    
    def is_available(self) -> bool:
        """Check if local database is available."""
        return self.db_path.exists()
    
    def find_entity(self, name: str, category: str = None) -> Optional[Dict]:
        """
        Find an entity by name, optionally filtered by category.
        Returns None if not found.
        
        Performance: ~2-5ms
        """
        if not self.is_available():
            return None
        
        cache_key = f"entity:{name.lower()}:{category or 'any'}"
        if cached := self._cached(cache_key):
            return cached
        
        conn = self._get_connection()
        
        try:
            if category:
                cursor = conn.execute(
                    "SELECT * FROM entities WHERE LOWER(name) = ? AND LOWER(category) = ? LIMIT 1",
                    (name.lower(), category.lower())
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM entities WHERE LOWER(name) = ? LIMIT 1",
                    (name.lower(),)
                )
            
            row = cursor.fetchone()
            if row:
                result = self._row_to_dict(row)
                self._set_cache(cache_key, result)
                return result
                
            # Fuzzy fallback: LIKE match
            cursor = conn.execute(
                "SELECT * FROM entities WHERE LOWER(name) LIKE ? ORDER BY LENGTH(name) ASC LIMIT 1",
                (f"%{name.lower()}%",)
            )
            row = cursor.fetchone()
            if row:
                result = self._row_to_dict(row)
                self._set_cache(cache_key, result)
                return result
                
        except Exception as e:
            print(f"[LocalQuery] Error in find_entity: {e}")
        
        return None
    
    def get_entity(self, name: str) -> Optional[Dict]:
        """Find any entity by name (alias for find_entity with no category)."""
        return self.find_entity(name)
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Full-text search across name, description, notes.
        Returns scored list of matches.
        
        Performance: ~5-15ms
        """
        if not self.is_available():
            return []
        
        cache_key = f"search:{query.lower()}:{limit}"
        if cached := self._cached(cache_key):
            return cached
        
        conn = self._get_connection()
        pattern = f"%{query}%"
        
        try:
            cursor = conn.execute("""
                SELECT *, 
                    CASE 
                        WHEN LOWER(name) = ? THEN 100
                        WHEN LOWER(name) LIKE ? THEN 80
                        WHEN LOWER(name) LIKE ? THEN 60
                        WHEN description LIKE ? THEN 40
                        WHEN notes LIKE ? THEN 20
                        ELSE 10
                    END as score
                FROM entities 
                WHERE name LIKE ? OR description LIKE ? OR notes LIKE ? OR alias LIKE ?
                ORDER BY score DESC, LENGTH(name) ASC
                LIMIT ?
            """, (
                query.lower(),           # Exact match
                f"{query.lower()}%",     # Starts with
                pattern,                 # Contains
                pattern, pattern,        # In description/notes
                pattern, pattern, pattern, pattern,  # WHERE clause
                limit
            ))
            
            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            self._set_cache(cache_key, results)
            return results
            
        except Exception as e:
            print(f"[LocalQuery] Error in search: {e}")
            return []
    
    def get_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get all entities in a category."""
        if not self.is_available():
            return []
        
        cache_key = f"category:{category.lower()}:{limit}"
        if cached := self._cached(cache_key):
            return cached
        
        conn = self._get_connection()
        
        try:
            cursor = conn.execute(
                "SELECT * FROM entities WHERE LOWER(category) = ? ORDER BY name LIMIT ?",
                (category.lower(), limit)
            )
            results = [self._row_to_dict(row) for row in cursor.fetchall()]
            self._set_cache(cache_key, results)
            return results
        except Exception as e:
            print(f"[LocalQuery] Error in get_by_category: {e}")
            return []
    
    def get_canon_entities(self, limit: int = 100) -> List[Dict]:
        """Get all canon entities."""
        if not self.is_available():
            return []
        
        conn = self._get_connection()
        
        try:
            cursor = conn.execute(
                "SELECT * FROM entities WHERE canon_status = 'Canon' ORDER BY category, name LIMIT ?",
                (limit,)
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[LocalQuery] Error in get_canon_entities: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        if not self.is_available():
            return {"total": 0, "available": False}
        
        cache_key = "stats"
        if cached := self._cached(cache_key):
            return cached
        
        conn = self._get_connection()
        
        try:
            total = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            
            by_category = {}
            for row in conn.execute("SELECT category, COUNT(*) FROM entities GROUP BY category ORDER BY COUNT(*) DESC"):
                by_category[row[0] or "Uncategorized"] = row[1]
            
            by_status = {}
            for row in conn.execute("SELECT canon_status, COUNT(*) FROM entities GROUP BY canon_status ORDER BY COUNT(*) DESC"):
                by_status[row[0] or "Unknown"] = row[1]
            
            result = {
                "total": total,
                "available": True,
                "by_category": by_category,
                "by_canon_status": by_status
            }
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"[LocalQuery] Error in get_stats: {e}")
            return {"total": 0, "available": False}
    
    def run_sql(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute arbitrary SQL query."""
        if not self.is_available():
            return []
        
        conn = self._get_connection()
        
        try:
            cursor = conn.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[LocalQuery] Error in run_sql: {e}")
            return []
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert SQLite row to dictionary with parsed JSON fields."""
        result = dict(row)
        
        # Parse JSON array fields
        for key in ["alias", "appears_in", "tags", "connected_to"]:
            if result.get(key):
                try:
                    result[key] = json.loads(result[key])
                except:
                    pass
        
        return result
    
    def clear_cache(self):
        """Clear the query cache."""
        self._cache.clear()


# Singleton instance for global use
_instance: Optional[LocalQueryService] = None


def get_local_query_service() -> LocalQueryService:
    """Get singleton LocalQueryService instance."""
    global _instance
    if _instance is None:
        _instance = LocalQueryService()
    return _instance


# Quick access functions
def find_entity(name: str, category: str = None) -> Optional[Dict]:
    """Quick access to find_entity."""
    return get_local_query_service().find_entity(name, category)


def search(query: str, limit: int = 20) -> List[Dict]:
    """Quick access to search."""
    return get_local_query_service().search(query, limit)


def get_stats() -> Dict:
    """Quick access to stats."""
    return get_local_query_service().get_stats()
