# Google Cloud Gemini Quotas & Limits Reference

## System Limits (Fixed)
- **Requests per second**: 2 (per user in a project)

## Daily Quotas
- **Gemini Code Assist / BigQuery Code**: 6000 requests/day
- **Chat / Visualization / Data Insights**: 960 requests/day

## Agent Mode & CLI Quotas
- **Requests per minute**: 120 (Standard & Enterprise)
- **Requests per day**: 
  - Standard: 1500
  - Enterprise: 2000

## Image Generation (Observed)
- **Error**: `aiplatform.googleapis.com/generate_content_requests_per_minute_per_project_per_base_model`
- **Limit**: Typically low for new projects (e.g., 5-10 RPM for Imagen 3.0)
- **Handling Strategy**: 
  - Detect `429 RESOURCE_EXHAUSTED`
  - Wait 65s (clears the 1-minute window)
  - Retry
