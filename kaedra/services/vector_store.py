"""
KAEDRA v0.0.6 - Vector Store Service
BigQuery-based semantic search using Gemini embeddings.
Ported from Dav1d's vector_store_bigquery.py
"""

import os
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from google.cloud import bigquery
from google import genai

from ..core.config import PROJECT_ID, LOCATION


class BigQueryVectorStore:
    """
    Vector store backed by BigQuery with Gemini embeddings.
    
    Features:
    - Semantic search using gemini-embedding-001
    - Cosine similarity ranking
    - Automatic dataset/table initialization
    - Metadata support
    """
    
    def __init__(
        self, 
        project_id: str = None, 
        location: str = None,
        dataset_id: str = "kaedra_memory",
        table_id: str = "embeddings"
    ):
        self.project_id = project_id or PROJECT_ID
        self.location = location or LOCATION
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        
        # Initialize clients
        self._bq_client = None
        self._genai_client = None
        self._initialized = False
    
    @property
    def bq_client(self) -> bigquery.Client:
        """Lazy-load BigQuery client."""
        if self._bq_client is None:
            self._bq_client = bigquery.Client(project=self.project_id)
        return self._bq_client
    
    @property
    def genai_client(self) -> genai.Client:
        """Lazy-load Gen AI client."""
        if self._genai_client is None:
            self._genai_client = genai.Client(
                vertexai=True, 
                project=self.project_id, 
                location=self.location
            )
        return self._genai_client
    
    def initialize_dataset(self) -> bool:
        """
        Ensure the dataset and table exist.
        Returns True if successful.
        """
        if self._initialized:
            return True
            
        try:
            # Create dataset if needed
            dataset_ref = self.bq_client.dataset(self.dataset_id)
            try:
                self.bq_client.get_dataset(dataset_ref)
            except Exception:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = self.location
                self.bq_client.create_dataset(dataset)
                print(f"[VectorStore] Created dataset {self.dataset_id}")
            
            # Create table if needed
            table_ref = dataset_ref.table(self.table_id)
            try:
                self.bq_client.get_table(table_ref)
            except Exception:
                schema = [
                    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("topic", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("tags", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("importance", "STRING", mode="NULLABLE"),
                    bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                    bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
                    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
                ]
                table = bigquery.Table(table_ref, schema=schema)
                self.bq_client.create_table(table)
                print(f"[VectorStore] Created table {self.table_id}")
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"[VectorStore] Initialization failed: {e}")
            return False
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using gemini-embedding-001.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self.genai_client.models.embed_content(
                model="gemini-embedding-001",
                contents=text
            )
            return list(result.embeddings[0].values)
        except Exception as e:
            print(f"[VectorStore] Embedding failed: {e}")
            return []
    
    def add_memory(
        self, 
        content: str, 
        topic: str = "general",
        tags: List[str] = None,
        importance: str = "normal",
        metadata: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Add a memory with its embedding to BigQuery.
        
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.initialize_dataset():
            return None
            
        embedding = self.get_embedding(content)
        if not embedding:
            return None
        
        memory_id = f"vec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        row = {
            "id": memory_id,
            "content": content,
            "topic": topic,
            "tags": ",".join(tags) if tags else "",
            "importance": importance,
            "metadata": json.dumps(metadata) if metadata else None,
            "embedding": embedding,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            errors = self.bq_client.insert_rows_json(self.full_table_id, [row])
            if errors:
                print(f"[VectorStore] Insert error: {errors}")
                return None
            return memory_id
        except Exception as e:
            print(f"[VectorStore] Add memory failed: {e}")
            return None
    
    def search_similar(
        self, 
        query: str, 
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar memories.
        
        Args:
            query: Search query
            limit: Max results to return
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of matching memories with similarity scores
        """
        if not self.initialize_dataset():
            return []
            
        query_embedding = self.get_embedding(query)
        if not query_embedding:
            return []
        
        # SQL for vector search using cosine distance
        sql = f"""
        SELECT
            id,
            content,
            topic,
            tags,
            importance,
            metadata,
            timestamp,
            1 - COSINE_DISTANCE(embedding, {query_embedding}) as similarity
        FROM
            `{self.full_table_id}`
        WHERE
            1 - COSINE_DISTANCE(embedding, {query_embedding}) >= {min_similarity}
        ORDER BY
            similarity DESC
        LIMIT {limit}
        """
        
        try:
            results = []
            for row in self.bq_client.query(sql):
                results.append({
                    "id": row.id,
                    "content": row.content,
                    "topic": row.topic,
                    "tags": row.tags.split(",") if row.tags else [],
                    "importance": row.importance,
                    "metadata": row.metadata,
                    "timestamp": str(row.timestamp),
                    "similarity": float(row.similarity)
                })
            return results
        except Exception as e:
            print(f"[VectorStore] Search failed: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            sql = f"DELETE FROM `{self.full_table_id}` WHERE id = '{memory_id}'"
            self.bq_client.query(sql).result()
            return True
        except Exception as e:
            print(f"[VectorStore] Delete failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        try:
            sql = f"""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT topic) as topics,
                MIN(timestamp) as oldest,
                MAX(timestamp) as newest
            FROM `{self.full_table_id}`
            """
            for row in self.bq_client.query(sql):
                return {
                    "total": row.total,
                    "topics": row.topics,
                    "oldest": str(row.oldest) if row.oldest else None,
                    "newest": str(row.newest) if row.newest else None,
                    "backend": "BigQuery"
                }
        except Exception as e:
            return {"error": str(e), "backend": "BigQuery"}


# Singleton instance for easy access
_vector_store: Optional[BigQueryVectorStore] = None

def get_vector_store() -> BigQueryVectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = BigQueryVectorStore()
    return _vector_store
