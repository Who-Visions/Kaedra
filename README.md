# 🌑 KAEDRA StoryEngine v7.15

<div align="center">

```
██╗  ██╗ █████╗ ███████╗██████╗ ██████╗  █████╗ 
██║ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗
█████╔╝ ███████║█████╗  ██║  ██║██████╔╝███████║
██╔═██╗ ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║
██║  ██╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

**🎬 Elite Narrative Intelligence & Cinematic Universe Architect**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini%203-orange)](https://cloud.google.com/vertex-ai)
[![Rich UI](https://img.shields.io/badge/Console-Rich%20Live-purple)](https://github.com/Textualize/rich)
[![Voice](https://img.shields.io/badge/Voice-Wispr%20Flow-green)](https://www.wispr.ai/)
[![Lights](https://img.shields.io/badge/Hardware-LIFX%20%2B%20Razer-red)](#-hardware-integration)

[Features](#-core-features) • [Commands](#-writing-commands) • [Tools](#-engine-tools) • [Services](#-services) • [Agents](#-agents) • [Hardware](#-hardware-integration) • [Quick Start](#-quick-start)

</div>

---

## 🎯 What is KAEDRA?

KAEDRA is a **Story Engine** and **Universe Architect** for deep narrative work. She orchestrates creative writing sessions, manages complex lore databases, controls ambient lighting, and automates the production pipeline for the **VeilVerse** cinematic universe.

---

## 🔥 Core Features

| Feature | Description |
|---------|-------------|
| 🧠 **Multi-Tier AI** | Gemini 3 Pro/Flash with Smart Routing and Thinking Levels |
| 📜 **World Registry** | Multi-save system with persistent world states |
| 🤖 **Universe Automations** | Self-cleaning database (Canon, Timeline, Power scoring) |
| 🎤 **Voice Dictation** | Wispr Flow integration for hands-free writing |
| 💡 **Ambient Lighting** | LIFX bulbs + Razer Blade 15 keyboard sync |
| 📟 **Rich Live UI** | "Writer Friendly" console with persistent footer |
| 🌙 **Night Mode** | Adaptive lighting with safety caps (11PM-8AM) |
| ⚡ **Smart Input** | Paste detection and raw terminal handling |

---

## 🎮 Writing Commands

Use `:` prefix for commands. Natural language for writing.

### 📝 Writing Flow

| Command | Description |
|---------|-------------|
| `:next` | ⏭️ Advance to next Scene (resets Tension) |
| `:pov [name]` | 👁️ Switch Point of View |
| `:freeze` | ❄️ Enter "Bullet Time" mode |
| `:god` | 🌍 Enter Worldbuilding/Lore mode |
| `:emotion [emo] [val]` | 💫 Pulse specific emotion |
| `:quit` | 💾 Save and Exit |

### 🤖 Automation

| Command | Description |
|---------|-------------|
| `:automate` | 🔄 Run Universe Automations (Canon, Timeline, Power) |
| `:roadmap new` | 📋 Create project roadmap template |
| `:roadmap tasks` | ✅ Generate milestone tasks |
| `:roadmap diag` | 🔍 25 Expert Roadblock Checks |
| `:roadmap names` | 🎭 Character Authenticity Protocol |
| `:roadmap add` | 📅 Sync to Google Tasks |
| `:roadmap sync` | 🔗 Sync to Notion + Drive |

### 💡 Hardware

| Command | Description |
|---------|-------------|
| `:lights fire` | 🔥 Fire atmosphere (LIFX flame + Razer sparks) |
| `:lights restore` | ☀️ Restore baseline lighting |
| `:voice on` | 🎤 Enable voice dictation |
| `:voice off` | 🔇 Disable voice dictation |

---

## 🛠️ Engine Tools

AI-callable functions available during generation:

### 📚 Lore & Notion

| Tool | Purpose |
|------|---------|
| `read_page_content` | 📖 Read Notion page content |
| `list_universe_pages` | 📂 List all lore pages |
| `update_page_content` | ✏️ Edit Notion page |
| `run_lore_automations` | ⚙️ Canon promotion, retcon safety |
| `read_local_lore` | 📁 Read local JSON lore files |
| `propose_canon_update` | 💡 Suggest lore changes |

### 🎬 Screenwriting

| Tool | Purpose |
|------|---------|
| `consult_director` | 🎥 Screenwriting guidance (structure, character, twist, etc.) |
| `set_engine_mode` | 🎭 Switch writing mode |
| `adjust_emotion` | 💫 Pulse emotional state |
| `clean_timeline_data` | 📅 Auto-tag timeline eras |

### 🌍 World Building

| Tool | Purpose |
|------|---------|
| `ingest_youtube_content` | 📺 Extract YouTube transcripts |
| `worldforge_from_youtube` | 🌱 Create worlds from videos |

---

## 🔌 Services

### 💡 Hardware Control

| Service | Description |
|---------|-------------|
| `lifx.py` (27KB) | 💡 LIFX bulb control (colors, effects, scenes) |
| `razer.py` (13KB) | ⌨️ Razer Chroma keyboard (per-key matrix, fire effect) |

### 🎤 Voice & Audio

| Service | Description |
|---------|-------------|
| `wispr.py` (8KB) | 🎤 Wispr Flow Desktop integration (dictation) |
| `wispr_cloud.py` (5KB) | ☁️ Wispr Cloud API |
| `tts.py` (15KB) | 🔊 Text-to-Speech (Gemini TTS) |
| `tts_chatterbox.py` (7KB) | 🗣️ Chatterbox TTS alternative |
| `mic.py` (7KB) | 🎙️ Microphone input handling |
| `vad.py` (1KB) | 🔈 Voice Activity Detection |
| `transcription.py` (3KB) | ✍️ Speech-to-text conversion |

### 📋 Productivity

| Service | Description |
|---------|-------------|
| `notion.py` (15KB) | 📓 Notion API integration |
| `google_workspace.py` (5KB) | 📅 Google Calendar/Tasks API |
| `invoices.py` (43KB) | 💰 Invoice generation & tracking |

### 🌐 Research & Media

| Service | Description |
|---------|-------------|
| `video.py` (11KB) | 🎬 Video ingestion & analysis |
| `web.py` (5KB) | 🌍 Web scraping & content extraction |
| `research.py` (5KB) | 🔍 Research aggregation |
| `memory.py` (9KB) | 🧠 Long-term memory management |

### ⚙️ Core

| Service | Description |
|---------|-------------|
| `prompt.py` (12KB) | 📝 Gemini 3 Smart Router & Thought Extraction |
| `logging.py` (7KB) | 📊 Session logging (JSON turns) |
| `fast_flow.py` (6KB) | ⚡ Fast streaming responses |

---

## 🤖 Agents

Multi-agent system with specialized personas:

| Agent | Role | Description |
|-------|------|-------------|
| 🗡️ **Blade** | System AI | Core orchestration and tool execution |
| 👥 **Council** | Multi-Agent | Collaborative decision-making |
| 🌑 **Kaedra** | Story Persona | Narrative intelligence and writing |
| 🌙 **Nyx** | Dark Persona | Alternative creative voice |

---

## 🎨 Hardware Integration

### 💡 LIFX Smart Lights

| Feature | Description |
|---------|-------------|
| Color Control | HSB + Kelvin temperature |
| Flame Effect | Flickering fire ambiance |
| Breathe/Pulse | Rhythmic color cycling |
| Night Mode | Auto-dim after 11PM (35% red) |
| Day Mode | 4500K warm white @ 60% |
| Selector | Target specific groups/zones |

### ⌨️ Razer Blade 15 Keyboard

| Feature | Description |
|---------|-------------|
| Static Colors | Solid color across all keys |
| Per-Key Matrix | 8x24 grid control (CHROMA_CUSTOM2) |
| Fire Animation | 🔥 Flickering sparks (threaded) |
| Wave Effect | Color sweep across keyboard |
| ChromaLink | 5 virtual LEDs for 3rd party devices |
| Breathing | Two-color pulse effect |

**Requirements:**

- Razer Synapse 4 Beta (fixes REST API errors)
- Enable "Kaedra Story Engine" in Chroma Apps

---

## 🌍 World Registry

Each world is a self-contained folder in `lore/worlds/`:

```
lore/worlds/world_id/
├── world.json          # 🎭 Manifest (Mode, Scene, POV, Tension)
├── world_bible.json    # 📖 Characters, Lore, Locations
├── timeline.json       # 📅 Chronological Events
├── canon.json          # ✅ Established Truths
├── ingestion.json      # 📥 Incoming Ideas Queue
└── notifications.md    # 🔔 System Alerts
```

---

## 🤖 Universe Automations

Trigger with `:automate` command:

### 📦 Production Pipeline

- **Canon Promotion**: `Concept` → `In Development`
- **Release Closeout**: `Released` → `Completed` + `Phase 1` tag

### ✅ Consistency Checks

- **Timeline Validator**: Auto-tag Era (Ancient, Classical, Modern, Future)
- **Power Scoring**: Calculate `Importance Score` (30-95) from Power Level
- **Retcon Safety**: Rename + deactivate retconned entries

### 🔗 Connection & Media

- **Major Characters**: Alert for connection review
- **Media Alerts**: Ping social scheduler on release
- **Ingestion**: Move "Approved" ideas to Bible

---

## 🏗️ Architecture

```
kaedra/
├── 🧠 core/              # Core config & models
├── 📜 story/             # Story Engine Logic
│   ├── engine.py         # Main Event Loop (2400+ lines)
│   ├── emotions.py       # Emotional Simulation
│   ├── tension.py        # Narrative Tension Curve
│   ├── lights.py         # LIFX + Razer Integration
│   ├── doctrine.py       # Writing Doctrine (MICE, Barthes, etc.)
│   ├── worldforge.py     # World Building Tools
│   └── tools/            # AI-Callable Functions
│
├── 🔌 services/          # External Integrations (19 modules)
├── 🤖 agents/            # AI Personas (Blade, Council, Kaedra, Nyx)
├── 🌍 worlds/            # Universe Management
├── 🛠️ skills/            # Agent Capabilities
└── 📋 strategies/        # Generation Strategies
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud Vertex AI credentials
- LIFX Token (optional)
- Razer Synapse 4 Beta (optional)
- Wispr Flow Desktop (optional)

