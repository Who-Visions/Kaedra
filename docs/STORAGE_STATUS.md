# ✅ Kaedra Storage Setup - Status Report

## Project Configuration
- **Project**: WhoBanana (`gen-lang-client-0939852539`)
- **Region**: `us-central1`
- **Quota Project**: ✅ Set in ADC
- **Date**: 2025-12-14

---

## ✅ Created Resources

### Cloud Storage Buckets
1. ✅ **`gs://gen-lang-client-0939852539-images`**
   - Location: US-CENTRAL1
   - Created: 2025-12-14 22:36:08 UTC
   - Purpose: Generated images storage

2. ✅ **`gs://gen-lang-client-0939852539-knowledge`**
   - Location: US-CENTRAL1
   - Purpose: Knowledge base documents

3. ✅ **`gs://gen-lang-client-0939852539-memory-async`**
   - Location: US-CENTRAL1
   - Purpose: Async memory offload

4. ✅ **`gs://gen-lang-client-0939852539-videos`**
   - Location: US-CENTRAL1
   - Purpose: Generated videos storage

### BigQuery Dataset
- ✅ **`kaedra_memory`** dataset created

### BigQuery Tables (Attempted)
Note: `bq` CLI has a known bug with `absl.flags`. Tables may need manual creation via Cloud Console.

**Required tables**:
1. `memory_short_term` - 7-day TTL, async operations
2. `memory_long_term` - Persistent, chunked at 1k tokens
3. `knowledge` - RAG knowledge base

---

## 🔧 Next Steps

### 1. Create BigQuery Tables Manually

Go to [BigQuery Console](https://console.cloud.google.com/bigquery?project=gen-lang-client-0939852539)

**Create `memory_short_term`**:
```sql
CREATE TABLE `gen-lang-client-0939852539.kaedra_memory.memory_short_term`
(
  chunk_id STRING,
  session_id STRING,
  content STRING,
  tokens INT64,
  embedding STRING,
  timestamp TIMESTAMP,
  ttl TIMESTAMP,
  metadata STRING
)
PARTITION BY DATE(timestamp)
OPTIONS(
  partition_expiration_days=7
)
```

**Create `memory_long_term`**:
```sql
CREATE TABLE `gen-lang-client-0939852539.kaedra_memory.memory_long_term`
(
  chunk_id STRING,
  topic STRING,
  content STRING,
  tokens INT64,
  chunk_index INT64,
  total_chunks INT64,
  importance STRING,
  tags STRING,
  embedding STRING,
  timestamp TIMESTAMP,
  metadata STRING
)
```

**Create `knowledge`**:
```sql
CREATE TABLE `gen-lang-client-0939852539.kaedra_memory.knowledge`
(
  chunk_id STRING,
  doc_id STRING,
  title STRING,
  content STRING,
  tokens INT64,
  chunk_index INT64,
  source STRING,
  embedding STRING,
  timestamp TIMESTAMP,
  metadata STRING
)
```

### 2. Update Kaedra Code

Add to `kaedra/core/config.py`:

```python
# BigQuery Configuration
BQ_DATASET = "kaedra_memory"
BQ_SHORT_TERM = f"{PROJECT_ID}.{BQ_DATASET}.memory_short_term"
BQ_LONG_TERM = f"{PROJECT_ID}.{BQ_DATASET}.memory_long_term"
BQ_KNOWLEDGE = f"{PROJECT_ID}.{BQ_DATASET}.knowledge"

# Cloud Storage Buckets
BUCKET_IMAGES = f"gs://{PROJECT_ID}-images"
BUCKET_VIDEOS = f"gs://{PROJECT_ID}-videos"
BUCKET_KNOWLEDGE = f"gs://{PROJECT_ID}-knowledge"
BUCKET_MEMORY_ASYNC = f"gs://{PROJECT_ID}-memory-async"
```

---

## 📊 Storage Summary

| Resource Type | Name | Location | Status |
|--------------|------|----------|--------|
| Dataset | kaedra_memory | us-central1 | ✅ Created |
| Bucket | images | us-central1 | ✅ Created |
| Bucket | knowledge | us-central1 | ✅ Created |
| Bucket | memory-async | us-central1 | ✅ Created |
| Bucket | videos | us-central1 | ✅ Created |
| Table | memory_short_term | us-central1 | ⚠️ Manual |
| Table | memory_long_term | us-central1 | ⚠️ Manual |
| Table | knowledge | us-central1 | ⚠️ Manual |

---

## 🐛 Known Issues

**`bq` CLI Error**: 
```
AttributeError: module 'absl.flags' has no attribute 'FLAGS'
```

**Workaround**: Use BigQuery Console UI for table creation (see SQL above)

---

**Status**: 🟡 Partial - Buckets created, tables need manual creation
**Ready for**: Code integration and testing once tables are created
