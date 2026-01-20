# Kaedra V2: Autonomy & Fleet Integration Handoff

> **Purpose**: Enable long-running autonomous tasks with Slack/Notion/Kaedra orchestration
> **Pattern Source**: Ralph Claude Code + Who Visions Fleet Architecture
> **Target**: Production-ready console for Vertex AI + Worldbuilding

---

## 1. Ralph-Inspired Autonomy Loop

### Core Cycle (Adapted for Kaedra)

```
1. READ PROMPT    → Load task from Slack/Notion/handoff notes
2. EXECUTE AGENT  → Run Kaedra with Gemini 3 + tools
3. TRACK PROGRESS → Update Notion, log to Slack, mark checkpoints
4. EVALUATE EXIT  → Dual condition: completion_indicators + agent EXIT_SIGNAL
5. LOOP OR EXIT   → Continue until complete or limits reached
```

### Exit Detection (Ralph Pattern)

```python
exit_required = (
    completion_indicators >= 2  # Natural language heuristics
    AND agent_exit_signal == True  # Explicit confirmation from agent
)

# Other exit conditions:
# - All tasks in TASK_PLAN.md marked complete
# - Multiple consecutive "done" signals
# - Budget limit reached (token/cost cap)
# - Human interrupt via Slack
```

### Circuit Breaker Thresholds

```
NO_PROGRESS_LOOPS = 3      # Open circuit after 3 loops with no changes
SAME_ERROR_LOOPS = 5       # Open circuit after 5 repeated errors
OUTPUT_DECLINE = 70%       # Open if output drops by 70%+
```

---

## 2. V2 UI Features (Flutter)

### Chat Mode Chips

```
[ Professional ] [ Kaedra ] [ Unk ] [ Lore Scribe ] [ Command Only ]
```

- **Professional**: Neutral, business tone
- **Kaedra**: Full persona with AAVE, tactical mindset
- **Unk**: Unknown/exploratory voice
- **Lore Scribe**: Canon-focused, formal worldbuilding
- **Command Only**: Terse, tool-focused responses

### Chat Canonize Toggle

```
[ Canonize: OFF ] → Ephemeral conversation
[ Canonize: ON ]  → Suggestions save to Lore drafts
```

### Lore Editor Flow

- **Draft** → **Reviewed** → **Canon**
- Detail page with tabs: Overview | Links | Assets | History
- Card buttons: Open | Pin | Canonize | Generate Assets

### Prompt Builder (Create)

Step 1: Template (Portrait, Location, Scene, Prop, UI)
Step 2: Structured Fields (Subject, Camera, Lighting, Mood, Constraints)
Step 3: Generate & Save (to Lore, as Preset)

### Home Panels

- Recent Sessions
- Active Runs (queued/running/failed/completed)
- Daily Budget (tokens, images, video seconds)
- Model Router View (which model, why)

---

## 3. API Contract

### Core Endpoints

```
POST /chat/send         → message, mode, session_id, attachments
GET  /lore/search       → q, type, tags
GET  /lore/{id}
POST /lore
PATCH /lore/{id}
POST /lore/{id}/canonize
POST /create/image
POST /create/video
POST /create/text
GET  /runs
POST /runs              → Kick off autonomous workflow
```

### Lore Entry Schema

```json
{
  "id": "uuid",
  "type": "character|event|location|item|concept",
  "title": "string",
  "summary": "one paragraph",
  "body": "full text",
  "tags": ["veilverse", "fleet"],
  "universe": "VeilVerse",
  "timeline_year": 2181,
  "canon_status": "draft|reviewed|canon",
  "canon_confidence": 0.92,
  "importance": 10,
  "links": [{"type": "character", "id": "uuid", "label": "Dav3"}],
  "sources": [{"kind": "chat|notion", "ref": "session:abc"}],
  "assets": [{"kind": "image", "uri": "gs://...", "prompt": "..."}]
}
```

---

## 4. Autonomy Architecture

### Orchestration Stack

```
┌─────────────────────────────────────────────┐
│ COMMANDER (Dav3/User)                       │
│ → Slack command / Notion checkbox / App UI  │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│ KAEDRA CORE API (Cloud Run)                 │
│ → /runs endpoint starts autonomy loop       │
│ → Tracks progress in Notion                 │
│ → Posts updates to Slack                    │
│ → Enforces budget/rate limits               │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│ VERTEX AI (Gemini 3 Pro/Flash)              │
│ → Chat completions                          │
│ → Tool use (function calling)               │
│ → Code execution                            │
│ → Grounded search                           │
└─────────────────────────────────────────────┘
```

### Long-Running Task Flow

```
1. TRIGGER: Slack /kaedra run "expand all Olympus Mons locations"
2. CREATE RUN: Kaedra creates run record in Notion, posts to Slack
3. EXECUTE LOOP:
   - Agent reads context
   - Generates content
   - Writes to Notion
   - Updates Slack thread
   - Checks exit conditions
4. COMPLETE: Final Slack message with summary + links
```

### Session Continuity

- Persist `.kaedra_session` with context across loops
- Auto-reset on: circuit breaker open, manual interrupt, completion
- Log session transitions to `.kaedra_session_history`

---

## 5. Next Actions

### Immediate (This Sprint)

- [ ] Add mode chips to ChatScreen
- [ ] Add canonize toggle to chat
- [ ] Implement `/runs` endpoint with progress tracking
- [ ] Wire Slack notifications for run status

### Next Sprint

- [ ] Lore detail page with tabs
- [ ] Prompt builder 3-step flow
- [ ] Home panels (sessions, runs, budget)
- [ ] Circuit breaker implementation

### Future

- [ ] Autonomous workflow templates
- [ ] Multi-agent coordination (Kaedra + Antigravity + Nyx)
- [ ] Voice command integration
- [ ] Mobile offline sync with SQLite

---

## 6. Context-Aware Persona Rule

**Single rule that transforms feel:**

```
IF user_message.word_count < 5:
    → Reply short, neutral, offer actions
ELSE IF user_message.contains(mission_keywords):
    → Shift to tactical mode with full persona
ELSE:
    → Match user's energy level
```

This makes the agent feel intelligent, not scripted.

---

*Handoff created: 2026-01-13 20:25 EST*
*Source: Ralph Claude Code patterns + user V2 requirements*