### Launch

```bash
# Enter the Story Engine
python -m kaedra.story.engine

# Or with voice mode
python -m kaedra.story.engine --voice
```

1. Select **N** to create a new world (or select existing)
2. Start writing naturally
3. Use `:automate` to clean your lore database

---

## 🎨 Brand

**Who Visions LLC** | Strategic AI Intelligence

- 📸 **Instagram**: [@aiwithdav3](https://instagram.com/aiwithdav3)
- 🎬 **YouTube**: [Ai with Dav3](https://youtube.com/aiwithdav3)
- 🌐 **Website**: [WhoVisions.com](https://WhoVisions.com)

---

## 📜 License

Proprietary - Who Visions LLC © 2026

---

## 🚀 Beyond The Story Engine

> **KAEDRA is more than a writing tool—it's a complete AI Agent Framework.**

---

## 🌐 FastAPI Server & A2A Protocol

KAEDRA exposes a production-ready **FastAPI server** supporting Google's Agent-to-Agent (A2A) protocol:

```bash
# Launch the API server
uvicorn kaedra.api.main:app --host 0.0.0.0 --port 8080
```

### 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | 🏠 Health check |
| `/agent.json` | GET | 🤖 A2A Agent Card |
| `/.well-known/agent.json` | GET | 🔍 A2A Discovery |
| `/v1/models` | GET | 📊 Available models |
| `/a2a` | POST | 💬 Agent-to-Agent messaging |
| `/generate` | POST | ✨ Text generation |
| `/generate/image` | POST | 🖼️ Image generation (Imagen) |
| `/generate/video` | POST | 🎬 Video generation (Veo 3) |
| `/query` | POST | 🧠 Reasoning engine query |
| `/metrics` | GET | 📈 Prometheus metrics |

### 🔑 Authentication

- Google Cloud IAM (Cloud Run)
- API Key header (`X-API-Key`)
- Service Account tokens

---

## 🧵 Thread-Based Engineering

**NEW: Implements Andy Devdan's framework + Geoffrey Huntley's Ralph Wiggum pattern.**

```python
from kaedra.core.threads import create_ralph, create_lthread, create_pthread

# Ralph Wiggum Pattern (infinite loop)
ralph = create_ralph("PROMPT.md", my_agent, timeout_hours=24)
result = await ralph.run()

# L-Thread (validation loop)
lthread = create_lthread(agent_fn, validator_fn, max_iterations=100)
result = await lthread.run("Fix all issues")

# P-Thread (parallel execution)
pthread = create_pthread(max_concurrent=5)
results = await pthread.run_parallel(agents, prompts)
```

### 🧵 Thread Types

| Thread | Class | Purpose |
|--------|-------|---------|
| 📎 **Base** | `BaseThread` | Prompt → Work → Review |
| 🔀 **P-Thread** | `PThreadRunner` | Parallel execution (5 concurrent) |
| ⛓️ **C-Thread** | `CThreadRunner` | Chained phases with checkpoints |
| 🔗 **F-Thread** | `FThreadRunner` | Fusion/best-of-N pattern |
| 🏃 **L-Thread** | `LThreadRunner` | Long-duration with validation |
| 🔄 **Ralph** | `RalphRunner` | Infinite loop (ghuntley.com) |

### ✅ Validation Hooks

| Validator | Purpose |
|-----------|---------|
| `validate_command()` | Run shell commands |
| `validate_pylint()` | Check Pylint score |
| `validate_tests()` | Run pytest |
| `validate_all()` | Combine validators |

---

## 🎯 Skill Packs

Modular capabilities organized by domain:

| Skill Pack | Description |
|------------|-------------|
| 🎬 **Universe** | Story engine, lore management, world building |
| 💰 **Financial** | Invoice generation, payment tracking |
| 📷 **Photography** | Image analysis, visual processing |
| 🎖️ **Tactical** | System operations, deployment |
| 🔍 **Introspective** | Self-analysis, debugging |
| ⚙️ **Default** | Core agent capabilities |

---

## 🧠 Core Modules

### 🔧 Engine & Infrastructure

| Module | Size | Purpose |
|--------|------|---------|
| `threads.py` | 24KB | 🧵 Thread-based engineering (6 thread types) |
| `engine.py` | 22KB | ⚡ Core reasoning engine |
| `tools.py` | 18KB | 🛠️ Tool execution framework |
| `config.py` | 11KB | ⚙️ Environment & credentials |
| `google_tools.py` | 12KB | 🔌 Google API integrations |
| `validation.py` | 10KB | ✅ Stop-hook validators |
| `skills.py` | 10KB | 🎯 Skill registration & routing |

### 🤖 AI Routing

| Module | Purpose |
|--------|---------|
| `prompts.py` | 📝 System prompts & persona management |
| `router.py` | 🔀 Smart model routing (Flash/Pro) |
| `retry.py` | 🔄 Exponential backoff & fallbacks |
| `isolation.py` | 🔒 Sandboxed execution |

---

## 🖼️ Visual Services

| Capability | Model | Description |
|------------|-------|-------------|
| 🖼️ **Image Gen** | Imagen 3 | High-quality image generation |
| 🎬 **Video Gen** | Veo 3 | 8-second video clips |
| 👁️ **Vision** | Gemini 3 | Image analysis & understanding |
| 🔍 **OCR** | Vertex AI | Document text extraction |

---

## 📊 Observability

| Feature | Description |
|---------|-------------|
| 📈 **Prometheus** | `/metrics` endpoint |
| 📝 **JSON Logs** | Structured session logging |
| 💰 **Cost Tracking** | Per-request token/$ tracking |
| 🔍 **Tracing** | Request correlation IDs |

---

## 🐳 Deployment Options

| Platform | Status | Notes |
|----------|--------|-------|
| ☁️ **Cloud Run** | ✅ Production | Auto-scaling, IAM auth |
| 🧠 **Reasoning Engine** | ✅ Deployed | Vertex AI managed |
| 🖥️ **Local** | ✅ Dev | `uvicorn` or `story.engine` |
| 🐳 **Docker** | ✅ Available | Multi-stage build |

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| 🎯 **Pylint Score** | 7.91/10 |
| 📦 **Total Modules** | 80+ Python files |
| 🔌 **Services** | 26 integrations |
| 🤖 **Agents** | 4 personas |
| 🧵 **Thread Types** | 6 patterns |

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GOOGLE_CLOUD_PROJECT="your-project"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Optional
export LIFX_TOKEN="your-lifx-token"
export NOTION_API_KEY="your-notion-key"
export WISPR_API_KEY="your-wispr-key"
```

### mprocs (Parallel Agents)

```yaml
# mprocs.yaml - P-Thread Configuration
procs:
  agent1:
    shell: "while :; do cat PROMPT.md | claude-code; done"
  agent2:
    shell: "while :; do cat PROMPT.md | claude-code; done"
  pylint:
    shell: "py -3.12 -m pylint kaedra --score=y"
    autostart: false
```

---

## 🎓 Thread Engineering Resources

| Resource | Link |
|----------|------|
| 🎬 **Andy Devdan Video** | [Agent Threads](https://www.youtube.com/watch?v=-WBHNFAB0OE) |
| 📖 **Ralph Wiggum** | [ghuntley.com/ralph](https://ghuntley.com/ralph/) |
| 🔧 **mprocs** | [github.com/pvolok/mprocs](https://github.com/pvolok/mprocs) |
| 📦 **repomirror** | [repomirror.md](https://github.com/repomirrorhq/repomirror) |

---

<div align="center">

**🌑 KAEDRA — From Story Engine to Full AI Agent Framework**

*Thread-Based Engineering • A2A Protocol • Visual AI • Hardware Control*

</div>
