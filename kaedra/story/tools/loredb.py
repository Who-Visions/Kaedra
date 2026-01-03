"""
LoreDB Engine Tools
Integrates LoreDB with the StoryEngine tool system.
"""
import json
from pathlib import Path
from typing import Optional, List

# Import will be resolved at runtime when called from engine
# from kaedra.services.loredb import LoreDB, LoreBlock


def query_lore(sql: str) -> str:
    """
    Execute a SQL query on the lore database.
    
    Example queries:
    - SELECT * FROM blocks WHERE type = 'character'
    - SELECT * FROM blocks WHERE json_extract(attrs, '$.power_level') > 80
    - SELECT * FROM blocks WHERE json_extract(attrs, '$.faction') = 'Veil Council'
    
    Args:
        sql: SQL query string
    
    Returns:
        JSON string with query results
    """
    from kaedra.services.loredb import LoreDB
    
    # Get world path from engine context (will be set at runtime)
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world", "results": []})
    
    lore = LoreDB(world_path)
    results = lore.query(sql)
    
    return json.dumps({
        "count": len(results),
        "results": [r.to_dict() for r in results]
    }, indent=2)


def search_lore(text: str, limit: int = 20) -> str:
    """
    Full-text search across all lore blocks.
    
    Args:
        text: Search query
        limit: Maximum results (default 20)
    
    Returns:
        JSON string with matching blocks
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world", "results": []})
    
    lore = LoreDB(world_path)
    results = lore.search(text, limit)
    
    return json.dumps({
        "query": text,
        "count": len(results),
        "results": [{"id": r.id, "type": r.type, "content": r.content[:200]} for r in results]
    }, indent=2)


def create_lore_block(type: str, content: str, attrs: Optional[str] = None) -> str:
    """
    Create a new lore block.
    
    Args:
        type: Block type (character, location, event, paragraph)
        content: Markdown content
        attrs: JSON string of attributes (optional)
    
    Returns:
        JSON with the new block ID
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world"})
    
    lore = LoreDB(world_path)
    attrs_dict = json.loads(attrs) if attrs else {}
    
    block_id = lore.create_block(type, content, attrs=attrs_dict)
    
    return json.dumps({
        "success": True,
        "block_id": block_id,
        "type": type
    })


def update_lore_block(id: str, content: Optional[str] = None, attrs: Optional[str] = None) -> str:
    """
    Update an existing lore block.
    
    Args:
        id: Block ID
        content: New content (optional)
        attrs: JSON string of attributes to merge (optional)
    
    Returns:
        JSON with success status
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world"})
    
    lore = LoreDB(world_path)
    attrs_dict = json.loads(attrs) if attrs else None
    
    success = lore.update_block(id, content=content, attrs=attrs_dict)
    
    return json.dumps({
        "success": success,
        "block_id": id
    })


def get_backlinks(id: str) -> str:
    """
    Get all blocks that reference the given block.
    
    Args:
        id: Block ID to find backlinks for
    
    Returns:
        JSON with backlink blocks
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world", "results": []})
    
    lore = LoreDB(world_path)
    results = lore.get_backlinks(id)
    
    return json.dumps({
        "block_id": id,
        "backlink_count": len(results),
        "backlinks": [{"id": r.id, "type": r.type, "content": r.content[:200]} for r in results]
    }, indent=2)


def lore_stats() -> str:
    """
    Get statistics about the lore database.
    
    Returns:
        JSON with block counts by type
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world"})
    
    lore = LoreDB(world_path)
    stats = lore.stats()
    
    return json.dumps(stats, indent=2)


def sync_lore_to_cloud(target: str, id: Optional[str] = None) -> str:
    """
    Sync lore blocks to cloud storage (Notion or BigQuery).
    
    Args:
        target: "notion" (requires page_id) or "bigquery" (requires dataset_id setup)
        id: Page ID for Notion, or dataset ID for BigQuery (default: "lore")
    
    Returns:
        JSON with sync status count
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world"})
    
    lore = LoreDB(world_path)
    
    if target.lower() == "notion":
        if not id:
            return json.dumps({"error": "Notion sync requires a parent Page ID"})
        count = lore.sync_to_notion(id)
        return json.dumps({"target": "notion", "synced_blocks": count})
        
    elif target.lower() == "bigquery":
        dataset_id = id or "lore"
        success = lore.sync_to_bigquery(dataset_id)
        return json.dumps({"target": "bigquery", "success": success})
        
    return json.dumps({"error": "Invalid target. Use 'notion' or 'bigquery'"})


def query_bigquery_lore(sql: str) -> str:
    """
    Run SQL analysis on BigQuery lore dataset.
    
    Args:
        sql: BigQuery SQL statement
    
    Returns:
        JSON query results
    """
    from kaedra.services.loredb import LoreDB
    
    world_path = Path.cwd() / "lore" / "worlds" / "current"
    if not world_path.exists():
        return json.dumps({"error": "No active world"})
    
    lore = LoreDB(world_path)
    results = lore.query_bigquery(sql)
    
    return json.dumps({
        "count": len(results),
        "results": results
    }, indent=2)


# Export tools for ENGINE_TOOLS
LOREDB_TOOLS = [
    query_lore,
    search_lore,
    create_lore_block,
    update_lore_block,
    get_backlinks,
    lore_stats,
    sync_lore_to_cloud,
    query_bigquery_lore
]
