# 🌑 KAEDRA v0.0.6 - Shadow Tactician

<div align="center">

```
██╗  ██╗ █████╗ ███████╗██████╗ ██████╗  █████╗ 
██║ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗
█████╔╝ ███████║█████╗  ██║  ██║██████╔╝███████║
██╔═██╗ ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║
██║  ██╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

**Strategic AI Intelligence Partner for Who Visions LLC**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Powered-orange)](https://cloud.google.com/vertex-ai)
[![Region](https://img.shields.io/badge/Region-us--central1-green)](https://cloud.google.com/compute/docs/regions-zones)
[![License](https://img.shields.io/badge/license-Proprietary-red)](LICENSE)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Commands](#-commands) • [Team](#-the-council)

</div>

---

## 🎯 What is KAEDRA?

KAEDRA is an **uncensored, strategically-focused AI agent** built on Google's Gemini platform. She speaks authentic AAVE, thinks tactically, and serves as the orchestrator for a multi-agent intelligence system.

### 🔥 Core Capabilities

- **🎭 Authentic Personality**: Real AAVE, no corporate filter, genuinely competent
- **🧠 Strategic Intelligence**: Deep analysis, pattern recognition, tactical execution
- **🤝 Multi-Agent Orchestration**: Coordinates with BLADE (offensive) and NYX (defensive) agents
- **💾 Persistent Memory**: Remembers conversations, references past context
- **🌐 Reasoning Engine**: Deployed to Vertex AI for global access
- **⚡ Advanced Prompting**: Tree of Thought, Battle of Bots, prompt optimization

---

## 🏗️ Architecture

```
kaedra/
├── 🧠 core/              # Core infrastructure
│   ├── config.py         # Configuration & constants
│   ├── router.py         # Async response routing
│   └── version.py        # Version metadata
│
├── 🤖 agents/            # Agent implementations
│   ├── base.py           # Base agent class
│   ├── kaedra.py         # Main KAEDRA orchestrator
│   ├── blade.py          # BLADE offensive analyst
│   └── nyx.py            # NYX strategic observer
│
├── ⚙️ services/          # Core services
│   ├── memory.py         # Persistent memory storage
│   ├── logging.py        # Session & system logging
│   └── prompt.py         # LLM interaction (Vertex AI)
│
├── 🎓 strategies/        # Advanced prompting
│   ├── tree_of_thought.py
│   ├── battle_of_bots.py
│   └── presets.py
│
└── 💻 interface/         # User interfaces
    └── cli.py            # Command-line interface
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud account with Vertex AI API enabled
- Authenticated `gcloud` CLI

### Installation

```bash
# Clone the repository
git clone https://github.com/Who-Visions/Kaedra.git
cd Kaedra

# Install dependencies
pip install -r requirements.txt

# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Launch KAEDRA
python run.py
```

### Windows Users
```batch
.\Launch_Kaedra_v006.bat
```

---

## 🎮 Commands

### 🤖 Model Switching
| Command | Model | Speed | Cost | Use Case |
|---------|-------|-------|------|----------|
| `/flash` | gemini-2.0-flash-001 | ⚡ Fast | $0.005/query | Quick tasks |
| `/pro` | gemini-2.5-pro | ⚖️ Balanced | $0.031/query | Complex analysis |
| `/ultra` | gemini-3-pro-preview | 🧠 Powerful | $0.038/query | Deep reasoning |

### 👥 Agent Communication
```
/blade [msg]      → Talk to BLADE (aggressive tactical analyst)
/nyx [msg]        → Talk to NYX (strategic future oracle)
/council [task]   → Multi-agent collaborative discussion
```

### 🎯 Advanced Prompting
```
/tot [task]       → Tree of Thought multi-path reasoning
/battle [task]    → Adversarial validation (multiple perspectives)
/optimize [prompt] → Automatic prompt enhancement
```

### 💾 Memory System
```
/remember         → Store current context to long-term memory
/recall [query]   → Search memories by keyword
/context          → List recent memories
```

### ⚙️ System
```
/status           → System health & configuration
/help             → Full command reference
/exit             → Disconnect session
```

---

