# 🔗 Notion Integration for Dav1d

**AI-Powered Notion Analysis with Gemini**

---

## ✨ What It Does

Dav1d's Notion integration automatically analyzes your Notion pages using Gemini AI and writes insights back to your workspace.

**When you create or update a Notion page, Dav1d:**
1. 📖 Reads the page content
2. 🧠 Analyzes it with Gemini 2.5
3. ✍️ Writes back:
   - Summary
   - Key points
   - Action items
   - Tags
   - Priority level

---

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Add to your `.env` file:

```bash
# Notion Configuration
NOTION_TOKEN=secret_...your_integration_token...
NOTION_DATABASE_ID=...your_database_id...  # Optional: specific database to watch

# GCP Configuration (already set)
PROJECT_ID=gen-lang-client-0285887798
LOCATION=us-east4
```

### 3. Create Notion Integration
1. Go to: https://www.notion.so/my-integrations
2. Click **"+ New integration"**
3. Name: **"Dav1d AI"**
4. Associated workspace: Select your workspace
5. Capabilities: **Read content**, **Update content**, **Insert content**
6. Click **"Submit"**
7. Copy the **Internal Integration Token** → Add to `.env` as `NOTION_TOKEN`

### 4. Share Database with Integration
1. Open your Notion database
2. Click **"•••"** (top right)
3. Click **"Add connections"**
4. Select **"Dav1d AI"**
5. Click **"Confirm"**

### 5. Run the Integration Server
```bash
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"
python notion_integration.py
```

**Server starts on:** http://localhost:3000

---

## 🔔 Setting Up Webhooks

### Option 1: Using ngrok (Development)
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 3000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add webhook in Notion settings (coming soon to Notion API)
```

### Option 2: Deploy to Cloud Run (Production)
```bash
#Build and deploy
gcloud run deploy dav1d-notion \
  --source . \
  --platform managed \
  --region us-east4 \
  --allow-unauthenticated \
  --set-env-vars="NOTION_TOKEN=$NOTION_TOKEN,PROJECT_ID=gen-lang-client-0285887798"

# Get the URL
gcloud run services describe dav1d-notion --region us-east4 --format='value(status.url)'
```

### Option 3: Manual Trigger (Testing)
```bash
# Analyze a specific page
curl -X POST http://localhost:3000/analyze-page/YOUR_PAGE_ID
```

---

## 📊 API Endpoints

### `POST /notion-webhook`
**Receives Notion webhook events**

Request body (from Notion):
```json
{
  "type": "page.created",
  "entity": {
    "type": "page",
    "id": "page-id-here"
  }
}
```

Response:
```json
{
  "status": "accepted"
}
```

---

### `POST /analyze-page/{page_id}`
**Manually trigger analysis for a page**

Example:
```bash
curl -X POST http://localhost:3000/analyze-page/abc123def456
```

Response:
```json
{
  "status": "accepted",
  "page_id": "abc123def456",
  "message": "Analysis queued"
}
```

---

### `GET /health`
**Check integration health**

Response:
```json
{
  "status": "healthy",
  "service": "Dav1d Notion Integration",
  "notion_connected": true,
  "gemini_configured": true
}
```

---

## 🧠 How AI Analysis Works

### Input
```markdown
# Weekly Planning

## Goals
- Complete Dav1d Notion integration
- Deploy to Cloud Run
- Test with real workspace

## Notes
Need to set up webhook endpoint. Consider using ngrok for local testing first.

## Action Items
- [ ] Create Notion integration
- [ ] Add environment variables
- [ ] Test locally
```

### Output (Written to Notion)
```
🤖 Dav1d AI Analysis

Summary: Planning document for Dav1d Notion integration deployment, 
focusing on setup steps and local testing strategy.

Key Points:
• Complete integration with Notion API
• Deploy to Cloud Run for production
• Use ngrok for local webhook testing

Action Items:
✓ Create Notion integration in settings
✓ Configure environment variables in .env
✓ Run local test with sample page

