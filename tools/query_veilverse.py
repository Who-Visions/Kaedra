"""
VeilVerse Local Query Tool
Fast queries against local SQLite backup.
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

BACKUP_DB = Path(__file__).parent.parent / "data" / "veilverse_backup.db"


def get_connection():
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(BACKUP_DB)
    conn.row_factory = sqlite3.Row
    return conn


def query_by_category(category: str, limit: int = 50) -> List[Dict]:
    """Get all entities in a category."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM entities WHERE category = ? ORDER BY name LIMIT ?",
        (category, limit)
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def query_by_name(name: str) -> Optional[Dict]:
    """Find entity by name (case-insensitive)."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM entities WHERE LOWER(name) LIKE ? LIMIT 1",
        (f"%{name.lower()}%",)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def search(query: str, limit: int = 20) -> List[Dict]:
    """Full-text search across name, description, notes."""
    conn = get_connection()
    pattern = f"%{query}%"
    cursor = conn.execute("""
        SELECT * FROM entities 
        WHERE name LIKE ? OR description LIKE ? OR notes LIKE ?
        ORDER BY 
            CASE WHEN LOWER(name) = ? THEN 1
                 WHEN LOWER(name) LIKE ? THEN 2
                 ELSE 3 END,
            name
        LIMIT ?
    """, (pattern, pattern, pattern, query.lower(), f"{query.lower()}%", limit))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_stats() -> Dict:
    """Get database statistics."""
    conn = get_connection()
    
    # Total count
    total = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    
    # By category
    by_category = {}
    for row in conn.execute("SELECT category, COUNT(*) FROM entities GROUP BY category ORDER BY COUNT(*) DESC"):
        by_category[row[0] or "Uncategorized"] = row[1]
    
    # By canon status
    by_canon = {}
    for row in conn.execute("SELECT canon_status, COUNT(*) FROM entities GROUP BY canon_status ORDER BY COUNT(*) DESC"):
        by_canon[row[0] or "Unknown"] = row[1]
    
    # By status
    by_status = {}
    for row in conn.execute("SELECT status, COUNT(*) FROM entities GROUP BY status ORDER BY COUNT(*) DESC"):
        by_status[row[0] or "Unknown"] = row[1]
    
    conn.close()
    return {
        "total": total,
        "by_category": by_category,
        "by_canon_status": by_canon,
        "by_status": by_status
    }


def get_characters(limit: int = 100) -> List[Dict]:
    """Get all characters."""
    return query_by_category("Character", limit)


def get_locations(limit: int = 100) -> List[Dict]:
    """Get all locations."""
    return query_by_category("Location", limit)


def get_canon_entities(limit: int = 100) -> List[Dict]:
    """Get all canon entities."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM entities WHERE canon_status = 'Canon' ORDER BY category, name LIMIT ?",
        (limit,)
    )
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def run_sql(sql: str, params: tuple = ()) -> List[Dict]:
    """Run arbitrary SQL query."""
    conn = get_connection()
    cursor = conn.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# CLI Demo
if __name__ == "__main__":
    print("=" * 60)
    print("🌌 VEILVERSE LOCAL DATABASE")
    print("=" * 60)
    
    stats = get_stats()
    print(f"\n📊 Total Entities: {stats['total']}")
    
    print("\n📁 By Category:")
    for cat, count in stats["by_category"].items():
        print(f"   {cat}: {count}")
    
    print("\n⚖️ By Canon Status:")
    for status, count in list(stats["by_canon_status"].items())[:5]:
        print(f"   {status}: {count}")
    
    print("\n🔍 Sample Search: 'shadow'")
    results = search("shadow", limit=5)
    for r in results:
        print(f"   - {r['name']} ({r['category']})")
