# Kaedra Capabilities Reference

> **Version**: v0.0.8  
> **Last Updated**: 2026-01-01

---

## 🎙️ Voice Engine

| Capability | Description |
|------------|-------------|
| **Real-time Voice Conversation** | Full-duplex voice interaction via `listen_and_speak.py` |
| **Speech-to-Text** | Whisper-based transcription (configurable: `base.en`, `distil-large-v3`) |
| **Text-to-Speech** | Google TTS with multiple variants (`flash`, `chirp-kore`) |
| **Barge-in Detection** | Interrupt Kaedra mid-speech |
| **Wake Threshold** | Configurable silence detection |
| **Wispr Integration** | Ingests transcriptions from Wispr Flow Desktop App |

---

## 🧠 AI Models & Reasoning

| Capability | Description |
|------------|-------------|
| **Gemini 3 Flash** | Fast responses, low-thinking tasks |
| **Gemini 3 Pro** | Deep reasoning, complex analysis |
| **Dynamic Model Routing** | Auto-selects model based on task complexity |
| **Thinking Levels** | Configurable (`low`, `medium`, `high`) |
| **Context Summarization** | Compresses long conversations to maintain history |

---

## 📖 StoryTime Engine (v6.0)

| Capability | Description |
|------------|-------------|
| **Cinematic Modes** | `NORMAL`, `FREEZE`, `ZOOM`, `ESCALATE`, `GOD`, `DIRECTOR`, `SHIFT_POV`, `REWIND` |
| **Emotion Physics** | Fear, Hope, Desire, Rage with decay, momentum, bleed |
| **Tension Curves** | Rising, Falling, Sawtooth, Climax, Dread patterns |
| **Narrative Structure** | 5-Act Yorke's Roadmap tracking |
| **Veil Manager** | Secret-keeping and revelation timing |
| **Character Voice Profiles** | POV-specific vocabulary and quirks |
| **Snapshots/Rewind** | Save and restore story states |
| **Session Logging** | Rich metadata per turn (timestamp, tension, emotions, tool calls) |

### Cinematic Modes Explained

- **NORMAL**: Standard storytelling, plot advancement
- **FREEZE**: Stop time, micro-expressions, suspended particles
- **ZOOM**: Hyper-focus on one detail, sensory overload
- **ESCALATE**: Spike tension, fast cuts, danger
- **GOD**: Architect mode, lore questions, worldbuilding
- **DIRECTOR**: Screenwriting workshop, structure, beats
- **SHIFT_POV**: Continue from a character's perspective
- **REWIND**: Alternative timeline, "what if" scenarios

---

## 💡 Smart Home (LIFX)

| Capability | Description |
|------------|-------------|
| **Power Control** | On/off, toggle, brightness |
| **Color Control** | Any color, kelvin temperature |
| **Effects** | Breathe, pulse, color cycle |
| **Mood Lighting** | Auto-adjusts based on emotional state/mode |
| **Multi-device** | Supports selectors (group, label, location) |

---

## 📝 Notion Integration

| Capability | Description |
|------------|-------------|
| **Read Pages** | Fetch content by title, URL, or ID |
| **Write/Append** | Add content to pages |
| **List Subpages** | Index universe content |
| **Universe Summary** | Get context injection for lore |

---

## 🌐 Web & Research

| Capability | Description |
|------------|-------------|
| **Web Fetching** | Scrape and parse web pages |
| **Google Search** | Search integration via Google Tools |
| **Deep Research** | Multi-source search → scrape → synthesis pipeline |

---

## 🎬 Video Generation

| Capability | Description |
|------------|-------------|
| **Text-to-Video** | Generate videos with Google Veo (3.1, 3.0, 2.0) |
| **Image-to-Video** | Use generated image as starting frame |
| **Video Extension** | Extend existing videos |

---

## 📊 Memory & Context

| Capability | Description |
|------------|-------------|
| **Memory Service** | Persistent memory across sessions |
| **Context Manager** | Smart history compression |
| **BigQuery Integration** | Analytics on session data |
| **GCS Storage** | Cloud storage for large content |

---

## 🔧 Tools & Agents

