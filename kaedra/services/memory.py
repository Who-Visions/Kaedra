"""
KAEDRA v0.0.6 - Memory Service
Persistent memory storage and retrieval with hybrid keyword + semantic search.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from ..core.config import MEMORY_DIR

# Optional vector store for semantic search
try:
    from .vector_store import get_vector_store, BigQueryVectorStore
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    topic: str
    content: str
    tags: List[str]
    timestamp: str
    importance: str = "normal"  # low, normal, high, critical
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MemoryEntry':
        return cls(**data)


class MemoryService:
    """
    Manages persistent memory storage and retrieval.
    
    Features:
    - JSON-based local storage
    - Keyword search with scoring
    - Semantic search via BigQuery vector store (optional)
    - Hybrid search combining keyword + semantic
    - Tag-based filtering
    - Importance levels
    - Recent memory listing
    """
    
    def __init__(self, db_path: Optional[Path] = None, enable_semantic: bool = True):
        self.db_path = db_path or MEMORY_DIR
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.db_path / "memory_index.json"
        self._index: List[Dict] = self._load_index()
        
        # Initialize vector store for semantic search
        self.vector_store: Optional[BigQueryVectorStore] = None
        self.semantic_enabled = False
        
        if enable_semantic and VECTOR_STORE_AVAILABLE:
            try:
                self.vector_store = get_vector_store()
                self.semantic_enabled = True
                print("[Memory] Semantic search enabled (BigQuery)")
            except Exception as e:
                print(f"[Memory] Semantic search unavailable: {e}")
    
    def _load_index(self) -> List[Dict]:
        """Load the memory index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_index(self):
        """Save the memory index to disk."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)
    
    def insert(self, content: str, topic: str = "general", 
               tags: List[str] = None, importance: str = "normal",
               metadata: Dict = None) -> str:
        """
        Store a new memory entry.
        
        Args:
            content: The memory content
            topic: Category/topic for the memory
            tags: List of searchable tags
            importance: Priority level (low/normal/high/critical)
            metadata: Additional metadata
            
        Returns:
            The memory ID
        """
        timestamp = datetime.now().isoformat()
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        entry = MemoryEntry(
            id=memory_id,
            topic=topic,
            content=content,
            tags=tags or [],
            timestamp=timestamp,
            importance=importance
        )
        
        # Save individual memory file
        mem_file = self.db_path / f"{memory_id}.json"
        entry_dict = entry.to_dict()
        if metadata:
            entry_dict['metadata'] = metadata
            
        with open(mem_file, 'w', encoding='utf-8') as f:
            json.dump(entry_dict, f, indent=2, ensure_ascii=False)
        
        # Update index
        self._index.append(entry_dict)
        self._save_index()
        
        # Also store in vector store for semantic search
        if self.semantic_enabled and self.vector_store:
            try:
                self.vector_store.add_memory(
                    content=content,
                    topic=topic,
                    tags=tags,
                    importance=importance,
                    metadata={'local_id': memory_id}
                )
            except Exception as e:
                print(f"[Memory] Vector store sync failed: {e}")
        
        return memory_id
    
    def recall(self, query: str, top_k: int = 5, 
               tags: List[str] = None,
               min_importance: str = None) -> List[Dict]:
        """
        Search memory for relevant entries.
        
        Args:
            query: Search query (keywords)
            top_k: Maximum number of results
            tags: Filter by specific tags
            min_importance: Minimum importance level
            
        Returns:
            List of matching memory entries, scored and sorted
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored = []
        
        importance_levels = {'low': 1, 'normal': 2, 'high': 3, 'critical': 4}
        min_imp_value = importance_levels.get(min_importance, 0)
        
        for entry in self._index:
            # Filter by importance
            entry_imp = importance_levels.get(entry.get('importance', 'normal'), 2)
            if entry_imp < min_imp_value:
                continue
            
            # Filter by tags
            if tags:
                entry_tags = set(t.lower() for t in entry.get('tags', []))
                if not any(t.lower() in entry_tags for t in tags):
                    continue
            
            # Score by relevance
            score = 0
            
            # Topic match (high weight)
            topic_lower = entry.get('topic', '').lower()
            if query_lower in topic_lower:
                score += 5
            for word in query_words:
                if word in topic_lower:
                    score += 2
            
            # Content match (medium weight)
            content_lower = entry.get('content', '').lower()
            if query_lower in content_lower:
                score += 3
            for word in query_words:
                if word in content_lower:
                    score += 1
            
            # Tag match (medium weight)
            for tag in entry.get('tags', []):
                tag_lower = tag.lower()
                if query_lower in tag_lower:
                    score += 2
                for word in query_words:
                    if word in tag_lower:
                        score += 1
            
            # Importance boost
            score += entry_imp * 0.5
            
            if score > 0:
                scored.append((score, entry))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]
    
    def list_recent(self, limit: int = 10) -> List[Dict]:
        """Get the most recent memories."""
        sorted_entries = sorted(
            self._index,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        return sorted_entries[:limit]
    
    def get_by_id(self, memory_id: str) -> Optional[Dict]:
        """Retrieve a specific memory by ID."""
        for entry in self._index:
            if entry.get('id') == memory_id:
                return entry
        return None
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory entry."""
        # Remove from index
        self._index = [e for e in self._index if e.get('id') != memory_id]
        self._save_index()
        
        # Remove file
        mem_file = self.db_path / f"{memory_id}.json"
        if mem_file.exists():
            mem_file.unlink()
            return True
        return False
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """Get all memories with a specific tag."""
        tag_lower = tag.lower()
        return [
            entry for entry in self._index
            if any(t.lower() == tag_lower for t in entry.get('tags', []))
        ]
    
    def get_stats(self) -> Dict:
        """Get memory statistics."""
        total = len(self._index)
        by_importance = {}
        by_tag = {}
        
        for entry in self._index:
            imp = entry.get('importance', 'normal')
            by_importance[imp] = by_importance.get(imp, 0) + 1
            
            for tag in entry.get('tags', []):
                by_tag[tag] = by_tag.get(tag, 0) + 1
        
        return {
            'total': total,
            'by_importance': by_importance,
            'top_tags': sorted(by_tag.items(), key=lambda x: x[1], reverse=True)[:10],
            'semantic_enabled': self.semantic_enabled
        }
    
    def semantic_recall(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search memories using semantic similarity (vector search).
        
        Args:
            query: Natural language search query
            top_k: Maximum results to return
            
        Returns:
            List of semantically similar memories with similarity scores
        """
        if not self.semantic_enabled or not self.vector_store:
            return []
        
        try:
            results = self.vector_store.search_similar(query, limit=top_k)
            return results
        except Exception as e:
            print(f"[Memory] Semantic recall failed: {e}")
            return []
    
    def hybrid_recall(
        self, 
        query: str, 
        top_k: int = 5,
        keyword_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> List[Dict]:
        """
        Combine keyword and semantic search for best results.
        
        Args:
            query: Search query
            top_k: Maximum results
            keyword_weight: Weight for keyword scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
            
        Returns:
            Combined and re-ranked list of memories
        """
        # Get keyword results
        keyword_results = self.recall(query, top_k=top_k * 2)
        
        # Get semantic results
        semantic_results = self.semantic_recall(query, top_k=top_k * 2)
        
        # If no semantic, return keyword only
        if not semantic_results:
            return keyword_results[:top_k]
        
        # Merge and score
        combined = {}
        
        # Score keyword results (normalize by max possible ~10)
        max_kw_score = 10.0
        for i, entry in enumerate(keyword_results):
            mem_id = entry.get('id')
            normalized_score = (len(keyword_results) - i) / len(keyword_results)
            combined[mem_id] = {
                'entry': entry,
                'keyword_score': normalized_score * keyword_weight,
                'semantic_score': 0
            }
        
        # Add semantic results
        for result in semantic_results:
            mem_id = result.get('id')
            similarity = result.get('similarity', 0)
            
            if mem_id in combined:
                combined[mem_id]['semantic_score'] = similarity * semantic_weight
            else:
                # Memory only in vector store, not local
                combined[mem_id] = {
                    'entry': result,
                    'keyword_score': 0,
                    'semantic_score': similarity * semantic_weight
                }
        
        # Calculate final scores and sort
        scored = []
        for mem_id, data in combined.items():
            total_score = data['keyword_score'] + data['semantic_score']
            entry = data['entry'].copy()
            entry['hybrid_score'] = total_score
            entry['keyword_score'] = data['keyword_score']
            entry['semantic_score'] = data['semantic_score']
            scored.append((total_score, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