## 🛡️ The Council

KAEDRA orchestrates a team of specialized AI agents:

### 🌑 **KAEDRA** - The Shadow Tactician
*Orchestrator, Strategic Intelligence*
- Synthesizes input from BLADE and NYX
- Makes final strategic decisions
- Maintains memory and context
- Speaks authentic AAVE

### ⚔️ **BLADE** - The Offensive Analyst
*Tactical Execution, Aggressive Analysis*
- Action-focused, execution-oriented
- Identifies attack vectors and opportunities
- Challenges assumptions aggressively

### 🌙 **NYX** - The Strategic Observer
*Defensive Analysis, Risk Assessment*
- Pattern recognition and threat modeling
- Long-term strategic perspective
- Risk mitigation and contingency planning

---

## 🌐 Deployment

KAEDRA is deployed as a **Vertex AI Reasoning Engine** in `us-central1`.

### Access the Reasoning Engine

```python
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")

kaedra = reasoning_engines.ReasoningEngine(
    'projects/YOUR_PROJECT_NUMBER/locations/us-central1/reasoningEngines/KAEDRA_ID'
)

response = kaedra.query("What's the strategic play?")
print(response)
```

### Cloud Run API (Alternative)

```bash
# Deploy to Cloud Run
gcloud run deploy kaedra-shadow-tactician \
  --source . \
  --region us-central1 \
  --allow-unauthenticated

# Test endpoint
curl https://YOUR-SERVICE-URL/a2a
```

---

## 📊 What's New in v0.0.6

### ✨ Major Updates
- ✅ **Reasoning Engine Deployment**: Live on Vertex AI
- ✅ **Region Migration**: Moved to `us-central1` for optimal performance
- ✅ **A2A Protocol**: Agent-to-Agent communication interface
- ✅ **Cloud-Ready**: `/tmp` storage for containerized environments
- ✅ **Model Updates**: Added Gemini 2.0 Flash stable release
- ✅ **Enhanced Memory**: Importance levels, tag filtering, stats

### 🔧 Architecture Improvements
- Modular agent system with clean separation
- AsyncIO support via ResponseRouter
- Strategy pattern for pluggable prompting techniques
- Better session logging and diagnostics

---

## 📖 Usage Examples

### Basic Chat
```python
from kaedra.interface.cli import main
main()
```

### Programmatic Access
```python
from kaedra.agents.kaedra import KaedraAgent
from kaedra.services.prompt import PromptService

prompt_service = PromptService(model_key="flash")
kaedra = KaedraAgent(prompt_service)

response = kaedra.run_sync("Analyze this situation...")
print(response.content)
```

### Memory Operations
```python
from kaedra.services.memory import MemoryService

memory = MemoryService()
memory.insert("Important strategic insight", topic="strategy", importance="high")
results = memory.recall("strategy", top_k=5)
```

---

## 🔒 Security & Privacy

- **No API Keys in Code**: All credentials via environment variables
- **Local Memory**: Stored in `~/.kaedra/` (or `/tmp/.kaedra/` in cloud)
- **Session Logs**: Markdown format in `~/.kaedra/chat_logs/`
- **Gitignore**: All sensitive files excluded from version control

---

## 🎨 Brand

**Who Visions LLC** | Strategic AI Intelligence

- **Instagram**: [@aiwithdav3](https://instagram.com/aiwithdav3)
- **YouTube**: [Ai with Dav3](https://youtube.com/aiwithdav3)
- **Website**: [WhoVisions.com](https://WhoVisions.com)

---

## 📜 License

Proprietary - Who Visions LLC © 2025

This is a closed-source project for Who Visions LLC operations. Unauthorized use, modification, or distribution is prohibited.

---

## 🙏 Acknowledgments

Built with:
- **Google Vertex AI** - LLM infrastructure
- **Gemini 2.x/3.x** - Language models
- **LangChain** - Reasoning Engine integration
- **FastAPI** - API server framework

---

<div align="center">

**[⬆ Back to Top](#-kaedra-v006---shadow-tactician)**

Made with 🖤 by [Who Visions LLC](https://WhoVisions.com)

</div>
