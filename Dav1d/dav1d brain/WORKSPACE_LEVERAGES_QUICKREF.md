# 🎯 WORKSPACE LEVERAGES - QUICK REFERENCE

**External Memory & Workflow Automation for Dav1d**

---

## 📦 What's Installed

✅ **7 new files created**
✅ **Dependencies updated**
✅ **3 integration types: Notion sync, Tasks sync, Workflow automation**

---

## 🚀 3-Step Quickstart

### 1. Setup (One-time)
```bash
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"
python setup_workspace_leverages.py
```

### 2. Get Credentials
- **OAuth credentials:** [Google Cloud Console](https://console.cloud.google.com/apis/credentials?project=gen-lang-client-0285887798)
- **Notion token:** [Notion Integrations](https://www.notion.so/my-integrations)

### 3. Test
```bash
# Test Gmail sync
python gmail_to_notion.py --max 5

# Test Tasks sync
python tasks_notion_sync.py --direction google-to-notion

# Test Workflows
python workflow_automation.py
```

---

## 📁 Files Reference

| File | Purpose | Port |
|------|---------|------|
| `gmail_to_notion.py` | Gmail → Notion sync with AI categorization | - |
| `tasks_notion_sync.py` | Google Tasks ↔ Notion bidirectional sync | - |
| `workflow_automation.py` | Event-driven automation engine | 3001 |
| `notion_integration.py` | Notion webhook server (existing) | 3000 |
| `dav1d_integrations.py` | Helper functions for dav1d.py | - |
| `setup_workspace_leverages.py` | Setup assistant | - |
| `WORKSPACE_LEVERAGES_GUIDE.md` | Complete documentation | - |

---

## 🔑 New Commands (After Integration)

Add to `dav1d.py`:

```bash
/search-memory <query>     # Search emails & tasks in Notion
/trigger-workflow <name>   # Manually trigger automation
/sync-tasks                # Sync Google Tasks ↔ Notion
/sync-gmail                # Sync Gmail → Notion
```

---

## 🗄️ Notion Databases Needed

Create these 3 databases:

### 1. Gmail Inbox
- Subject (Title)
- From (Text)
- Category (Select)
- Priority (Select)
- Action Required (Checkbox)
- Date (Date)
- Tags (Multi-select)

### 2. Tasks
- Name (Title)
- Status (Select)
- Priority (Select)
- Due Date (Date)
- Tags (Multi-select)

### 3. Workflows
- Workflow (Title)
- Timestamp (Date)
- Status (Select)

**Get database IDs from URLs, add to `.env`**

---

## ⚡ Workflows Included

**Auto-analyze urgent emails:**
- Trigger: Email with "urgent", "asap", "important"
- Action: Gemini analysis + Dav1d multi-agent

**Summarize shared documents:**
- Trigger: PDF/DOCX shared in Drive
- Action: AI summary → Notion

**Prepare for meetings:**
- Trigger: Calendar event in 30 min
- Action: Generate briefing + agenda

---

## 🔧 .env Variables to Add

```bash
# Notion
NOTION_TOKEN=secret_your_token
NOTION_GMAIL_DB_ID=your_gmail_db_id
NOTION_TASKS_DB_ID=your_tasks_db_id
NOTION_WORKFLOWS_DB_ID=your_workflows_db_id
```

---

## 📚 Documentation

- **Setup Guide:** `WORKSPACE_LEVERAGES_GUIDE.md` (detailed)
- **Complete Summary:** `WORKSPACE_LEVERAGES_COMPLETE.md` (overview)
- **This File:** Quick reference

---

## ✅ Checklist

- [ ] Run `setup_workspace_leverages.py`
- [ ] Download OAuth credentials → `credentials_gmail.json`, `credentials_tasks.json`
- [ ] Create Notion token → Add to `.env`
- [ ] Create 3 Notion databases → Add IDs to `.env`
- [ ] Test Gmail sync: `python gmail_to_notion.py --max 5`
- [ ] Test Tasks sync: `python tasks_notion_sync.py`
- [ ] Test Workflows: `python workflow_automation.py`
- [ ] Integrate with `dav1d.py` (use `dav1d_integrations.py`)

---

## 🎉 What This Gives You

**Before:** Dav1d has no memory beyond the current session

**After:**
- ✅ Permanent email memory (searchable in Notion)
- ✅ AI-enriched task management
- ✅ Auto-trigger analysis on important events
- ✅ Centralized knowledge base
- ✅ Workflow automation

**External Memory = Context for Better Decisions** 🧠

---

**Need help?** See `WORKSPACE_LEVERAGES_GUIDE.md` for detailed setup!
