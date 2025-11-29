# Dav1d: Google Cloud API Utilization Plan

This document outlines a comprehensive strategy for leveraging your installed Google Cloud APIs to power **Dav1d**. The plan prioritizes APIs based on their critical value to an AI agent system, balances performance with cost, and provides a clear implementation roadmap.

## Executive Summary

**Strategy:** "Serverless Intelligence"
We will build Dav1d as a cloud-native, serverless AI agent.
*   **Brain:** Vertex AI (Gemini 2.5 Flash for speed/cost, Pro for complex reasoning).
*   **Memory:** BigQuery (Vector Search for semantic recall) + Cloud Storage (Long-term archival).
*   **Body:** Cloud Run (Hosting the UI and API endpoints).
*   **Senses:** Custom Search, YouTube Data, and Maps APIs for real-world interaction.

**Estimated Monthly Cost:** Free to Low (<$10/mo) for personal usage, scaling linearly with heavy traffic.

---

## Tier 1: The "Brain" (Critical AI Capabilities)
*These APIs are the core of Dav1d's intelligence and existence.*

### 1. Vertex AI API (Gemini & Imagen)
*   **Purpose:** The core reasoning engine. Handles chat, code generation, image analysis, and image generation.
*   **Model Selection:**
    *   **Gemini 2.5 Flash:** **DEFAULT**. Use for 95% of interactions (chat, quick commands, summarization). It is extremely fast and cost-effective.
    *   **Gemini 2.5 Pro:** Use for complex reasoning, large context analysis (entire codebases), and creative writing.
    *   **Imagen 3:** Use for generating UI assets or visual content.
*   **Cost Breakdown:**
    *   **Flash:** ~$0.075 / 1M input tokens (Virtually free for personal use).
    *   **Pro:** ~$1.25 / 1M input tokens.
    *   **Imagen:** ~$0.04 per image.

### 2. Cloud Text-to-Speech & Speech-to-Text APIs
*   **Purpose:** Voice interaction for Dav1d.
*   **Usage:**
    *   **STT:** Transcribing your voice commands to Dav1d.
    *   **TTS:** Dav1d speaking responses back to you (can use "Journey" voices for premium feel).
*   **Cost:**
    *   **STT:** Free tier (60 min/mo), then ~$0.024/min.
    *   **TTS:** Free tier (4M chars/mo standard, 1M chars/mo WaveNet), then ~$16/1M chars.

---

## Tier 2: The "Body" & "Memory" (Infrastructure)
*These APIs host the application and store its experiences.*

### 3. Cloud Run Admin API
*   **Purpose:** Hosting the `dav1d-ui` (Next.js) and `dav1d-brain` (Python) in a serverless environment.
*   **Why:** Scales to zero when not in use (saving money) and handles traffic spikes automatically.
*   **Cost:**
    *   **Free Tier:** 2M requests/mo, 180k vCPU-seconds, 360k GiB-seconds.
    *   **Overage:** Very low (~$0.000024/vCPU-sec). Likely **FREE** for personal use.

### 4. BigQuery API
*   **Purpose:** **Semantic Memory**. We will store chat logs, embeddings, and knowledge in BigQuery.
*   **Feature:** Use **BigQuery Vector Search** to let Dav1d "remember" past conversations by meaning, not just keywords.
*   **Status:** (Done) Implemented in `tools/vector_store_bigquery.py`.
*   **Cost:**
    *   **Storage:** 10 GB/mo free.
    *   **Queries:** 1 TB/mo free.
    *   **Vector Search:** Small cost for indexing, but negligible for personal datasets.

### 5. Cloud Storage (GCS)
*   **Purpose:** Storing generated images, user uploads, and large backup files.
*   **Cost:**
    *   **Standard:** ~$0.02/GB/month.
    *   **Free Tier:** 5 GB-months free in US regions.

---

## Tier 3: The "Senses" (Tools & Capabilities)
*APIs that allow Dav1d to interact with the outside world.*

### 6. Google Search (Vertex AI Grounding)
*   **Purpose:** Web browsing capability. Allows Dav1d to look up real-time information, documentation, and news.
*   **Status:** (Done) Implemented via Vertex AI `GoogleSearch` tool.
*   **Cost:**
    *   **Grounding:** ~$35 per 1,000 queries (Enterprise).
    *   *Note:* `dav1d.py` uses the Vertex AI Grounding tool, which is more integrated than the Custom Search JSON API.

### 7. YouTube Data API v3
*   **Purpose:** Finding videos, managing playlists, or analyzing video content (via transcripts).
*   **Cost:** Free (quota based). 10,000 units/day is plenty for personal use.

### 8. Google Maps Platform (Places, Geocoding)
*   **Purpose:** Location awareness. "Find coffee shops near me", "How far is X".
*   **Cost:**
    *   $200/mo recurring credit.
    *   This covers ~28,000 map loads or ~40,000 geocoding requests. Effectively **FREE**.

---

## Tier 4: The "Nervous System" (DevOps & Monitoring)
*APIs that keep the system healthy and deploy changes.*

### 9. Cloud Build API
*   **Purpose:** CI/CD. Automatically build and deploy Dav1d to Cloud Run when you push code.
*   **Cost:** 120 build-minutes/day free.

### 10. Cloud Logging & Monitoring APIs
*   **Purpose:** Debugging. View logs from Dav1d's brain and UI. Set up alerts if costs spike.
*   **Cost:** Generous free tier (50GB logs/mo).

---

## Recommended Implementation Order

1.  **Core Intelligence (Done/In Progress):**
    *   Ensure `dav1d.py` uses **Vertex AI** (Gemini 2.5 Flash) as the default model.
    *   *Action:* Verify `dav1d.py` model config.

2.  **Memory Upgrade (Done):**
    *   Set up a **BigQuery** dataset for logs.
    *   Implement a "Memory Manager" class in Python to save/retrieve embeddings.
    *   *Status:* `tools/vector_store_bigquery.py` exists and is imported.

3.  **Web Capability (Done):**
    *   Integrate **Google Search** tool.
    *   *Status:* `Tool(google_search=GoogleSearch())` is implemented in `dav1d.py`.

4.  **Deployment Pipeline:**
    *   Create a `cloudbuild.yaml` to auto-deploy to **Cloud Run**.

5.  **Voice & Vision:**
    *   Add **STT/TTS** endpoints to the Python server.
    *   **Imagen 3:** (Done) Image generation is already operational.

## Cost Control Strategy
To ensure no surprise bills:
1.  **Set up Budgets & Alerts:** Set a budget of $10/mo in GCP Console. Alert at 50% and 90%.
2.  **Rate Limiting:** Hard-code limits in `dav1d.py` (e.g., max 50 searches/day).
3.  **Use "Flash" Models:** Default to Gemini 2.5 Flash. Only use Pro when explicitly requested (e.g., "Dav1d, think deeply about this...").

---

## Summary Table

| API Name | Priority | Use Case | Estimated Cost (Personal) |
| :--- | :--- | :--- | :--- |
| **Vertex AI** | 🚨 Critical | Brain (LLM) | < $2.00/mo |
| **Cloud Run** | 🚨 Critical | Hosting | FREE |
| **BigQuery** | ⚡ High | Memory | FREE |
| **Custom Search** | ⚡ High | Web Search | FREE (<100/day) |
| **Cloud Storage** | 🔹 Medium | File Store | < $0.10/mo |
| **YouTube Data** | 🔹 Medium | Video Tools | FREE |
| **Maps Platform** | 🔸 Low | Location | FREE (w/ credit) |
