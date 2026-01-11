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
