import os
from google.cloud import bigquery
from google.cloud import aiplatform
import pandas as pd
from typing import List, Dict, Any, Optional

class BigQueryVectorStore:
    def __init__(self, project_id: str, location: str):
        self.project_id = project_id
        self.location = location
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = "dav1d_memory"
        self.table_id = "embeddings"
        
        aiplatform.init(project=project_id, location=location)

    def initialize_dataset(self):
        """Ensures the dataset and table exist."""
        dataset_ref = self.client.dataset(self.dataset_id)
        try:
            self.client.get_dataset(dataset_ref)
            print(f"Dataset {self.dataset_id} already exists.")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            self.client.create_dataset(dataset)
            print(f"Created dataset {self.dataset_id}.")

        table_ref = dataset_ref.table(self.table_id)
        try:
            self.client.get_table(table_ref)
            print(f"Table {self.table_id} already exists.")
        except Exception:
            schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            ]
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Created table {self.table_id}.")

    def get_embedding(self, text: str) -> List[float]:
        """Generates embedding using Vertex AI."""
        from vertexai.language_models import TextEmbeddingModel
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        embeddings = model.get_embeddings([text])
        return embeddings[0].values

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Adds a text memory with its embedding to BigQuery."""
        import uuid
        import json
        
        embedding = self.get_embedding(text)
        row = {
            "id": str(uuid.uuid4()),
            "content": text,
            "metadata": json.dumps(metadata) if metadata else None,
            "embedding": embedding
        }
        
        errors = self.client.insert_rows_json(f"{self.project_id}.{self.dataset_id}.{self.table_id}", [row])
        if errors:
            print(f"Encountered errors while inserting rows: {errors}")
        else:
            print("Memory added successfully.")

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for similar memories using vector search."""
        query_embedding = self.get_embedding(query)
        
        # SQL for vector search using cosine distance
        sql = f"""
        SELECT
            id,
            content,
            metadata,
            1 - COSINE_DISTANCE(embedding, {query_embedding}) as similarity
        FROM
            `{self.project_id}.{self.dataset_id}.{self.table_id}`
        ORDER BY
            similarity DESC
        LIMIT {limit}
        """
        
        query_job = self.client.query(sql)
        results = []
        for row in query_job:
            results.append({
                "id": row.id,
                "content": row.content,
                "metadata": row.metadata,
                "similarity": row.similarity
            })
        return results

# Tool function wrapper
def search_codebase_semantically(query: str) -> str:
    """
    Searches the codebase/memory semantically using BigQuery Vector Search.
    Useful for finding code patterns, understanding context, or recalling past decisions.
    """
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    
    if not project_id:
        return "Error: PROJECT_ID environment variable not set."
        
    store = BigQueryVectorStore(project_id, location)
    # Ensure initialized (lazy init)
    # store.initialize_dataset() # Commented out to avoid overhead on every search, assume init done
    
    results = store.search_similar(query)
    
    if not results:
        return "No relevant memories found."
        
    output = "Found relevant memories:\n"
    for r in results:
        output += f"- [Similarity: {r['similarity']:.2f}] {r['content'][:200]}...\n"
        if r['metadata']:
             output += f"  Metadata: {r['metadata']}\n"
    
    return output
