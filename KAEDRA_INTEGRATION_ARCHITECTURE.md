# Kaedra Integration Architecture

## Overview

Kaedra is a multi-service AI agent that orchestrates:
- **Notion** — Content management, lore database, ingestion queue
- **Google Workspace** — Gmail, Calendar, Drive, Docs, Sheets, Tasks
- **LIFX** — Ambient lighting synced to narrative tension
- **Story Engine** — Interactive writing assistant with voice support

---

## Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                     Kaedra Engine.py                        │
│                    (Story Engine CLI)                       │
├─────────────────────────────────────────────────────────────┤
│  Commands:                                                  │
│    :sync      → Notion bidirectional sync                  │
│    :automate  → Universe automations (timeline/tension)    │
│    :email     → Gmail read/send                            │
│    :calendar  → Calendar check/create events               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    Notion     │   │    Google     │   │    LIFX       │
│   Bridge      │   │   Workspace   │   │   Lights      │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ • Pull Queue  │   │ • Gmail       │   │ • Mood Sync   │
│ • Push Bible  │   │ • Calendar    │   │ • Tension     │
│ • Upload File │   │ • Drive/Docs  │   │ • Night Mode  │
│ • Download    │   │ • Sheets      │   └───────────────┘
└───────────────┘   │ • Tasks       │
                    └───────────────┘
```

---

## Notion Integration

### Endpoints (Cloud Run)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/notion` | POST | Receive Notion change events |
| `/sync` | POST | Trigger full sync `{"world_id": "..."}` |
| `/sync/{world_id}` | GET | Check sync status |

### Data Flow
```
Notion Ingestion Queue (Status: Approved)
    ↓ pull_ingestion_queue()
Local ingestion.json
    ↓ processed by Engine
World Bible entry created
    ↓ push_to_bible()
Notion World Bible page
    ↓ _mark_as_imported()
Notion Status → "Imported"
```

### Key Files
- `tools/sync_notion.py` — NotionBridge class
- `kaedra/config/notion.toml` — Token and database IDs
- `lore/worlds/{world_id}/ingestion.json` — Pulled items
- `lore/worlds/{world_id}/world_bible.json` — Canon entries

---

## Google Workspace Integration

### Available APIs (8/8 Working)
| API | Scope | Use Case |
|-----|-------|----------|
| **Gmail** | `gmail.modify` | Read/send emails, auto-responses |
| **Calendar** | `calendar` | Schedule events, writing sessions |
| **Drive** | `drive` | File storage, backups |
| **Docs** | `documents` | Generate/read documents |
| **Sheets** | `spreadsheets` | Data tracking, logs |
| **Slides** | `presentations.readonly` | Read presentations |
| **Tasks** | `tasks` | Task management |
| **Contacts** | `contacts.readonly` | Contact lookup |

### Key Files
- `tools/google_auth.py` — OAuth flow
- `tools/test_google_apis.py` — API test suite
- `kaedra/config/google_oauth_client.json` — OAuth credentials
- `kaedra/config/google_token.json` — Refresh token

---

## Automation Possibilities

### Notion → Google
| Trigger | Action |
|---------|--------|
| New "Approved" item in Ingestion Queue | Create Google Task |
| World Bible entry created | Backup to Google Drive |
| Session scheduled in Notion | Create Calendar event |

### Google → Notion
| Trigger | Action |
|---------|--------|
| Gmail with "VeilVerse" keyword | Add to Ingestion Queue |
| Calendar event starts | Update Notion session log |
| Task completed | Update Notion status |

### Engine → Both
| Command | Action |
|---------|--------|
| `:sync` | Full Notion bidirectional sync |
| `:email inbox` | Show recent emails |
| `:calendar today` | Show today's events |
| `:automate` | Run universe automations |

---

## Cloud Deployment

### Cloud Run Service
- **URL**: `https://kaedra-69017097813.us-central1.run.app`
- **Trigger**: Git push to `main` branch
- **Build**: Cloud Build with `cloudbuild.yaml`

