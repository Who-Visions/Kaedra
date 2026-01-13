from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
from ..services.loredb import LoreDB, LoreBlock

router = APIRouter(prefix="/lore", tags=["Lore"])

# Initialize LoreDB (using a default world for now)
# In a real app, this might be injected or managed via app state
LORE_DB_PATH = Path("data/worlds/default")
lore_db = LoreDB(LORE_DB_PATH)

# Request/Response Models
class LoreItemResponse(BaseModel):
    id: str
    title: str
    category: str
    description: Optional[str] = None
    importance: int = 0
    confidence: int = 100
    source: str = "System"
    timestamp: Optional[str] = None

@router.get("/feed", response_model=List[LoreItemResponse])
async def get_lore_feed(limit: int = 50):
    """
    Get a feed of lore items sorted by importance/updates.
    Currently maps LoreDB blocks to the LoreItem format expected by the frontend.
    """
    # Simple strategy: get all blocks, mock importance if missing
    # Optimized query would be better, but LoreDB is simple for now
    blocks = lore_db.query("SELECT * FROM blocks ORDER BY updated DESC LIMIT ?", (limit,))
    
    return [_map_block_to_item(b) for b in blocks]

@router.get("/weighted", response_model=List[LoreItemResponse])
async def get_weighted_lore(limit: int = 50):
    """
    Get lore items weighted by importance.
    """
    # Try to find blocks with 'importance' attribute, fall back to recent
    blocks = lore_db.query(
        "SELECT * FROM blocks WHERE json_extract(attrs, '$.importance') IS NOT NULL ORDER BY json_extract(attrs, '$.importance') DESC LIMIT ?", 
        (limit,)
    )
    
    if not blocks:
        # Fallback to recent if no tiered stats
        blocks = lore_db.query("SELECT * FROM blocks ORDER BY updated DESC LIMIT ?", (limit,))
        
    return [_map_block_to_item(b) for b in blocks]

@router.get("/search", response_model=List[LoreItemResponse])
async def search_lore(q: str = Query(..., min_length=1), limit: int = 20):
    """
    Search lore blocks.
    """
    blocks = lore_db.search(q, limit=limit)
    return [_map_block_to_item(b) for b in blocks]

@router.get("/{id}", response_model=LoreItemResponse)
async def get_lore_item(id: str):
    """
    Get a single lore item by ID.
    """
    block = lore_db.get_block(id)
    if not block:
        raise HTTPException(status_code=404, detail="Lore item not found")
    return _map_block_to_item(block)

# Helper to map LoreDB block to API response
def _map_block_to_item(block: LoreBlock) -> LoreItemResponse:
    # Attempt to extract title/name from attrs or truncate content
    title = block.attrs.get("name") or block.attrs.get("title")
    if not title:
        # Naive title extraction: first sentence or first few words
        content_clean = block.content.split('\n')[0]
        title = (content_clean[:50] + '...') if len(content_clean) > 50 else content_clean
    
    return LoreItemResponse(
        id=block.id,
        title=title,
        category=block.type,
        description=block.content,
        importance=int(block.attrs.get("importance", 0)),
        confidence=int(block.attrs.get("confidence", 100)),
        source=block.attrs.get("source", "LoreDB"),
        timestamp=block.updated
    )
