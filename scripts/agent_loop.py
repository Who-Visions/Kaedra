#!/usr/bin/env python3
"""
KAEDRA Autonomous Agent Loop v2.0
Ralph-inspired multi-agent execution system

Features:
- Alternates between BLADE and NYX agents
- Task queue management via AGENT_PROTOCOL.md
- Circuit breaker for stagnation detection
- Session continuity with logging
- Exit signal handling
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.spinner import Spinner
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs): print(*args)
        def log(self, *args, **kwargs): print(*args)

console = Console()

# ============================================================================
# Configuration
# ============================================================================

class Config:
    PROJECT_ID = "gen-lang-client-0939852539"
    MAX_LOOPS = 50
    LOOP_DELAY = 10  # seconds
    STAGNATION_THRESHOLD = 3  # loops without progress
    
    BASE_DIR = Path(__file__).parent.parent
    AGENT_DIR = BASE_DIR / ".agent"
    PROTOCOL_FILE = AGENT_DIR / "AGENT_PROTOCOL.md"
    LOG_FILE = AGENT_DIR / "agent_loop.log"
    SESSION_FILE = AGENT_DIR / "session.json"

# ============================================================================
# Logging
# ============================================================================

def log(msg: str, level: str = "INFO"):
    """Log to file and console"""
    Config.AGENT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    
    with open(Config.LOG_FILE, "a") as f:
        f.write(log_line + "\n")
    
    color = {"INFO": "white", "BLADE": "cyan", "NYX": "magenta", 
             "ERROR": "red", "SUCCESS": "green"}.get(level, "white")
    if RICH_AVAILABLE:
        console.print(f"[{color}]{log_line}[/{color}]")
    else:
        print(log_line)

# ============================================================================
# Session Management
# ============================================================================

class Session:
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> dict:
        if Config.SESSION_FILE.exists():
            try:
                return json.loads(Config.SESSION_FILE.read_text())
            except:
                pass
        return {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started": datetime.now().isoformat(),
            "loop_count": 0,
            "blade_runs": 0,
            "nyx_runs": 0,
            "tasks_completed": 0,
            "last_agent": None,
            "stagnation_count": 0
        }
    
    def save(self):
        Config.AGENT_DIR.mkdir(exist_ok=True)
        Config.SESSION_FILE.write_text(json.dumps(self.data, indent=2))
    
    def increment_loop(self, agent: str, completed: bool):
        self.data["loop_count"] += 1
        self.data["last_agent"] = agent
        if agent == "BLADE":
            self.data["blade_runs"] += 1
        else:
            self.data["nyx_runs"] += 1
        if completed:
            self.data["tasks_completed"] += 1
            self.data["stagnation_count"] = 0
        else:
            self.data["stagnation_count"] += 1
        self.save()

# ============================================================================
# Agent Runners
# ============================================================================

def run_blade(task: str) -> Tuple[bool, str]:
    """Execute Blade agent on technical task"""
    log(f"Executing: {task[:60]}...", "BLADE")
    try:
        from kaedra.agents.blade import BladeAgent
        agent = BladeAgent()
        result = agent.query(task)
        response = result.response if hasattr(result, 'response') else str(result)
        log(f"Complete: {response[:100]}...", "BLADE")
        return True, response
    except ImportError:
        # Fallback to Kaedra agent
        try:
            from kaedra.agents.kaedra import KaedraAgent
            agent = KaedraAgent()
            result = agent.run_sync(f"[BLADE MODE] {task}")
            response = result.response if hasattr(result, 'response') else str(result)
            return True, response
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            return False, str(e)
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return False, str(e)

def run_nyx(task: str) -> Tuple[bool, str]:
    """Execute Nyx agent on creative/research task"""
    log(f"Executing: {task[:60]}...", "NYX")
    try:
        from kaedra.agents.nyx import NyxAgent
        agent = NyxAgent()
        result = agent.query(task)
        response = result.response if hasattr(result, 'response') else str(result)
        log(f"Complete: {response[:100]}...", "NYX")
        return True, response
    except ImportError:
        # Fallback to Kaedra agent
        try:
            from kaedra.agents.kaedra import KaedraAgent
            agent = KaedraAgent()
            result = agent.run_sync(f"[NYX MODE - Creative] {task}")
            response = result.response if hasattr(result, 'response') else str(result)
            return True, response
        except Exception as e:
            log(f"Error: {e}", "ERROR")
            return False, str(e)
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        return False, str(e)

# ============================================================================
# Protocol Management
# ============================================================================

def get_next_task(agent: str) -> Optional[str]:
    """Get next unclaimed task for agent"""
    if not Config.PROTOCOL_FILE.exists():
        return None
    
    content = Config.PROTOCOL_FILE.read_text()
    prefix = "B" if agent == "BLADE" else "N"
    
    for line in content.split("\n"):
        # Look for task rows with unclaimed status
        if f"| {prefix}" in line and "| [ ] |" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                return parts[2]  # Task description
    return None

def mark_task_in_progress(agent: str, task: str):
    """Mark task as in progress [/]"""
    if not Config.PROTOCOL_FILE.exists():
        return
    
    content = Config.PROTOCOL_FILE.read_text()
    # Find and replace the task status
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if task[:30] in line and "[ ]" in line:
            lines[i] = line.replace("[ ]", "[/]")
            break
    Config.PROTOCOL_FILE.write_text("\n".join(lines))

def mark_task_complete(agent: str, task: str):
    """Mark task as complete [x]"""
    if not Config.PROTOCOL_FILE.exists():
        return
    
    content = Config.PROTOCOL_FILE.read_text()
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if task[:30] in line and "[/]" in line:
            lines[i] = line.replace("[/]", "[x]")
            break
    Config.PROTOCOL_FILE.write_text("\n".join(lines))

def check_exit_signal() -> bool:
    """Check if exit signal is set"""
    if Config.PROTOCOL_FILE.exists():
        return "EXIT_SIGNAL: true" in Config.PROTOCOL_FILE.read_text()
    return False

def check_circuit_breaker(session: Session) -> bool:
    """Check if we should stop due to stagnation"""
    return session.data["stagnation_count"] >= Config.STAGNATION_THRESHOLD

# ============================================================================
# Main Loop
# ============================================================================

def run_loop():
    """Main autonomous loop"""
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold purple]KAEDRA AUTONOMOUS LOOP v2.0[/bold purple]\n"
            "[cyan]BLADE + NYX Multi-Agent Execution[/cyan]\n"
            f"[dim]Project: {Config.PROJECT_ID}[/dim]",
            border_style="purple"
        ))
    else:
        print("=" * 50)
        print("KAEDRA AUTONOMOUS LOOP v2.0")
        print("BLADE + NYX Multi-Agent Execution")
        print("=" * 50)
    
    session = Session()
    log("Agent loop started", "INFO")
    
    current_agent = "BLADE"
    
    while session.data["loop_count"] < Config.MAX_LOOPS:
        # Header
        console.print(f"\n[bold purple]{'═' * 50}[/bold purple]")
        console.print(f"[bold]Loop {session.data['loop_count'] + 1} | Agent: {current_agent}[/bold]")
        console.print(f"[bold purple]{'═' * 50}[/bold purple]")
        
        # Get task
        task = get_next_task(current_agent)
        
        if task:
            mark_task_in_progress(current_agent, task)
            
            if current_agent == "BLADE":
                success, result = run_blade(task)
            else:
                success, result = run_nyx(task)
            
            if success:
                mark_task_complete(current_agent, task)
            
            session.increment_loop(current_agent, success)
        else:
            console.print(f"[yellow]No unclaimed tasks for {current_agent}[/yellow]")
            session.increment_loop(current_agent, False)
        
        # Check exit conditions
        if check_exit_signal():
            log("EXIT_SIGNAL detected", "SUCCESS")
            break
        
        if check_circuit_breaker(session):
            log(f"Circuit breaker: {Config.STAGNATION_THRESHOLD} loops without progress", "ERROR")
            break
        
        # Alternate agents
        current_agent = "NYX" if current_agent == "BLADE" else "BLADE"
        
        # Delay
        console.print(f"[dim]Waiting {Config.LOOP_DELAY}s...[/dim]")
        time.sleep(Config.LOOP_DELAY)
    
    # Summary
    if RICH_AVAILABLE:
        table = Table(title="Session Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Loops", str(session.data["loop_count"]))
        table.add_row("BLADE Runs", str(session.data["blade_runs"]))
        table.add_row("NYX Runs", str(session.data["nyx_runs"]))
        table.add_row("Tasks Completed", str(session.data["tasks_completed"]))
        console.print(table)
    
    log(f"Loop complete. Tasks: {session.data['tasks_completed']}", "SUCCESS")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="KAEDRA Agent Loop")
    parser.add_argument("command", nargs="?", default="run",
                        choices=["run", "status", "reset", "logs"])
    parser.add_argument("--max-loops", type=int, default=50)
    parser.add_argument("--delay", type=int, default=10)
    args = parser.parse_args()
    
    Config.MAX_LOOPS = args.max_loops
    Config.LOOP_DELAY = args.delay
    
    if args.command == "run":
        run_loop()
    elif args.command == "status":
        if Config.SESSION_FILE.exists():
            console.print(Config.SESSION_FILE.read_text())
        else:
            console.print("No active session")
    elif args.command == "logs":
        if Config.LOG_FILE.exists():
            console.print(Config.LOG_FILE.read_text()[-5000:])
        else:
            console.print("No logs")
    elif args.command == "reset":
        for f in [Config.SESSION_FILE, Config.LOG_FILE]:
            if f.exists():
                f.unlink()
        console.print("[green]Session reset[/green]")

if __name__ == "__main__":
    main()
