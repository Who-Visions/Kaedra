# 🔗 Workspace Leverages Integration Guide

**Leverage Google Workspace Apps to Build Dav1d's External Memory & Workflow Automation**

---

## 🎯 What We Built

### 1. **Gmail to Notion** (`gmail_to_notion.py`)
**Auto-save emails to Notion with AI categorization**

**Features:**
- ✅ Fetches emails via Gmail API (OAuth authenticated)
- ✅ Gemini AI categorization (work/personal/urgent)
- ✅ Auto-extracts priority, action items, tags
- ✅ Saves to Notion database as structured memory
- ✅ Searchable external memory for Dav1d

**Use Case:** Build a permanent, AI-organized email knowledge base in Notion that Dav1d can query.

---

### 2. **Tasks & Notion Sync** (`tasks_notion_sync.py`)
**Bidirectional sync between Google Tasks and Notion**

**Features:**
- ✅ Sync Google Tasks → Notion (with AI enrichment)
- ✅ Sync Notion → Google Tasks (for mobile access)
- ✅ Gemini auto-enrichment (priority, time estimates, subtasks, tags)
- ✅ Multi-list support
- ✅ Automated task breakdown

**Use Case:** Centralize all tasks in Notion, enriched with AI insights, while keeping mobile access via Google Tasks.

---

### 3. **Workflow Automation** (`workflow_automation.py`)
**Trigger Dav1d agents based on Google Workspace events**

**Features:**
- ✅ Webhook endpoints for Gmail, Drive, Calendar
- ✅ Pattern-matching workflow engine
- ✅ Gemini-powered intelligent routing
- ✅ Pre-defined automation rules
- ✅ Notion workflow logging
- ✅ Manual trigger API

**Use Case:** Auto-analyze urgent emails, summarize shared docs, prepare meeting briefings — all without manual intervention.

---

## 🚀 Quick Start

### Prerequisites

1. **Install dependencies:**
```bash
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"
pip install -r requirements.txt
```

2. **Set up OAuth credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create OAuth 2.0 Client ID (Desktop app)
   - Download as `credentials_gmail.json` and `credentials_tasks.json`
   - Place in `dav1d brain/` folder

3. **Enable APIs:**
```bash
gcloud services enable gmail.googleapis.com --project=gen-lang-client-0285887798
gcloud services enable tasks.googleapis.com --project=gen-lang-client-0285887798
gcloud services enable drive.googleapis.com --project=gen-lang-client-0285887798
```

4. **Create Notion databases:**
   - Create 3 databases in Notion:
     - **Gmail Inbox** (for emails)
     - **Tasks** (for synced tasks)
     - **Workflows** (for automation logs)
   - Share each with your Dav1d Notion integration
   - Get database IDs from URLs

5. **Update `.env`:**
```bash
# Existing
NOTION_TOKEN=secret_...
PROJECT_ID=gen-lang-client-0285887798
LOCATION=us-east4

# New
NOTION_GMAIL_DB_ID=your_gmail_database_id
NOTION_TASKS_DB_ID=your_tasks_database_id
NOTION_WORKFLOWS_DB_ID=your_workflows_database_id
```

---

## 📧 Gmail to Notion

### Setup Notion Database

**Required properties:**
- `Subject` (Title)
- `From` (Text)
- `Category` (Select: Work, Personal, Newsletter, Spam, Urgent)
- `Priority` (Select: Low, Medium, High, Urgent)
- `Action Required` (Checkbox)
- `Date` (Date)
- `Tags` (Multi-select)

### Run

**Sync unread emails:**
```bash
python gmail_to_notion.py
```

**Custom query:**
```bash
python gmail_to_notion.py --query "from:important@example.com" --max 20
```

**What happens:**
1. Authenticates with Gmail (opens browser first time)
2. Fetches emails matching query
3. Analyzes each with Gemini (category, priority, key points)
4. Creates Notion page with AI insights
5. Email now permanently stored in searchable Notion database

---

## ✅ Tasks & Notion Sync

### Setup Notion Database

