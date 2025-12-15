# Kaedra Enhanced Memory Architecture
# Project: WhoBanana (gen-lang-client-0939852539)
# Region: us-central1

## 🧠 Memory System Architecture

### Memory Types

#### 1. **SHORT-TERM MEMORY** (Async, Fast, Temporary)
- **Table**: `memory_short_term`
- **Purpose**: Active session memory, rapid context switching
- **Retention**: 7 days (auto-expires)
- **Chunk Size**: 1k tokens max
- **Access Pattern**: Async read/write, millisecond latency

**Schema**:
```
chunk_id:STRING       - Unique chunk ID
session_id:STRING     - Session identifier
content:STRING        - Memory content (≤1k tokens)
tokens:INTEGER        - Token count
embedding:STRING      - Vector embedding (JSON)
timestamp:TIMESTAMP   - When created
ttl:TIMESTAMP         - Expiration time
metadata:STRING       - JSON metadata
```

**Use Cases**:
- Current conversation context
- Recent tool calls and results
- Active task tracking
- Session state

#### 2. **LONG-TERM MEMORY** (Persistent, Indexed, Chunked)
- **Table**: `memory_long_term`
- **Purpose**: Permanent knowledge, important conversations
- **Retention**: Infinite
- **Chunk Size**: 1k tokens (with chunking metadata)
- **Access Pattern**: Indexed retrieval, semantic search

**Schema**:
```
chunk_id:STRING       - Unique chunk ID
topic:STRING          - Memory topic
content:STRING        - Chunk content (≤1k tokens)
tokens:INTEGER        - Token count
chunk_index:INTEGER   - Position in sequence (0, 1, 2...)
total_chunks:INTEGER  - Total chunks for this memory
importance:STRING     - low, normal, high, critical
tags:STRING           - Comma-separated tags
embedding:STRING      - Vector embedding (JSON)
timestamp:TIMESTAMP   - When created
metadata:STRING       - JSON metadata
```

**Use Cases**:
- Strategic decisions
- Critical learnings
- User preferences
- Historical context

#### 3. **KNOWLEDGE BASE** (RAG, Chunked Documents)
- **Table**: `knowledge`
- **Purpose**: External knowledge, documents, research
- **Retention**: Infinite
- **Chunk Size**: 1k tokens (with source tracking)
- **Access Pattern**: Vector similarity search

**Schema**:
```
chunk_id:STRING       - Unique chunk ID
doc_id:STRING         - Document identifier
title:STRING          - Document title
content:STRING        - Chunk content (≤1k tokens)
tokens:INTEGER        - Token count
chunk_index:INTEGER   - Position in document
source:STRING         - Source URL/reference
embedding:STRING      - Vector embedding (JSON)
timestamp:TIMESTAMP   - When ingested
metadata:STRING       - JSON metadata
```

---

## ⚡ Async Memory Operations

### Write Pattern (Non-blocking)
```python
import asyncio
from google.cloud import bigquery
from datetime import datetime, timedelta

async def async_write_short_term(session_id: str, content: str, tokens: int):
    """Non-blocking write to short-term memory."""
    client = bigquery.Client(project="gen-lang-client-0939852539")
    
    row = {
        "chunk_id": f"stm_{datetime.now().timestamp()}",
        "session_id": session_id,
        "content": content,
        "tokens": tokens,
        "embedding": "[]",  # Embed async later
        "timestamp": datetime.now().isoformat(),
        "ttl": (datetime.now() + timedelta(days=7)).isoformat(),
        "metadata": "{}"
    }
    
    table = "gen-lang-client-0939852539.kaedra_memory.memory_short_term"
    
    # Fire and forget
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, client.insert_rows_json, table, [row])
```

### Read Pattern (Streaming)
```python
async def async_read_recent(session_id: str, limit: int = 10):
    """Stream recent memories for context."""
    client = bigquery.Client(project="gen-lang-client-0939852539")
    
    query = f"""
        SELECT content, tokens, timestamp
        FROM `gen-lang-client-0939852539.kaedra_memory.memory_short_term`
        WHERE session_id = @session_id
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
        ]
    )
    
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: list(client.query(query, job_config=job_config)))
    
    return [dict(row) for row in results]
```

---

## 📦 1k Token Chunking

### Chunking Strategy

**Algorithm**:
1. Token count input text
2. If ≤ 1000 tokens → Single chunk
3. If > 1000 tokens → Split at 1000 token boundaries
4. Preserve sentence boundaries when possible

**Implementation**:
```python
import tiktoken

def chunk_content(content: str, max_tokens: int = 1000) -> list[dict]:
    """Chunk content into 1k token pieces."""
    encoder = tiktoken.encoding_for_model("gpt-4")
    tokens = encoder.encode(content)
    
    chunks = []
    total_chunks = (len(tokens) + max_tokens - 1) // max_tokens
    
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_text = encoder.decode(chunk_tokens)
        
        chunks.append({
            "content": chunk_text,
            "tokens": len(chunk_tokens),
            "chunk_index": i // max_tokens,
            "total_chunks": total_chunks
        })
    
    return chunks
```

### Storage Example
```python
async def store_long_term_chunked(topic: str, content: str, importance: str = "normal"):
    """Store long-term memory with chunking."""
    chunks = chunk_content(content)
    chunk_id_base = f"ltm_{datetime.now().timestamp()}"
    
    rows = []
    for i, chunk in enumerate(chunks):
        rows.append({
            "chunk_id": f"{chunk_id_base}_chunk{i}",
            "topic": topic,
            "content": chunk["content"],
            "tokens": chunk["tokens"],
            "chunk_index": i,
            "total_chunks": len(chunks),
            "importance": importance,
            "tags": "",
            "embedding": "[]",
            "timestamp": datetime.now().isoformat(),
            "metadata": "{}"
        })
    
    client = bigquery.Client(project="gen-lang-client-0939852539")
    table = "gen-lang-client-0939852539.kaedra_memory.memory_long_term"
    
    await asyncio.get_event_loop().run_in_executor(
        None, client.insert_rows_json, table, rows
    )
```

---

## 🔄 Migration from Current System

### Current (JSON Files)
```
~/.kaedra/memory/
  memory_index.json
  memory_001.json
  memory_002.json
```

### New (Hybrid: BigQuery + GCS)
```
BigQuery: Structured, indexed, searchable
GCS: Backups, archives, async offload

Short-term: Active session (7 days)
Long-term: Permanent (chunked)
```

---

## 🚀 Setup Commands

**Run in Cloud Shell**:
```bash
bash SETUP_ENHANCED_MEMORY.sh
```

This creates:
- ✅ Short-term memory (7-day TTL, async)
- ✅ Long-term memory (permanent, chunked)
- ✅ Knowledge base (RAG, chunked)
- ✅ Storage buckets (async offload)

---

**Last Updated**: 2025-12-14
**Architecture**: Async + Short/Long-term + 1k Chunking
