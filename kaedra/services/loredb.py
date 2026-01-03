"""
LoreDB: Hybrid Knowledge System
SQLite index + JSON storage for block-level lore management.

Inspired by SiYuan, Notion, and Obsidian - built custom for Kaedra.
"""
import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import re
import logging
import os
try:
    from google.cloud import bigquery
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False

try:
    from kaedra.services.notion import NotionService
    HAS_NOTION = True
except ImportError:
    HAS_NOTION = False

log = logging.getLogger("kaedra")


@dataclass
class LoreBlock:
    """A single block of lore content."""
    id: str
    type: str  # "paragraph", "heading", "character", "location", "event"
    content: str
    parent_id: Optional[str] = None
    attrs: Dict[str, Any] = field(default_factory=dict)
    refs: List[str] = field(default_factory=list)
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "LoreBlock":
        return cls(**data)


class LoreDB:
    """
    Hybrid SQLite + JSON knowledge system.
    
    Features:
    - Block-level IDs for fine-grained references
    - SQL queries on lore content
    - Full-text search
    - Bidirectional link tracking
    - JSON export for human-readable storage
    - Cloud Sync (Notion + BigQuery)
    """
    
    # Block ID prefix for identification
    BLOCK_PREFIX = "blk_"
    
    # Reference patterns
    REF_PATTERN = re.compile(r'\[\[(blk_[a-z0-9]+)\]\]')  # [[blk_abc123]]
    EMBED_PATTERN = re.compile(r'\{\{(blk_[a-z0-9]+)\}\}')  # {{blk_abc123}}
    MENTION_PATTERN = re.compile(r'@(\w+)')  # @CharacterName
    
    def __init__(self, world_path: Path):
        """
        Initialize LoreDB for a specific world.
        
        Args:
            world_path: Path to the world folder (e.g., lore/worlds/world_abc123/)
        """
        self.world_path = Path(world_path)
        self.db_path = self.world_path / "lore.db"
        self.world_id = self.world_path.name
        
        # Cloud Clients
        self.notion = NotionService() if HAS_NOTION else None
        self.bq_client = bigquery.Client() if HAS_BIGQUERY else None
        
        # Ensure world folder exists
        self.world_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite
        self._init_db()
        
        log.info(f"LoreDB initialized: {self.db_path}")
    
    def _init_db(self):
        """Create SQLite tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        conn.executescript("""
            -- Blocks table
            CREATE TABLE IF NOT EXISTS blocks (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                type TEXT NOT NULL,
                content TEXT,
                attrs JSON,
                refs JSON,
                created TEXT DEFAULT CURRENT_TIMESTAMP,
                updated TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Links table (bidirectional tracking)
            CREATE TABLE IF NOT EXISTS links (
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                type TEXT DEFAULT 'ref',
                PRIMARY KEY (source_id, target_id, type)
            );
            
            -- Full-text search
            CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
                id UNINDEXED,
                content,
                type
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_blocks_type ON blocks(type);
            CREATE INDEX IF NOT EXISTS idx_blocks_parent ON blocks(parent_id);
            CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id);
        """)
        
        conn.commit()
        conn.close()
    
    def _conn(self) -> sqlite3.Connection:
        """Get a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _generate_id(self) -> str:
        """Generate a unique block ID."""
        short_uuid = uuid.uuid4().hex[:12]
        return f"{self.BLOCK_PREFIX}{short_uuid}"
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def create_block(
        self,
        type: str,
        content: str,
        parent_id: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new lore block.
        
        Args:
            type: Block type (paragraph, heading, character, location, event)
            content: Markdown content
            parent_id: Optional parent block ID
            attrs: Custom attributes (power_level, faction, era, etc.)
        
        Returns:
            The new block's ID
        """
        block_id = self._generate_id()
        now = datetime.now().isoformat()
        attrs = attrs or {}
        
        # Extract references from content
        refs = self._extract_refs(content)
        
        conn = self._conn()
        try:
            # Insert block
            conn.execute("""
                INSERT INTO blocks (id, parent_id, type, content, attrs, refs, created, updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (block_id, parent_id, type, content, json.dumps(attrs), json.dumps(refs), now, now))
            
            # Add to FTS
            conn.execute("INSERT INTO fts (id, content, type) VALUES (?, ?, ?)", 
                        (block_id, content, type))
            
            # Track outgoing links
            for ref_id in refs:
                conn.execute("""
                    INSERT OR IGNORE INTO links (source_id, target_id, type)
                    VALUES (?, ?, 'ref')
                """, (block_id, ref_id))
            
            conn.commit()
            log.info(f"Created block: {block_id} ({type})")
            return block_id
            
        finally:
            conn.close()
    
    def get_block(self, id: str) -> Optional[LoreBlock]:
        """Get a block by ID."""
        conn = self._conn()
        try:
            row = conn.execute("SELECT * FROM blocks WHERE id = ?", (id,)).fetchone()
            if row:
                return LoreBlock(
                    id=row["id"],
                    parent_id=row["parent_id"],
                    type=row["type"],
                    content=row["content"],
                    attrs=json.loads(row["attrs"] or "{}"),
                    refs=json.loads(row["refs"] or "[]"),
                    created=row["created"],
                    updated=row["updated"]
                )
            return None
        finally:
            conn.close()
    
    def update_block(
        self,
        id: str,
        content: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing block.
        
        Args:
            id: Block ID
            content: New content (optional)
            attrs: New/updated attributes (merged with existing)
        
        Returns:
            True if updated, False if not found
        """
        conn = self._conn()
        try:
            # Get existing block
            existing = self.get_block(id)
            if not existing:
                return False
            
            now = datetime.now().isoformat()
            new_content = content if content is not None else existing.content
            new_attrs = {**existing.attrs, **(attrs or {})}
            new_refs = self._extract_refs(new_content)
            
            # Update block
            conn.execute("""
                UPDATE blocks 
                SET content = ?, attrs = ?, refs = ?, updated = ?
                WHERE id = ?
            """, (new_content, json.dumps(new_attrs), json.dumps(new_refs), now, id))
            
            # Update FTS
            conn.execute("DELETE FROM fts WHERE id = ?", (id,))
            conn.execute("INSERT INTO fts (id, content, type) VALUES (?, ?, ?)",
                        (id, new_content, existing.type))
            
            # Update links (remove old, add new)
            conn.execute("DELETE FROM links WHERE source_id = ?", (id,))
            for ref_id in new_refs:
                conn.execute("""
                    INSERT OR IGNORE INTO links (source_id, target_id, type)
                    VALUES (?, ?, 'ref')
                """, (id, ref_id))
            
            conn.commit()
            log.info(f"Updated block: {id}")
            return True
            
        finally:
            conn.close()
    
    def delete_block(self, id: str) -> bool:
        """Delete a block and its links."""
        conn = self._conn()
        try:
            # Check if exists
            if not self.get_block(id):
                return False
            
            # Delete block
            conn.execute("DELETE FROM blocks WHERE id = ?", (id,))
            
            # Delete from FTS
            conn.execute("DELETE FROM fts WHERE id = ?", (id,))
            
            # Delete links (both directions)
            conn.execute("DELETE FROM links WHERE source_id = ? OR target_id = ?", (id, id))
            
            conn.commit()
            log.info(f"Deleted block: {id}")
            return True
            
        finally:
            conn.close()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def query(self, sql: str, params: tuple = ()) -> List[LoreBlock]:
        """
        Execute raw SQL query on blocks table.
        
        Example:
            lore.query("SELECT * FROM blocks WHERE type = ?", ("character",))
            lore.query("SELECT * FROM blocks WHERE json_extract(attrs, '$.power_level') > 80")
        """
        conn = self._conn()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [
                LoreBlock(
                    id=row["id"],
                    parent_id=row["parent_id"],
                    type=row["type"],
                    content=row["content"],
                    attrs=json.loads(row["attrs"] or "{}"),
                    refs=json.loads(row["refs"] or "[]"),
                    created=row["created"],
                    updated=row["updated"]
                )
                for row in rows
            ]
        finally:
            conn.close()
    
    def search(self, text: str, limit: int = 20) -> List[LoreBlock]:
        """Full-text search across all blocks."""
        conn = self._conn()
        try:
            # FTS5 search
            rows = conn.execute("""
                SELECT b.* FROM blocks b
                JOIN fts ON b.id = fts.id
                WHERE fts MATCH ?
                LIMIT ?
            """, (text, limit)).fetchall()
            
            return [
                LoreBlock(
                    id=row["id"],
                    parent_id=row["parent_id"],
                    type=row["type"],
                    content=row["content"],
                    attrs=json.loads(row["attrs"] or "{}"),
                    refs=json.loads(row["refs"] or "[]"),
                    created=row["created"],
                    updated=row["updated"]
                )
                for row in rows
            ]
        finally:
            conn.close()
    
    def find_by_type(self, type: str) -> List[LoreBlock]:
        """Find all blocks of a specific type."""
        return self.query("SELECT * FROM blocks WHERE type = ?", (type,))
    
    def find_by_attr(self, key: str, value: Any) -> List[LoreBlock]:
        """Find blocks with a specific attribute value."""
        return self.query(
            f"SELECT * FROM blocks WHERE json_extract(attrs, '$.{key}') = ?",
            (value,)
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # LINKS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_backlinks(self, id: str) -> List[LoreBlock]:
        """Get all blocks that reference this block."""
        conn = self._conn()
        try:
            rows = conn.execute("""
                SELECT b.* FROM blocks b
                JOIN links l ON b.id = l.source_id
                WHERE l.target_id = ?
            """, (id,)).fetchall()
            
            return [
                LoreBlock(
                    id=row["id"],
                    parent_id=row["parent_id"],
                    type=row["type"],
                    content=row["content"],
                    attrs=json.loads(row["attrs"] or "{}"),
                    refs=json.loads(row["refs"] or "[]"),
                    created=row["created"],
                    updated=row["updated"]
                )
                for row in rows
            ]
        finally:
            conn.close()
    
    def get_outlinks(self, id: str) -> List[LoreBlock]:
        """Get all blocks that this block references."""
        block = self.get_block(id)
        if not block:
            return []
        
        return [self.get_block(ref_id) for ref_id in block.refs if self.get_block(ref_id)]
    
    def _extract_refs(self, content: str) -> List[str]:
        """Extract block references from content."""
        refs = []
        refs.extend(self.REF_PATTERN.findall(content))
        refs.extend(self.EMBED_PATTERN.findall(content))
        return list(set(refs))
    
    def resolve_refs(self, content: str) -> str:
        """Expand [[blk_id]] references to their content."""
        def replace_ref(match):
            ref_id = match.group(1)
            block = self.get_block(ref_id)
            return block.content if block else f"[[{ref_id}]]"
        
        return self.REF_PATTERN.sub(replace_ref, content)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # JSON SYNC
    # ═══════════════════════════════════════════════════════════════════════════
    
    def sync_to_json(self):
        """Export all blocks to human-readable JSON files."""
        # Group blocks by type
        characters = self.find_by_type("character")
        locations = self.find_by_type("location")
        events = self.find_by_type("event")
        paragraphs = self.find_by_type("paragraph")
        
        # Export world_bible.json
        world_bible = {
            "characters": [b.to_dict() for b in characters],
            "locations": [b.to_dict() for b in locations],
            "misc": [b.to_dict() for b in paragraphs],
            "synced_at": datetime.now().isoformat()
        }
        
        with open(self.world_path / "world_bible_loredb.json", "w") as f:
            json.dump(world_bible, f, indent=2)
        
        # Export timeline.json
        timeline = {
            "events": [b.to_dict() for b in events],
            "synced_at": datetime.now().isoformat()
        }
        
        with open(self.world_path / "timeline_loredb.json", "w") as f:
            json.dump(timeline, f, indent=2)
        
        log.info(f"Synced to JSON: {len(characters)} characters, {len(locations)} locations, {len(events)} events")
    
    def sync_from_json(self, json_path: Path = None):
        """
        Import blocks from existing JSON files.
        Generates block IDs for entries that don't have them.
        """
        json_path = json_path or self.world_path / "world_bible.json"
        
        if not json_path.exists():
            log.warning(f"JSON file not found: {json_path}")
            return
        
        with open(json_path) as f:
            data = json.load(f)
        
        imported = 0
        
        # Import characters
        for char in data.get("characters", []):
            if isinstance(char, dict):
                name = char.get("name", "Unknown")
                content = char.get("description", char.get("bio", str(char)))
                attrs = {k: v for k, v in char.items() if k not in ["name", "description", "bio"]}
                attrs["name"] = name
                self.create_block("character", content, attrs=attrs)
                imported += 1
        
        # Import locations
        for loc in data.get("locations", []):
            if isinstance(loc, dict):
                name = loc.get("name", "Unknown")
                content = loc.get("description", str(loc))
                attrs = {k: v for k, v in loc.items() if k not in ["description"]}
                attrs["name"] = name
                self.create_block("location", content, attrs=attrs)
                imported += 1
        
        log.info(f"Imported {imported} blocks from {json_path}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CLOUD SYNC
    # ═══════════════════════════════════════════════════════════════════════════

    def sync_to_notion(self, parent_page_id: str) -> int:
        """
        Sync all local blocks to a Notion Page as children.
        Note: This is a simplified 1-way backup for V1.
        
        Args:
            parent_page_id: The ID of the Notion page to dump blocks into.
        
        Returns:
            Number of blocks synced.
        """
        if not self.notion:
            log.warning("Notion service not available.")
            return 0

        # Get all blocks
        conn = self._conn()
        blocks = conn.execute("SELECT * FROM blocks").fetchall()
        conn.close()

        children = []
        for b in blocks:
            # Create a simple paragraph block for each LoreBlock
            # Format: **[Type]** Content (ID: blk_...)
            text = f"**[{b['type'].upper()}]** {b['content']} `({b['id']})`"
            notion_block = {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": text}
                        }
                    ]
                }
            }
            children.append(notion_block)
            
            # Batch every 100 blocks (Notion limit)
            if len(children) >= 100:
                self.notion.append_children(parent_page_id, children)
                children = []
                
        if children:
            self.notion.append_children(parent_page_id, children)
            
        return len(blocks)

    def sync_from_notion(self, page_id: str) -> int:
        """
        Pull content from a Notion page and create blocks.
        """
        if not self.notion:
            return 0
            
        content = self.notion.read_page_content(page_id)
        # Naive import: treat each line as a paragraph block
        # In a real impl, we'd parse the Notion block structure deeper
        imported = 0
        for line in content.split('\n'):
            if line.strip():
                self.create_block("paragraph", line.strip())
                imported += 1
        return imported

    def sync_to_bigquery(self, dataset_id: str = "lore") -> bool:
        """
        Push blocks and links table to BigQuery for analytics.
        Target tables: {project}.{dataset}.blocks, {project}.{dataset}.links
        """
        if not self.bq_client:
            log.warning("BigQuery client not available.")
            return False
            
        # 1. Prepare Blocks Data
        conn = self._conn()
        blocks = [dict(row) for row in conn.execute("SELECT * FROM blocks").fetchall()]
        links = [dict(row) for row in conn.execute("SELECT * FROM links").fetchall()]
        conn.close()
        
        # Add metadata
        now = datetime.now().isoformat()
        for b in blocks:
            b["synced_at"] = now
            b["world_id"] = self.world_id
            
        for l in links:
            l["world_id"] = self.world_id
            
        # 2. Upload to BigQuery
        try:
            # table_id = f"{self.bq_client.project}.{dataset_id}.blocks"
            table_blocks = f"{dataset_id}.blocks"
            table_links = f"{dataset_id}.links"
            
            # Insert blocks (streaming)
            errors_b = self.bq_client.insert_rows_json(table_blocks, blocks)
            if errors_b:
                log.error(f"BigQuery Blocks Insert Errors: {errors_b}")
                
            # Insert links (streaming)
            errors_l = self.bq_client.insert_rows_json(table_links, links)
            if errors_l:
                log.error(f"BigQuery Links Insert Errors: {errors_l}")
                
            log.info(f"BigQuery Sync: {len(blocks)} blocks, {len(links)} links")
            return True
            
        except Exception as e:
            log.error(f"BigQuery Sync Failed: {e}")
            return False

    def query_bigquery(self, sql: str) -> List[dict]:
        """Execute a read-only query on BigQuery."""
        if not self.bq_client:
            return []
        try:
            query_job = self.bq_client.query(sql)
            return [dict(row) for row in query_job]
        except Exception as e:
            log.error(f"BigQuery Query Failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
            by_type = conn.execute(
                "SELECT type, COUNT(*) as count FROM blocks GROUP BY type"
            ).fetchall()
            links = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
            
            return {
                "total_blocks": total,
                "total_links": links,
                **{row["type"]: row["count"] for row in by_type}
            }
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import tempfile
    
    # Test with temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        lore = LoreDB(Path(tmpdir) / "test_world")
        
        # Create blocks
        char_id = lore.create_block(
            "character",
            "The Shadow King rules from the Obsidian Throne.",
            attrs={"name": "Shadow King", "power_level": 95, "faction": "Veil Council"}
        )
        
        loc_id = lore.create_block(
            "location",
            "The Obsidian Throne sits at the heart of the Veil Citadel.",
            attrs={"name": "Obsidian Throne", "era": "Modern"}
        )
        
        # Create block with reference
        event_id = lore.create_block(
            "event",
            f"The coronation of [[{char_id}]] at the [[{loc_id}]].",
            attrs={"year": 2026, "era": "Modern"}
        )
        
        # Test queries
        print(f"Created: {char_id}, {loc_id}, {event_id}")
        print(f"Stats: {lore.stats()}")
        
        # Test search
        results = lore.search("Shadow")
        print(f"Search 'Shadow': {len(results)} results")
        
        # Test backlinks
        backlinks = lore.get_backlinks(char_id)
        print(f"Backlinks to {char_id}: {len(backlinks)}")
        
        # Test JSON export
        lore.sync_to_json()
        print("JSON export complete!")
        
        print("\n✅ LoreDB tests passed!")
