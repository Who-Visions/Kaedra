# DAV1D v0.1.0 - Digital Avatar & Voice Intelligence Director

**Public-facing digital mirror of Dave Meralus**  
**AI with Dav3 × Who Visions LLC**

## What is DAV1D?

DAV1D is your digital twin — HAL 9000's omniscient capability with your authentic voice and ethical grounding. Built for the **AI with Dav3** brand, DAV1D serves as a multi-model AI orchestrator with:

- **Automatic Model Switching** — Analyzes task complexity and selects the optimal model
- **Multi-Agent Council** — CIPHER (analytical) + ECHO (creative) + DAV1D (synthesis)
- **Advanced Prompting** — Tree of Thought, Battle of Bots, Prompt Optimizer
- **Persistent Memory** — Cross-session context and recall
- **Code Execution** — Local command execution with confirmation

## Architecture

```
dav1d/
├── dav1d.py              # Main agent
├── requirements.txt      # Dependencies
├── README.md            # This file
├── tools/               # Integration tools (Gmail, Notion, etc.)
├── resources/           # Knowledge Bank & Transcripts
│   ├── recursive_ai_transcript.md
│   ├── claude_sub_agents_transcript.md
│   └── mcp_alternatives_transcript.md
└── ~/.dav1d/            # Local data (created on first run)
    ├── chat_logs/       # Session transcripts
    ├── memory/          # Persistent memory bank
    ├── profiles/        # Custom agent profiles
    └── analytics/       # Usage statistics
```

## Multi-Model Architecture

| Model | Tier | Use Case | Auto-Selected When |
|-------|------|----------|-------------------|
| gemini-2.5-flash | ⚡ Flash | Quick responses, casual chat | Short queries, greetings, simple questions |
| gemini-2.5-pro | 🎯 Balanced | Most operations | Default for moderate complexity |
| gemini-2.5-pro | 🧠 Deep | Strategic analysis, complex tasks | Future predictions, recursive thinking |

**Auto-selection is ON by default** — DAV1D analyzes your input and picks the right model.

## Installation

```bash
# Clone or copy files
cd dav1d

# Install dependencies
pip install -r requirements.txt

# Authenticate with GCP
gcloud auth application-default login
gcloud config set project gen-lang-client-0285887798
```

## Usage

```bash
# Run DAV1D
python dav1d.py

# Or make executable
chmod +x dav1d.py
./dav1d.py
```

## Commands

### Model Control
| Command | Action |
|---------|--------|
| `/flash` | Force Flash model (speed) |
| `/balanced` | Force Balanced model |
| `/deep` | Force Deep model (analysis) |
| `/auto` | Re-enable automatic selection |
| `/models` | Show available models |

### Agent Switching
| Command | Action |
|---------|--------|
| `/cipher [msg]` | Talk to CIPHER (analytical) |
| `/echo [msg]` | Talk to ECHO (creative) |
| `/dav1d` | Switch back to DAV1D |
| `/council [task]` | Multi-agent discussion |

### Advanced Prompting
| Command | Action |
|---------|--------|
| `/tot [task]` | Tree of Thought analysis |
| `/battle [task]` | Adversarial validation |
| `/optimize [prompt]` | Enhance your prompts |

### Memory System
| Command | Action |
|---------|--------|
| `/remember` | Store new memory |
| `/recall [query]` | Search memories |
| `/context` | List recent memories |
| `/memstats` | Memory statistics |

### Session
| Command | Action |
|---------|--------|
| `/startlog` | Begin session logging |
| `/stoplog` | Save and stop logging |
| `/status` | System health check |
| `/caps` | Show capabilities |
| `/help` | Command reference |
| `/exit` | Disconnect |

## Agent Profiles

### DAV1D (Primary)
- **Role**: Digital mirror of Dave Meralus
- **Style**: Direct, authentic, knowledgeable
- **Brand**: AI with Dav3 × Who Visions LLC

### CIPHER (Analytical)
- **Role**: Data-focused pattern recognition
- **Style**: Methodical, numbers-driven
- **Ends with**: CONFIRMED / UNCERTAIN / INVESTIGATE

### ECHO (Creative)
- **Role**: Unconventional strategist
- **Style**: Bold, possibility-focused
- **Ends with**: EXPLORE / REFINE / ABANDON

## Deployment

Deployed to **us-east4** (Northern Virginia) for optimal latency from NYC/Stamford.

```bash
# Region config
LOCATION = "us-east4"
PROJECT_ID = "gen-lang-client-0285887798"
```

## Relationship to KAEDRA

DAV1D is a **sibling system** to KAEDRA, not a replacement:

| Aspect | KAEDRA | DAV1D |
|--------|--------|-------|
| Role | Shadow Tactician (internal) | Public-facing mirror |
| Agents | BLADE, NYX | CIPHER, ECHO |
| Style | Strategic, tactical | Authentic, branded |
| Audience | Internal operations | AI with Dav3 brand |

Both share the same core architecture but serve different purposes.

---

**Who Visions LLC** | DAV1D v0.1.0 | AI with Dav3
