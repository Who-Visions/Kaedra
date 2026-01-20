#!/bin/bash
# ============================================================================
# KAEDRA Cloud Shell Setup
# One-command setup for Blade/Nyx agent deployment
# Usage: curl -sSL https://raw.githubusercontent.com/Who-Visions/Kaedra/main/scripts/cloudshell_setup.sh | bash
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
PROJECT_ID="gen-lang-client-0939852539"
WORKSPACE="${HOME}/kaedra"
VENV="${WORKSPACE}/.venv"

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄  ▄▄▄▄▄▄   ▄▄▄▄▄▄▄           ║"
echo "║   █       █       █       █      ██       █ █       █          ║"
echo "║   █   ▄   █   ▄▄▄▄█   ▄   █  ▄    █   ▄   █ █   ▄   █          ║"
echo "║   █  █ █  █  █  ▄▄█  █ █  █ █ █   █  █▄█  █ █  █▀█  █          ║"
echo "║   █  █▄█  █  █ █  █  █▄█  █ █▄█   █       █ █   ▄▄█ █          ║"
echo "║   █       █  █▄▄█ █       █       █   ▄   █ █  █    █          ║"
echo "║   █▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄██▄▄█ █▄▄█ █▄▄█    █▄▄▄▄▄▄▄  ║"
echo "║                                                               ║"
echo "║   Cloud Shell Agent Deployment                                ║"
echo "║   BLADE + NYX Autonomous Loop                                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Configure Project
echo -e "${CYAN}[1/6] Configuring GCP project...${NC}"
gcloud config set project ${PROJECT_ID} 2>/dev/null
echo -e "${GREEN}[✓] Project set to ${PROJECT_ID}${NC}"

# Step 2: Clone Repository
echo -e "${CYAN}[2/6] Setting up workspace...${NC}"
if [ -d "${WORKSPACE}" ]; then
    echo -e "${YELLOW}[!] Workspace exists, pulling latest...${NC}"
    cd "${WORKSPACE}"
    git pull origin main 2>/dev/null || git pull 2>/dev/null || true
else
    echo -e "${CYAN}[*] Cloning Kaedra repository...${NC}"
    git clone https://github.com/Who-Visions/Kaedra.git "${WORKSPACE}" 2>/dev/null || \
    git clone git@github.com:Who-Visions/Kaedra.git "${WORKSPACE}"
    cd "${WORKSPACE}"
fi
echo -e "${GREEN}[✓] Workspace ready at ${WORKSPACE}${NC}"

# Step 3: Create Virtual Environment
echo -e "${CYAN}[3/6] Setting up Python environment...${NC}"
if [ ! -d "${VENV}" ]; then
    python3 -m venv "${VENV}"
fi
source "${VENV}/bin/activate"
echo -e "${GREEN}[✓] Virtual environment activated${NC}"

# Step 4: Install Dependencies
echo -e "${CYAN}[4/6] Installing dependencies...${NC}"
pip install --quiet --upgrade pip
pip install --quiet google-genai httpx toml pydantic python-dotenv rich
if [ -f "requirements.txt" ]; then
    pip install --quiet -r requirements.txt 2>/dev/null || true
fi
echo -e "${GREEN}[✓] Dependencies installed${NC}"

# Step 5: Verify Authentication
echo -e "${CYAN}[5/6] Verifying Vertex AI authentication...${NC}"
if gcloud auth application-default print-access-token &>/dev/null; then
    echo -e "${GREEN}[✓] ADC authentication active${NC}"
else
    echo -e "${YELLOW}[!] Setting up ADC...${NC}"
    gcloud auth application-default login --quiet
fi

