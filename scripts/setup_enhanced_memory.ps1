# Enhanced Kaedra Memory Setup - PowerShell
# Async memory with short-term/long-term separation + 1k token chunking

$PROJECT_ID = "gen-lang-client-0939852539"
$REGION = "us-central1"
$DATASET_ID = "kaedra_memory"

Write-Host "=========================================="
Write-Host " Kaedra Enhanced Memory Setup"
Write-Host "=========================================="
Write-Host ""

# 1. Verify project
Write-Host "[1/6] Verifying project..." -ForegroundColor Cyan
gcloud config get-value project

# 2. Enable APIs
Write-Host "[2/6] Enabling APIs..." -ForegroundColor Cyan
gcloud services enable bigquery.googleapis.com storage.googleapis.com

# 3. Create BigQuery dataset
Write-Host "[3/6] Creating BigQuery dataset..." -ForegroundColor Cyan
bq --location=$REGION mk --dataset --description="Kaedra intelligent memory system" ${PROJECT_ID}:${DATASET_ID}
if ($LASTEXITCODE -ne 0) { Write-Host "Dataset may already exist" -ForegroundColor Yellow }

# 4. Create SHORT-TERM memory table
Write-Host "[4/6] Creating SHORT-TERM memory table..." -ForegroundColor Cyan
bq mk --table ${PROJECT_ID}:${DATASET_ID}.memory_short_term "chunk_id:STRING,session_id:STRING,content:STRING,tokens:INTEGER,embedding:STRING,timestamp:TIMESTAMP,ttl:TIMESTAMP,metadata:STRING"
if ($LASTEXITCODE -ne 0) { Write-Host "Short-term table may already exist" -ForegroundColor Yellow }

# Set 7-day expiration
bq update --time_partitioning_field timestamp --time_partitioning_expiration 604800 ${PROJECT_ID}:${DATASET_ID}.memory_short_term
if ($LASTEXITCODE -ne 0) { Write-Host "Partitioning may already be configured" -ForegroundColor Yellow }

# 5. Create LONG-TERM memory table
Write-Host "[5/6] Creating LONG-TERM memory table..." -ForegroundColor Cyan
bq mk --table ${PROJECT_ID}:${DATASET_ID}.memory_long_term "chunk_id:STRING,topic:STRING,content:STRING,tokens:INTEGER,chunk_index:INTEGER,total_chunks:INTEGER,importance:STRING,tags:STRING,embedding:STRING,timestamp:TIMESTAMP,metadata:STRING"
if ($LASTEXITCODE -ne 0) { Write-Host "Long-term table may already exist" -ForegroundColor Yellow }

# Create KNOWLEDGE table
Write-Host "Creating KNOWLEDGE table..." -ForegroundColor Cyan
bq mk --table ${PROJECT_ID}:${DATASET_ID}.knowledge "chunk_id:STRING,doc_id:STRING,title:STRING,content:STRING,tokens:INTEGER,chunk_index:INTEGER,source:STRING,embedding:STRING,timestamp:TIMESTAMP,metadata:STRING"
if ($LASTEXITCODE -ne 0) { Write-Host "Knowledge table may already exist" -ForegroundColor Yellow }

# 6. Create Cloud Storage buckets
Write-Host "[6/6] Creating storage buckets..." -ForegroundColor Cyan

gcloud storage buckets create gs://${PROJECT_ID}-memory-async --location=$REGION --uniform-bucket-level-access
if ($LASTEXITCODE -ne 0) { Write-Host "Async memory bucket may already exist" -ForegroundColor Yellow }

gcloud storage buckets create gs://${PROJECT_ID}-knowledge --location=$REGION --uniform-bucket-level-access
if ($LASTEXITCODE -ne 0) { Write-Host "Knowledge bucket may already exist" -ForegroundColor Yellow }

gcloud storage buckets create gs://${PROJECT_ID}-images --location=$REGION --uniform-bucket-level-access
if ($LASTEXITCODE -ne 0) { Write-Host "Images bucket may already exist" -ForegroundColor Yellow }

gcloud storage buckets create gs://${PROJECT_ID}-videos --location=$REGION --uniform-bucket-level-access
if ($LASTEXITCODE -ne 0) { Write-Host "Videos bucket may already exist" -ForegroundColor Yellow }

Write-Host ""
Write-Host "=========================================="
Write-Host " SUCCESS! Enhanced Memory Setup Complete" -ForegroundColor Green
Write-Host "=========================================="
Write-Host ""
Write-Host "BigQuery Tables:"
Write-Host "  - memory_short_term (async, 7-day TTL)"
Write-Host "  - memory_long_term (persistent, 1k chunks)"
Write-Host "  - knowledge (RAG, 1k chunks)"
Write-Host ""
Write-Host "Cloud Storage:"
Write-Host "  - gs://${PROJECT_ID}-memory-async"
Write-Host "  - gs://${PROJECT_ID}-knowledge"
Write-Host "  - gs://${PROJECT_ID}-images"
Write-Host "  - gs://${PROJECT_ID}-videos"
Write-Host ""
Write-Host "Location: $REGION" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host ""

# Verify
Write-Host "Verifying BigQuery tables..." -ForegroundColor Cyan
bq ls ${PROJECT_ID}:${DATASET_ID}

Write-Host ""
Write-Host "Verifying Cloud Storage buckets..." -ForegroundColor Cyan
gcloud storage buckets list --filter="name~${PROJECT_ID}-"

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