| Capability | Description |
|------------|-------------|
| **BLADE Agent** | Offensive analyst, action-focused |
| **NYX Agent** | Defensive observer, pattern-focused |
| **Kaedra Orchestrator** | Synthesizes BLADE/NYX perspectives |
| **Function Calling** | 7+ built-in tools for story engine |
| **Director Consultation** | Screenwriting frameworks on demand |

### Built-in StoryEngine Tools

- `read_page_content(page)` - Fetch Notion lore
- `list_universe_pages()` - Index available lore
- `update_page_content(page, text)` - Write to codex
- `read_local_lore(filename)` - Read from `lore/` directory
- `set_engine_mode(mode)` - Switch engine mode
- `consult_director(topic)` - Get screenwriting framework
- `adjust_emotion(emotion, delta)` - Shift emotional vector

---

## 💾 Persistence & Logging

| Capability | Description |
|------------|-------------|
| **Session Files** | Markdown logs in `lore/sessions/` |
| **Local Lore** | Read/write to `lore/*.md` files |
| **Structured Logging** | Rich console output with RichHandler |

---

## �️ Command Line Interface

| Capability | Description |
|------------|-------------|
| **Interactive REPL** | Full CLI at `kaedra/interface/cli.py` |
| **Multi-Agent Council** | `/council` command for BLADE + NYX + Kaedra discussions |
| **Tree of Thoughts** | `/tot` strategy for complex reasoning |
| **Battle of Bots** | Debate mode between agents |
| **System Info** | `/sysinfo` for diagnostics |
| **Command Help** | `/help` for all available commands |

### CLI Commands
```bash
# Start CLI
python -m kaedra

# Or directly
python kaedra/interface/cli.py
```

---

## 🌐 Fleet Communication (A2A Protocol)

| Capability | Description |
|------------|-------------|
| **OpenAI-Compatible API** | `/v1/chat/completions` endpoint |
| **A2A Card** | `/.well-known/agent.json` for agent discovery |
| **Fleet Health** | `/health` standard health check |
| **Fleet Generate** | `/generate` for direct text generation |
| **Fleet Search** | `/search` for grounded Google Search |
| **Fleet Analyze URL** | `/analyze-url` for web scraping |
| **Fleet Execute Code** | `/execute-code` for code simulation |
| **Deep Research** | `/research` for multi-source research tasks |
| **Embeddings** | `/v1/embeddings` for vector generation |

### Fleet Endpoints
```
POST /v1/chat/completions  - OpenAI-compatible chat
POST /chat                 - Fleet chat alias
POST /generate             - Direct text generation
POST /search               - Grounded search
POST /analyze-url          - URL analysis
POST /execute-code         - Code execution
POST /research             - Start research task
GET  /research/{id}        - Get research status
POST /v1/embeddings        - Create embeddings
GET  /.well-known/agent.json - Agent identity card
GET  /a2a                  - A2A card
GET  /health               - Health check
```

### Cloud Run URL
```
https://kaedra-69017097813.us-central1.run.app
```

---

## �📡 API & Cloud

| Capability | Description |
|------------|-------------|
| **FastAPI Backend** | REST API at `kaedra/api/main.py` |
| **Cloud Run Ready** | Containerized deployment |
| **Vertex AI** | Google Cloud AI integration |

---

## File Structure

```
kaedra/
├── agents/          # BLADE, NYX, Kaedra orchestrator
├── api/             # FastAPI backend
├── core/            # Config, models, engine, prompts
├── services/        # LIFX, Notion, TTS, STT, Video, Web, Research
├── skills/          # Universe skills
├── strategies/      # Response strategies
├── tools/           # Function calling tools
└── ui/              # Interface components

lore/                # Universe content
├── sessions/        # Story session logs
└── *.md             # Lore files

universe_text.py     # StoryTime Engine v6.0
listen_and_speak.py  # Voice Engine entry point
call_mode.py         # Voice call mode
```

---

## Quick Start

### Voice Mode
```bash
python listen_and_speak.py --model flash --tts flash
```

### StoryTime Engine
```bash
python universe_text.py
```

### API Server
```bash
uvicorn kaedra.api.main:app --reload
```