### Required Secrets
- `NOTION_TOKEN` — Notion integration token
- `GOOGLE_TOKEN` — OAuth refresh token (for Gmail/Calendar)

---

---

## Google API Automation Triggers (Deep Dive)

### Push vs Polling Patterns

| Feature | Push (Webhooks/PubSub) | Polling (Scheduled Jobs) |
|---------|------------------------|--------------------------|
| **Latency** | Near real-time (< 2s) | Delay based on interval (1-60 min) |
| **Cost/Quota** | High efficiency, low API hits | Constant API hits even if no changes |
| **Setup** | Complex (Needs Public URL/Cloud Run) | Simple (Self-contained script) |
| **Best Use** | Incoming Emails, Calendar Invites | Sheets tracking, Task status checks |

---

### Push-Capable APIs (Real-time)

#### Gmail
*   **Mechanism**: Pub/Sub topic watch.
*   **Permissions**: `https://www.googleapis.com/auth/gmail.modify`
*   **Setup**:
    ```python
    service.users().watch(userId='me', body={'topicName': 'projects/kaedra/topics/gmail'}).execute()
    ```
*   **Trigger**: Incoming mail with specific labels or keywords → Calls `/webhook/gmail` → Add to Notion Ingestion.

#### Google Calendar
*   **Mechanism**: Webhook channel registration.
*   **Permissions**: `https://www.googleapis.com/auth/calendar`
*   **Setup**: 
    ```python
    body = {'id': 'channel-id', 'type': 'web_hook', 'address': 'https://api.kaedra.run/webhook/calendar'}
    service.events().watch(calendarId='primary', body=body).execute()
    ```
*   **Trigger**: New event or invite → Kaedra checks availability or updates Session Log.

#### Google Drive
*   **Mechanism**: Changes API + Watch.
*   **Trigger**: New lore document uploaded → Kaedra auto-parses and pushes to Ingestion Queue.

---

### Polling-Only APIs

#### Google Tasks
*   **Strategy**: Poll every 5 mins using `updatedMin` to only fetch new changes.
*   **Trigger**: Task marked complete → Kaedra updates Notion world status.

#### Google Sheets
*   **Strategy**: Value diffing. Fetch column/row range, compare with local state.
*   **Trigger**: New row added (e.g., character stat change) → Update World Bible.

#### Google Docs
*   **Strategy**: Watch via Drive API `modifiedTime`, then fetch doc content.
*   **Trigger**: Lore doc updated → Reparse and check for coherence.

---

### Implementation Templates

#### Cloud Run Webhook Handler (`kaedra/api/main.py`)
```python
@app.post("/webhook/gmail")
async def gmail_webhook(payload: dict):
    # Process Gmail Pub/Sub notification
    # 1. Fetch history.list()
    # 2. Extract message
    # 3. Add to Notion Ingestion Queue
    return {"status": "processed"}
```

#### Automation Roadmap

| API | Support | Recommended Pattern | Kaedra Use Case |
|-----|---------|---------------------|-----------------|
| **Gmail** | Push | Pub/Sub Watch | Email → Ingestion Queue |
| **Calendar** | Push | Webhook Channel | Sync Sessions with Calendar |
| **Drive** | Push | Changes Watch | Auto-ingest lore docs |
| **Tasks** | Polling | `updatedMin` | Mission/Quest status sync |
| **Sheets** | Polling | Value diffing | Character sheet tracking |
| **Docs** | Polling | Drive modifiedTime | Deep narrative parsing |

## Recent Achievements (2026-01-02)

- **YouTube Ingestion**: Fully automated from link paste to Notion promotion with AI Lore Briefings.
- **Lore Draft Index**: Syncing 12 technical drafts from Notion to local `lore/drafts/`.
- **World Bible Integration**: Added "Magnetic Consciousness Interface" and "Sireva" to the world config.
- **Agent Automations**: Integrated into `StoryEngine` via `:automate`.

---

*Last Updated: 2026-01-02*