Priority: MEDIUM
```

---

## 🎯 Use Cases

### 1. Meeting Notes Analysis
**What it does:** Extracts action items and key decisions from meeting notes

**Example:**
- You write meeting notes in Notion
- Dav1d analyzes the content
- Creates a summary with action items
- Highlights priorities

### 2. Project Documentation
**What it does:** Tags and categorizes project docs

**Example:**
- You create a project spec
- Dav1d identifies key components
- Suggests related tasks
- Tags with relevant categories

### 3. Research Notes
**What it does:** Synthesizes key insights from research

**Example:**
- You paste research findings
- Dav1d extracts main points
- Identifies action items
- Assigns priority

---

## 🔧 Advanced Configuration

### Custom Analysis Prompts

Edit `notion_integration.py` to customize the analysis prompt:

```python
async def analyze_page_with_gemini(title: str, content: str, custom_instructions: str = "") -> dict:
    prompt = f"""Analyze this Notion page...

{custom_instructions}

Page Title: {title}
Content: {content}
...
"""
```

### Database-Specific Handlers

Add custom logic for different databases:

```python
async def process_notion_page(page_id: str, database_id: str, event_type: str):
    if database_id == "meeting-notes-db-id":
        # Custom meeting notes analysis
        analysis = await analyze_meeting_notes(...)
    elif database_id == "projects-db-id":
        # Custom project analysis
        analysis = await analyze_project(...)
    else:
        # Default analysis
        analysis = await analyze_page_with_gemini(...)
```

### Multi-Database Support

Watch multiple databases:

```python
WATCHED_DATABASES = {
    "meeting-notes": os.getenv("NOTION_MEETINGS_DB"),
    "projects": os.getenv("NOTION_PROJECTS_DB"),
    "tasks": os.getenv("NOTION_TASKS_DB"),
}
```

---

## 🔒 Security Best Practices

### Environment Variables
- ✅ Store `NOTION_TOKEN` in `.env` (gitignored)
- ✅ Never commit secrets to GitHub
- ✅ Use GCP Secret Manager for production

### Webhook Security
- ✅ Verify webhook signatures (when Notion adds support)
- ✅ Use HTTPS only in production
- ✅ Rate limit requests

### Notion Permissions
- ✅ Grant minimum required permissions
- ✅ Scope integration to specific databases
- ✅ Audit integration access regularly

---

## 📈 Monitoring & Logs

### Check Server Logs
```bash
# When running locally
tail -f notion_integration.log

# Cloud Run logs
gcloud run services logs read dav1d-notion --region us-east4 --limit=50
```

### Common Log Messages
```
🔔 Processing page: abc123... (event: page.created)
📄 Page: 'Meeting Notes' | 1234 chars | 15 blocks
🧠 Analyzing with Gemini...
✅ Analysis complete: high priority
✅ Analysis written back to page abc123
✅ Page processing complete: abc123
```

---

## 🐛 Troubleshooting

### "NOTION_TOKEN not set"
**Fix:** Add `NOTION_TOKEN=secret_...` to `.env`

### "Failed to write analysis: object_type is not supported"
**Fix:** Your Notion database may not support the callout block type. Check page permissions.

### "Gemini analysis failed"
**Fix:** 
1. Check GCP authentication
2. Verify `PROJECT_ID` is correct
3. Ensure Gemini API is enabled

### "Permission denied" when writing to page
**Fix:**
1. Go to Notion page
2. Click "•••" → "Add connections"
3. Select "Dav1d AI"

---

## 🚀 Next Steps

### Phase 1: Basic Integration ✅
- [x] Create Notion webhook endpoint
- [x] Analyze pages with Gemini
- [x] Write insights back to Notion

### Phase 2: Enhanced Features 🔄
- [ ] Support for multiple databases
- [ ] Custom analysis per database type
- [ ] Task creation from action items
- [ ] Slack notifications for high-priority items

### Phase 3: Advanced 🔮
- [ ] Notion MCP integration (when available)
- [ ] Multi-hop reasoning across pages
- [ ] Automatic relation detection
- [ ] Schedule automatic re-analysis

---

## 📚 Resources

**Notion API:**
- Docs: https://developers.notion.com
- Integration guide: https://developers.notion.com/docs/create-a-notion-integration

**Gemini API:**
- Docs: https://ai.google.dev/docs
- Vertex AI: https://cloud.google.com/vertex-ai/docs

**FastAPI:**
- Docs: https://fastapi.tiangolo.com
- Webhooks guide: https://fastapi.tiangolo.com/advanced/events/

---

## ✨ Summary

**Dav1d's Notion integration brings AI analysis to your workspace:**

1. ✅ **Zero manual work** - Automatic analysis on page creation/update
2. ✅ **Instant insights** - Gemini analyzes in seconds
3. ✅ **Written back** - Insights appear right in Notion
4. ✅ **Cloud-native** - Runs on GCP, scales automatically
5. ✅ **Fully integrated** - Uses your existing Dav1d setup

**Start using it:** Just run `python notion_integration.py` and create a Notion page! 🎉

---

**Questions?** Check the HQ_WhoArt implementation for advanced examples or open an issue on GitHub.
