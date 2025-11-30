# KAEDRA v0.0.6 - Shadow Tactician

**Strategic AI Intelligence Partner for Who Visions LLC**

## Architecture

```
kaedra/
├── core/                   # Core infrastructure
│   ├── config.py          # Configuration & constants
│   ├── router.py          # Async response routing
│   └── version.py         # Version metadata
│
├── agents/                 # Agent implementations
│   ├── base.py            # Base agent class
│   ├── kaedra.py          # Main KAEDRA agent
│   ├── blade.py           # BLADE offensive analyst
│   └── nyx.py             # NYX strategic observer
│
├── services/               # Core services
│   ├── memory.py          # Persistent memory storage
│   ├── logging.py         # Session & system logging
│   └── prompt.py          # LLM interaction (Vertex AI)
│
├── strategies/             # Advanced prompting
│   ├── tree_of_thought.py # Multi-path reasoning
│   ├── battle_of_bots.py  # Adversarial validation
│   └── presets.py         # Prompt templates
│
└── interface/              # User interfaces
    └── cli.py             # Command-line interface
```

## Installation

```bash
# Clone or download the package
cd kaedra_v006

# Install dependencies
pip install -e .

# Or install directly
pip install google-cloud-aiplatform google-generativeai python-dotenv
```

## Setup

```bash
# Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project gen-lang-client-0285887798
```

## Usage

```bash
# Run KAEDRA
python run.py

# Or as module
python -m kaedra

# Or after pip install
kaedra
```

## Commands

### Model Switching
- `/flash` - Fast, cheap (~$0.008/query)
- `/pro` - Balanced (~$0.031/query)
- `/ultra` - Powerful (~$0.038/query)

### Agent Communication
- `/blade [msg]` - Talk to BLADE (aggressive analyst)
- `/nyx [msg]` - Talk to NYX (strategic observer)
- `/council [task]` - Multi-agent discussion

### Advanced Prompting
- `/tot [task]` - Tree of Thought analysis
- `/battle [task]` - Adversarial validation
- `/optimize [prompt]` - Prompt enhancement

### Memory System
- `/remember` - Store context
- `/recall [query]` - Search memories
- `/context` - List recent memories

### System
- `/status` - System health
- `/help` - Command reference
- `/exit` - Disconnect

## What's New in v0.0.6

- **Modular Architecture**: Clean separation of agents, services, strategies
- **Async Support**: ResponseRouter for concurrent operations
- **Enhanced Memory**: Importance levels, tag filtering, stats
- **Strategy Pattern**: Pluggable prompting strategies
- **Better Logging**: Session logs + system diagnostics

## Region

Deployed to `us-east4` (Virginia) for NYC latency optimization.

---

**Who Visions LLC** | Shadow Tactician v0.0.6