**Required properties:**
- `Name` (Title)
- `Status` (Select: To Do, In Progress, Done)
- `Priority` (Select: Low, Medium, High, Urgent)
- `Due Date` (Date)
- `Tags` (Multi-select)

### Run

**Sync Google Tasks → Notion:**
```bash
python tasks_notion_sync.py --direction google-to-notion
```

**Sync Notion → Google Tasks:**
```bash
python tasks_notion_sync.py --direction notion-to-google
```

**Bidirectional sync:**
```bash
python tasks_notion_sync.py --direction both
```

**What happens:**
1. Fetches tasks from Google Tasks
2. Gemini analyzes each task:
   - Suggests priority
   - Estimates time
   - Generates tags
   - Breaks into subtasks (if complex)
3. Creates enriched Notion pages
4. Tasks now have AI-powered metadata

---

## ⚡ Workflow Automation

### Pre-defined Workflows

**1. Auto-analyze urgent emails:**
- **Trigger:** New email with "urgent", "asap", or "important"
- **Actions:**
  - Analyze email with Gemini
  - Trigger full Dav1d multi-agent analysis
  - Log to Notion

**2. Summarize shared documents:**
- **Trigger:** File shared in Google Drive (PDF or DOCX)
- **Actions:**
  - Fetch file content
  - Generate AI summary
  - Save to Notion

**3. Prepare for meetings:**
- **Trigger:** Calendar event starting in 30 minutes
- **Actions:**
  - Generate meeting briefing
  - Create agenda
  - Suggest preparation checklist

### Run Server

```bash
python workflow_automation.py
```

Server starts on `http://localhost:3001`

### API Endpoints

**Webhook endpoints:**
- `POST /webhook/gmail` - Receive Gmail events
- `POST /webhook/drive` - Receive Drive events
- `POST /webhook/calendar` - Receive Calendar events

**Manual trigger:**
```bash
curl -X POST http://localhost:3001/trigger-manual \
  -H "Content-Type: application/json" \
  -d '{
    "action": "analyze_email",
    "event_data": {
      "subject": "Urgent: Server Down",
      "from": "ops@example.com",
      "body": "Production server is down..."
    }
  }'
```

**List workflows:**
```bash
curl http://localhost:3001/workflows
```

**Health check:**
```bash
curl http://localhost:3001/health
```

---

## 🔧 Advanced: Connecting Webhooks

### Gmail Webhooks

Gmail doesn't have native webhooks, but you can:

**Option 1: Use Cloud Scheduler + Cloud Run**
Deploy `gmail_to_notion.py` to Cloud Run, trigger with Cloud Scheduler every 5 minutes.

**Option 2: Use Gmail Push Notifications**
Set up Gmail API push notifications to Pub/Sub → Cloud Function → Your webhook.

### Drive Webhooks

```bash
# Set up Drive API push notifications
gcloud pubsub topics create drive-changes
gcloud pubsub subscriptions create drive-changes-sub --topic=drive-changes

# Point to your webhook endpoint
```

### Calendar Webhooks

Similar to Drive, use Calendar API push notifications.

---

## 🎯 Integration with Dav1d

### Query External Memory

Once data is in Notion, Dav1d can query it using existing `notion_integration.py`:

```python
# In dav1d.py, add command:
if user_input.startswith("/search-memory"):
    query = user_input.replace("/search-memory", "").strip()
    # Search Notion databases for query
    results = search_notion_memory(query)
    print(f"Found {len(results)} results in external memory")
```

### Trigger Workflows from Dav1d

