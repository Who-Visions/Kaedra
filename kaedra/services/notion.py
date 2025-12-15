"""
KAEDRA v0.0.6 - Notion Service
Two-way sync with Notion for memory and notes.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging
import hashlib

try:
    from notion_client import Client as NotionClient
    from notion_client import AsyncClient as AsyncNotionClient
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    NotionClient = None
    AsyncNotionClient = None

from ..core.exceptions import NotionError, ServiceError


logger = logging.getLogger("kaedra.services.notion")


@dataclass
class NotionPage:
    """Represents a Notion page."""
    id: str
    title: str
    content: str
    url: str
    created_time: str
    last_edited_time: str
    properties: Dict[str, Any]


class NotionService:
    """
    Notion integration service.
    
    Features:
    - Page reading and writing
    - Database queries
    - Memory sync (Notion <-> KAEDRA memory)
    - Webhook handling (when server mode enabled)
    """
    
    def __init__(
        self,
        integration_token: str,
        memory_service = None,
        logging_service = None,
        database_id: str = None
    ):
        if not NOTION_AVAILABLE:
            raise NotionError("notion-client not installed. Run: pip install notion-client")
        
        self.token = integration_token
        self.memory = memory_service
        self.logger = logging_service
        self.database_id = database_id
        
        self._client = NotionClient(auth=integration_token)
        self._async_client = None
        
        # Sync state
        self._last_sync: Optional[datetime] = None
        self._sync_hashes: Dict[str, str] = {}
    
    def _get_async_client(self) -> AsyncNotionClient:
        """Get or create async client."""
        if self._async_client is None:
            self._async_client = AsyncNotionClient(auth=self.token)
        return self._async_client
    
    def _content_hash(self, content: str) -> str:
        """Generate hash of content for change detection."""
        return hashlib.md5(content.encode()).hexdigest()
    
    # ══════════════════════════════════════════════════════════════════════════
    # PAGE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════
    
    def get_page(self, page_id: str) -> NotionPage:
        """Retrieve a page by ID."""
        try:
            page = self._client.pages.retrieve(page_id=page_id)
            
            # Get page content (blocks)
            blocks = self._client.blocks.children.list(block_id=page_id)
            content = self._blocks_to_text(blocks.get("results", []))
            
            # Extract title from properties
            title = self._extract_title(page.get("properties", {}))
            
            return NotionPage(
                id=page_id,
                title=title,
                content=content,
                url=page.get("url", ""),
                created_time=page.get("created_time", ""),
                last_edited_time=page.get("last_edited_time", ""),
                properties=page.get("properties", {})
            )
        
        except Exception as e:
            raise NotionError(f"Failed to get page {page_id}: {e}")
    
    async def get_page_async(self, page_id: str) -> NotionPage:
        """Async version of get_page."""
        client = self._get_async_client()
        
        try:
            page = await client.pages.retrieve(page_id=page_id)
            blocks = await client.blocks.children.list(block_id=page_id)
            content = self._blocks_to_text(blocks.get("results", []))
            title = self._extract_title(page.get("properties", {}))
            
            return NotionPage(
                id=page_id,
                title=title,
                content=content,
                url=page.get("url", ""),
                created_time=page.get("created_time", ""),
                last_edited_time=page.get("last_edited_time", ""),
                properties=page.get("properties", {})
            )
        
        except Exception as e:
            raise NotionError(f"Failed to get page {page_id}: {e}")
    
    def create_page(
        self,
        title: str,
        content: str,
        parent_id: str = None,
        properties: Dict[str, Any] = None
    ) -> str:
        """
        Create a new page in Notion.
        
        Args:
            title: Page title
            content: Page content (plain text or markdown-like)
            parent_id: Parent page or database ID (uses default DB if not provided)
            properties: Additional page properties
        
        Returns:
            New page ID
        """
        parent_id = parent_id or self.database_id
        if not parent_id:
            raise NotionError("No parent_id provided and no default database configured")
        
        try:
            # Build page structure
            page_data = {
                "parent": {"database_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    },
                    **(properties or {})
                },
                "children": self._text_to_blocks(content)
            }
            
            response = self._client.pages.create(**page_data)
            page_id = response.get("id")
            
            logger.info(f"Created Notion page: {title} ({page_id})")
            return page_id
        
        except Exception as e:
            raise NotionError(f"Failed to create page: {e}")
    
    def update_page(
        self,
        page_id: str,
        content: str = None,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Update an existing page."""
        try:
            if properties:
                self._client.pages.update(page_id=page_id, properties=properties)
            
            if content:
                # Clear existing blocks and add new ones
                existing = self._client.blocks.children.list(block_id=page_id)
                for block in existing.get("results", []):
                    try:
                        self._client.blocks.delete(block_id=block["id"])
                    except:
                        pass
                
                # Add new blocks
                self._client.blocks.children.append(
                    block_id=page_id,
                    children=self._text_to_blocks(content)
                )
            
            logger.info(f"Updated Notion page: {page_id}")
            return True
        
        except Exception as e:
            raise NotionError(f"Failed to update page {page_id}: {e}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # DATABASE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════
    
    def query_database(
        self,
        database_id: str = None,
        filter_obj: Dict[str, Any] = None,
        sorts: List[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[NotionPage]:
        """Query a Notion database."""
        db_id = database_id or self.database_id
        if not db_id:
            raise NotionError("No database_id provided and no default configured")
        
        try:
            query_params = {"database_id": db_id, "page_size": min(limit, 100)}
            
            if filter_obj:
                query_params["filter"] = filter_obj
            if sorts:
                query_params["sorts"] = sorts
            
            response = self._client.databases.query(**query_params)
            
            pages = []
            for result in response.get("results", []):
                title = self._extract_title(result.get("properties", {}))
                pages.append(NotionPage(
                    id=result["id"],
                    title=title,
                    content="",  # Content not loaded in queries
                    url=result.get("url", ""),
                    created_time=result.get("created_time", ""),
                    last_edited_time=result.get("last_edited_time", ""),
                    properties=result.get("properties", {})
                ))
            
            return pages
        
        except Exception as e:
            raise NotionError(f"Failed to query database: {e}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # MEMORY SYNC
    # ══════════════════════════════════════════════════════════════════════════
    
    def sync_page_to_memory(self, page_id: str) -> str:
        """
        Sync a Notion page to KAEDRA memory.
        
        Returns:
            Memory entry ID
        """
        if not self.memory:
            raise NotionError("Memory service not configured")
        
        page = self.get_page(page_id)
        
        # Check if content changed
        content_hash = self._content_hash(page.content)
        if self._sync_hashes.get(page_id) == content_hash:
            logger.debug(f"Page {page_id} unchanged, skipping sync")
            return None
        
        # Store in memory
        memory_id = self.memory.insert(
            topic=page.title,
            content=page.content,
            tags=["notion", "sync"],
            source="notion",
            metadata={
                "notion_page_id": page_id,
                "notion_url": page.url,
                "synced_at": datetime.now().isoformat()
            }
        )
        
        self._sync_hashes[page_id] = content_hash
        self._last_sync = datetime.now()
        
        logger.info(f"Synced Notion page to memory: {page.title}")
        return memory_id
    
    def sync_memory_to_page(self, memory_id: str, page_id: str = None) -> str:
        """
        Sync a memory entry to Notion.
        
        Args:
            memory_id: KAEDRA memory entry ID
            page_id: Existing Notion page to update (creates new if None)
        
        Returns:
            Notion page ID
        """
        if not self.memory:
            raise NotionError("Memory service not configured")
        
        entry = self.memory.get(memory_id)
        if not entry:
            raise NotionError(f"Memory entry not found: {memory_id}")
        
        if page_id:
            self.update_page(page_id, content=entry.content)
            return page_id
        else:
            return self.create_page(
                title=entry.topic,
                content=entry.content,
                properties={
                    "Tags": {"multi_select": [{"name": tag} for tag in entry.tags]}
                } if entry.tags else None
            )
    
    async def sync_database_to_memory(self, database_id: str = None) -> int:
        """
        Sync all pages in a database to memory.
        
        Returns:
            Number of pages synced
        """
        pages = self.query_database(database_id)
        count = 0
        
        for page in pages:
            try:
                full_page = await self.get_page_async(page.id)
                
                self.memory.insert(
                    topic=full_page.title,
                    content=full_page.content,
                    tags=["notion", "sync"],
                    source="notion",
                    metadata={
                        "notion_page_id": full_page.id,
                        "notion_url": full_page.url
                    }
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to sync page {page.id}: {e}")
        
        self._last_sync = datetime.now()
        return count
    
    # ══════════════════════════════════════════════════════════════════════════
    # WEBHOOK HANDLING
    # ══════════════════════════════════════════════════════════════════════════
    
    async def handle_webhook(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming Notion webhook event.
        
        Args:
            event_payload: Webhook payload from Notion
        
        Returns:
            Processing result
        """
        event_type = event_payload.get("type")
        page_id = event_payload.get("page", {}).get("id")
        
        logger.info(f"Received Notion webhook: {event_type} for {page_id}")
        
        if event_type == "page.created":
            if self.memory and page_id:
                memory_id = self.sync_page_to_memory(page_id)
                return {"action": "synced_to_memory", "memory_id": memory_id}
        
        elif event_type == "page.updated":
            if self.memory and page_id:
                memory_id = self.sync_page_to_memory(page_id)
                return {"action": "updated_memory", "memory_id": memory_id}
        
        elif event_type == "page.deleted":
            # Optionally mark memory as stale
            return {"action": "noted_deletion", "page_id": page_id}
        
        return {"action": "ignored", "event_type": event_type}
    
    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════
    
    def _extract_title(self, properties: Dict[str, Any]) -> str:
        """Extract title from Notion properties."""
        # Try common title property names
        for key in ["title", "Title", "Name", "name"]:
            if key in properties:
                prop = properties[key]
                if prop.get("type") == "title":
                    title_items = prop.get("title", [])
                    if title_items:
                        return title_items[0].get("text", {}).get("content", "Untitled")
        return "Untitled"
    
    def _blocks_to_text(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert Notion blocks to plain text."""
        lines = []
        
        for block in blocks:
            block_type = block.get("type")
            block_data = block.get(block_type, {})
            
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
                rich_text = block_data.get("rich_text", [])
                text = "".join(t.get("text", {}).get("content", "") for t in rich_text)
                
                if block_type == "heading_1":
                    lines.append(f"# {text}")
                elif block_type == "heading_2":
                    lines.append(f"## {text}")
                elif block_type == "heading_3":
                    lines.append(f"### {text}")
                else:
                    lines.append(text)
            
            elif block_type == "bulleted_list_item":
                rich_text = block_data.get("rich_text", [])
                text = "".join(t.get("text", {}).get("content", "") for t in rich_text)
                lines.append(f"• {text}")
            
            elif block_type == "numbered_list_item":
                rich_text = block_data.get("rich_text", [])
                text = "".join(t.get("text", {}).get("content", "") for t in rich_text)
                lines.append(f"1. {text}")
            
            elif block_type == "code":
                rich_text = block_data.get("rich_text", [])
                text = "".join(t.get("text", {}).get("content", "") for t in rich_text)
                lang = block_data.get("language", "")
                lines.append(f"```{lang}\n{text}\n```")
            
            elif block_type == "divider":
                lines.append("---")
        
        return "\n\n".join(lines)
    
    def _text_to_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Convert plain text to Notion blocks."""
        blocks = []
        
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("# "):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith("## "):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith("### "):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            elif line.startswith("• ") or line.startswith("- "):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line == "---":
                blocks.append({
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": line}}]
                    }
                })
        
        return blocks
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status information."""
        return {
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "tracked_pages": len(self._sync_hashes),
            "database_configured": bool(self.database_id),
            "memory_connected": bool(self.memory)
        }