# Step 6: Create Agent Runner
echo -e "${CYAN}[6/6] Creating agent runner...${NC}"
cat > "${WORKSPACE}/run_loop.py" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
KAEDRA Autonomous Agent Loop
Runs Blade and Nyx agents alternately on task queue
"""
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add kaedra to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Configuration
MAX_LOOPS = 50
LOOP_DELAY = 10  # seconds between loops
PROTOCOL_FILE = Path(__file__).parent / ".agent" / "AGENT_PROTOCOL.md"
LOG_FILE = Path(__file__).parent / ".agent" / "agent_loop.log"

def log(msg: str):
    """Log to file and console"""
    timestamp = datetime.now().isoformat()
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    console.print(f"[dim]{timestamp}[/dim] {msg}")

def run_blade(task: str) -> str:
    """Execute Blade agent on technical task"""
    try:
        from kaedra.agents.blade import BladeAgent
        agent = BladeAgent()
        result = agent.query(task)
        return result.response if hasattr(result, 'response') else str(result)
    except Exception as e:
        return f"BLADE ERROR: {e}"

def run_nyx(task: str) -> str:
    """Execute Nyx agent on creative/research task"""
    try:
        from kaedra.agents.nyx import NyxAgent
        agent = NyxAgent()
        result = agent.query(task)
        return result.response if hasattr(result, 'response') else str(result)
    except Exception as e:
        return f"NYX ERROR: {e}"

def get_next_task(agent: str) -> str:
    """Get next unclaimed task for agent from protocol"""
    if not PROTOCOL_FILE.exists():
        return None
    
    content = PROTOCOL_FILE.read_text()
    prefix = "B" if agent == "BLADE" else "N"
    
    # Find unclaimed tasks
    for line in content.split("\n"):
        if f"| {prefix}" in line and "[ ]" in line:
            # Extract task description
            parts = line.split("|")
            if len(parts) >= 3:
                return parts[2].strip()
    return None

def check_exit_signal() -> bool:
    """Check if exit signal is set"""
    if PROTOCOL_FILE.exists():
        content = PROTOCOL_FILE.read_text()
        return "EXIT_SIGNAL: true" in content
    return False

def main():
    console.print(Panel.fit(
        "[bold purple]KAEDRA AUTONOMOUS LOOP[/bold purple]\n"
        "[cyan]BLADE + NYX Multi-Agent Execution[/cyan]",
        border_style="purple"
    ))
    
    log("Agent loop started")
    
    loop_count = 0
    current_agent = "BLADE"
    
    while loop_count < MAX_LOOPS:
        loop_count += 1
        
        console.print(f"\n[bold purple]{'═' * 50}[/bold purple]")
        console.print(f"[bold]Loop {loop_count} | Agent: {current_agent}[/bold]")
        console.print(f"[bold purple]{'═' * 50}[/bold purple]")
        
        # Get next task
        task = get_next_task(current_agent)
        
        if task:
            log(f"[{current_agent}] Executing: {task[:50]}...")
            
            if current_agent == "BLADE":
                console.print(f"[cyan][BLADE][/cyan] {task}")
                result = run_blade(task)
            else:
                console.print(f"[magenta][NYX][/magenta] {task}")
                result = run_nyx(task)
            
            console.print(f"[dim]{result[:200]}...[/dim]" if len(result) > 200 else f"[dim]{result}[/dim]")
            log(f"[{current_agent}] Complete: {result[:100]}")
        else:
            log(f"[{current_agent}] No unclaimed tasks")
            console.print(f"[yellow]No unclaimed tasks for {current_agent}[/yellow]")
        
        # Check exit
        if check_exit_signal():
            console.print("[green]EXIT_SIGNAL detected. Stopping.[/green]")
            break
        
        # Alternate agents
        current_agent = "NYX" if current_agent == "BLADE" else "BLADE"
        
        # Delay
        console.print(f"[dim]Waiting {LOOP_DELAY}s...[/dim]")
        time.sleep(LOOP_DELAY)
    
    console.print(Panel.fit(
        f"[bold green]Loop Complete[/bold green]\n"
        f"Total iterations: {loop_count}",
        border_style="green"
    ))
    log(f"Agent loop complete. Iterations: {loop_count}")

if __name__ == "__main__":
    main()
PYTHON_SCRIPT

chmod +x "${WORKSPACE}/run_loop.py"
echo -e "${GREEN}[✓] Agent runner created${NC}"

# Create .agent directory with protocol
mkdir -p "${WORKSPACE}/.agent"
cat > "${WORKSPACE}/.agent/AGENT_PROTOCOL.md" << 'PROTOCOL'
# Agent Protocol - Cloud Shell Instance

## Session Info
- **Started**: AUTO_TIMESTAMP
- **Project**: gen-lang-client-0939852539
- **Environment**: Cloud Shell

## Task Queue

### BLADE Tasks (Technical)
| ID | Task | Status |
|----|------|--------|
| B1 | Implement Chat screen with message bubbles | [x] |
| B2 | Add voice input button | [ ] |
| B3 | Add TTS playback toggle | [ ] |

### NYX Tasks (Creative)
| ID | Task | Status |
|----|------|--------|
| N1 | Design chat UI patterns | [ ] |
| N2 | Create emotion visualization | [ ] |

## Exit Signal
EXIT_SIGNAL: false
PROTOCOL

# Replace timestamp
sed -i "s/AUTO_TIMESTAMP/$(date -Iseconds)/" "${WORKSPACE}/.agent/AGENT_PROTOCOL.md"

# Final message
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  KAEDRA Cloud Shell Setup Complete!                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "To start the autonomous agent loop:"
echo -e "  ${CYAN}cd ~/kaedra && source .venv/bin/activate${NC}"
echo -e "  ${CYAN}python run_loop.py${NC}"
echo ""
echo -e "Or run with the shell script:"
echo -e "  ${CYAN}./scripts/run_agents.sh run${NC}"
echo ""