```python
# In dav1d.py, add command:
if user_input.startswith("/trigger-workflow"):
    workflow_name = user_input.replace("/trigger-workflow", "").strip()
    # Call workflow automation API
    trigger_workflow(workflow_name)
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              GOOGLE WORKSPACE LEVERAGES                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Gmail API ──────┐                                      │
│  Tasks API ──────┼───→ OAuth Authentication             │
│  Drive API ──────┤                                      │
│  Calendar API ───┘                                      │
│                                                         │
└──────────────┬──────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────┐
│                  DAV1D INTEGRATIONS                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  gmail_to_notion.py         (Port 3000)                 │
│  tasks_notion_sync.py       (CLI)                       │
│  workflow_automation.py     (Port 3001)                 │
│                                                         │
└──────────────┬──────────────────────────────────────────┘
               │
               │ ┌────────────────────┐
               ├→│  Gemini 2.5 Flash  │ (AI Analysis)
               │ └────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────┐
│                  NOTION (EXTERNAL MEMORY)               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📧 Gmail Inbox DB      (Categorized emails)            │
│  ✅ Tasks DB            (Enriched tasks)                │
│  ⚡ Workflows DB        (Automation logs)               │
│                                                         │
└──────────────┬──────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────┐
│                   DAV1D MAIN AGENT                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  - Queries external memory via Notion API               │
│  - Triggers workflows programmatically                  │
│  - Multi-agent analysis with full context               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚨 Security Checklist

- ✅ **OAuth tokens** stored in `token_*.json` (gitignored)
- ✅ **Credentials** in `credentials_*.json` (gitignored)
- ✅ **Notion token** in `.env` (gitignored)
- ✅ **Service account keys** in `.json` files (gitignored)
- ⚠️  Never commit tokens/credentials to Git
- ⚠️  Use least-privilege OAuth scopes
- ⚠️  Rotate Notion integration tokens periodically

---

## 📁 Files Created

```
c:\Users\super\Watchtower\Dav1d\dav1d brain\
├── gmail_to_notion.py              ← Gmail → Notion sync
├── tasks_notion_sync.py            ← Tasks ↔ Notion sync
├── workflow_automation.py          ← Workflow engine
├── WORKSPACE_LEVERAGES_GUIDE.md    ← This file
├── requirements.txt                ← Updated with OAuth deps
└── .env                            ← Add new database IDs here
```

**To be created by you:**
```
├── credentials_gmail.json          ← Download from Google Cloud Console
├── credentials_tasks.json          ← Download from Google Cloud Console
├── token_gmail.json                ← Auto-generated on first run
└── token_tasks.json                ← Auto-generated on first run
```

---

## ✨ Next Steps

### Immediate (Do Now)

1. ✅ **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. ✅ **Download OAuth credentials** from Google Cloud Console

3. ✅ **Create Notion databases** and get IDs

4. ✅ **Update `.env`** with database IDs

5. ✅ **Test Gmail sync:**
   ```bash
   python gmail_to_notion.py --max 5
   ```

### Short-term (This Week)

1. **Set up automated Gmail sync:**
   - Deploy to Cloud Run
   - Use Cloud Scheduler to run every 15 minutes

2. **Connect workflow webhooks:**
   - Set up Gmail push notifications → Pub/Sub → workflow_automation.py

3. **Integrate with Dav1d main loop:**
   - Add `/search-memory` command
   - Add `/trigger-workflow` command

### Long-term (Future Enhancements)

1. **Add more Workspace apps:**
   - Google Forms → Auto-analyze survey responses
   - Google Sheets → Data extraction for reports
   - Google Slides → Auto-generate from Notion content

2. **Two-way sync:**
   - Notion updates → Gmail drafts
   - Notion tasks → Calendar events

3. **Advanced workflows:**
   - Multi-step approval flows
   - Conditional branching based on Gemini analysis
   - Integration with external tools (Slack, Discord, etc.)

---

## 🎉 Summary

**You now have:**
- ✅ **Gmail → Notion**: AI-categorized email memory
- ✅ **Tasks ↔ Notion**: Bidirectional task sync with AI enrichment
- ✅ **Workflow Automation**: Event-driven Dav1d triggers
- ✅ **External Memory**: Searchable knowledge base in Notion
- ✅ **API Integrations**: OAuth-authenticated Google APIs
- ✅ **Gemini Intelligence**: Auto-categorization and enrichment

**All connected to Dav1d's existing Gemini stack!** 🚀

---

**Ready to build Dav1d's memory?** Start with Gmail sync and watch your external knowledge base grow! 📧🧠
