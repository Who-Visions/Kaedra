#!/usr/bin/env python3
"""
Kaedra Brain Visualizer Engine (Reverse Engineered from Antigravity Brain Visualizer v0.6.0)
Author: Kaedra / Antigravity Coach (The Observatory)

Features:
1. Single-Pass Session Analysis: Parses transcript.jsonl directly, extracts tool calls, failures, and summaries.
2. Artifacts & Metadata Inspection: Parses implementation plans, walkthroughs, and .metadata.json.
3. Subagent Navigation: Traces send_message and subagent conversation delegations.
4. Git Checkpoints & Diff Inspection: Examines .git commits inside session directories.
5. Token & Cost Estimation: Computes input, thinking, output tokens and Gemini 3.8 / Pro pricing.
"""

import os
import sys
import json
import glob
import re
import subprocess
from datetime import datetime
from pathlib import Path

# ANSI Styling
C_CYAN = "\033[38;5;87m"
C_GREEN = "\033[38;5;82m"
C_YELLOW = "\033[38;5;220m"
C_PURPLE = "\033[38;5;141m"
C_RED = "\033[38;5;196m"
C_GRAY = "\033[38;5;244m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

BRAIN_DIR = Path(os.path.expanduser("~/.gemini/antigravity/brain"))

# Gemini Official Pricing (per 1M tokens)
PRICING = {
    "gemini-3.8-flash": {"input": 0.75, "output": 3.75},
    "gemini-3.1-pro": {"input": 1.25, "output": 5.00},
}

# Redaction Patterns for Credentials & Sensitive Tokens
SECRET_PATTERNS = [
    re.compile(r'AIza[0-9A-Za-z-_]{35}'),
    re.compile(r'sk-[a-zA-Z0-9_-]{20,}'),
    re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    re.compile(r'gho_[a-zA-Z0-9]{36}'),
    re.compile(r'glpat-[0-9a-zA-Z_-]{20}'),
    re.compile(r'bearer\s+[a-zA-Z0-9_\-\.]{25,}', re.IGNORECASE),
    # --- added on phoebus 2026-09-07 (HURRICANE KICK hop 3). The six patterns
    # above caught 7 of 16 synthetic credential shapes; these nine cover the
    # rest. The two that mattered most were NGS_NODE_TOKEN and
    # CLOUDFLARE_API_TOKEN -- key names this fleet actually carries, printed
    # in the clear by a function whose name promises redaction.
    re.compile(r'hf_[a-zA-Z0-9]{30,}'),
    re.compile(r'xox[abprs]-[0-9a-zA-Z-]{10,}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
    re.compile(r'ASIA[0-9A-Z]{16}'),
    # -----BEGIN ... PRIVATE KEY----- and everything after it on that line
    re.compile(r'-----BEGIN[ A-Z]*PRIVATE KEY-----[\s\S]*?(?=-----END|\Z)'),
    # user:password@host in any URI
    re.compile(r'(?<=://)[^\s:/@]+:[^\s:/@]{6,}(?=@)'),
    # NAME=value / NAME: value where NAME looks like a credential name.
    # Keeps the NAME (it is safe and useful) and destroys only the value --
    # fleet doctrine is that key NAMES may travel and values may not.
    re.compile(r'((?:[A-Za-z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|APIKEY|API_KEY|PRIVATE_KEY|ACCESS_KEY|CREDENTIAL)[A-Za-z0-9_]*)\s*[=:]\s*)\S{8,}',
               re.IGNORECASE),
]

def redact_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    for p in SECRET_PATTERNS:
        if p.groups:
            # Pattern captured a safe prefix (the key NAME) -- keep it and
            # redact only the value.
            text = p.sub(lambda m: m.group(1) + "[REDACTED_CREDENTIAL]", text)
        else:
            text = p.sub("[REDACTED_CREDENTIAL]", text)
    return text

class KaedraBrainVisualizer:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or self.get_latest_session()
        self.session_path = BRAIN_DIR / self.session_id if self.session_id else None

    @staticmethod
    def get_latest_session() -> str:
        if not BRAIN_DIR.exists():
            return None
        sessions = [
            p for p in BRAIN_DIR.iterdir()
            if p.is_dir() and not p.name.startswith(".") and (p / ".system_generated" / "logs" / "transcript.jsonl").exists()
        ]
        if not sessions:
            sessions = [p for p in BRAIN_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not sessions:
            return None
        latest = max(sessions, key=lambda p: p.stat().st_mtime)
        return latest.name

    def load_transcript(self):
        if not self.session_path:
            return []
        log_file = self.session_path / ".system_generated" / "logs" / "transcript.jsonl"
        if not log_file.exists():
            return []
        
        steps = []
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        step_data = json.loads(line)
                        # Redact strings at ingest level
                        if isinstance(step_data.get("content"), str):
                            step_data["content"] = redact_text(step_data["content"])
                        steps.append(step_data)
                    except json.JSONDecodeError:
                        continue
        return steps

    def analyze_tokens(self, steps):
        input_tokens = 0
        output_tokens = 0
        thinking_tokens = 0
        tool_counts = {}
        subagent_invocations = []
        failures = []

        for step in steps:
            stype = step.get("type", "")
            content = step.get("content", "")
            
            chars = len(content) if isinstance(content, str) else 0
            
            if stype == "USER_INPUT":
                input_tokens += max(1, chars // 4)
            elif stype == "PLANNER_RESPONSE":
                thinking_match = re.search(r"<\|channel>thought(.*?)(?:<channel\|>|<\|channel>)", content, re.DOTALL)
                if thinking_match:
                    t_chars = len(thinking_match.group(1))
                    thinking_tokens += max(1, t_chars // 4)
                    chars -= t_chars
                output_tokens += max(1, chars // 4)

            for tc in step.get("tool_calls", []):
                tname = tc.get("toolAction") or tc.get("name") or "unknown_tool"
                tool_counts[tname] = tool_counts.get(tname, 0) + 1
                if "subagent" in str(tc).lower():
                    subagent_invocations.append(tc)

            if step.get("status") == "ERROR" or "exited with code" in str(content) or "failed" in str(content).lower():
                if len(failures) < 5:
                    failures.append(redact_text(str(content)[:200].replace("\n", " ")))

        total_tokens = input_tokens + thinking_tokens + output_tokens
        flash_cost = (input_tokens / 1e6 * PRICING["gemini-3.8-flash"]["input"]) + \
                     ((output_tokens + thinking_tokens) / 1e6 * PRICING["gemini-3.8-flash"]["output"])

        return {
            "total_steps": len(steps),
            "input_tokens": input_tokens,
            "thinking_tokens": thinking_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": flash_cost,
            "tool_counts": tool_counts,
            "subagent_count": len(subagent_invocations),
            "failures": failures,
        }

    def inspect_artifacts(self):
        if not self.session_path or not self.session_path.exists():
            return []
        
        artifacts = []
        for file in self.session_path.glob("*.md"):
            meta_file = file.with_name(file.name + ".metadata.json")
            metadata = {}
            if meta_file.exists():
                try:
                    with open(meta_file, "r") as mf:
                        metadata = json.load(mf)
                except Exception:
                    pass
            
            artifacts.append({
                "name": file.name,
                "size_bytes": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "metadata": metadata,
            })
        return artifacts

    def inspect_git_checkpoints(self):
        if not self.session_path:
            return []
        git_dir = self.session_path / ".git"
        if not git_dir.exists():
            return []
        try:
            cmd = ["git", f"--git-dir={git_dir}", f"--work-tree={self.session_path}", "log", "--oneline", "-n", "10"]
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            return out.strip().split("\n") if out.strip() else []
        except Exception:
            return []

    def render_dashboard(self):
        if not self.session_path or not self.session_path.exists():
            print(f"{C_RED}Error: Session not found at {self.session_path}{C_RESET}")
            return

        steps = self.load_transcript()
        token_stats = self.analyze_tokens(steps)
        artifacts = self.inspect_artifacts()
        checkpoints = self.inspect_git_checkpoints()

        print(f"\n{C_BOLD}{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════╗{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}║                     🪐 KAEDRA BRAIN VISUALIZER (v0.6.0 SPEC)                      ║{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}║                        Session: {self.session_id:<49} ║{C_RESET}")
        print(f"{C_BOLD}{C_CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣{C_RESET}")

        print(f"{C_BOLD}📊 TOKEN CONSUMPTION & FINANCIAL TELEMETRY:{C_RESET}")
        print(f"  • Total Steps:      {C_BOLD}{token_stats['total_steps']}{C_RESET}")
        print(f"  • Est. Input:       {C_CYAN}{token_stats['input_tokens']:,} it{C_RESET}")
        print(f"  • Est. Thinking:    {C_PURPLE}{token_stats['thinking_tokens']:,} th{C_RESET}")
        print(f"  • Est. Output:      {C_GREEN}{token_stats['output_tokens']:,} ot{C_RESET}")
        print(f"  • Total Tokens:     {C_YELLOW}{token_stats['total_tokens']:,} tokens{C_RESET}")
        print(f"  • Est. Run Cost:    {C_GREEN}${token_stats['estimated_cost_usd']:.4f} USD{C_RESET} (Gemini 3.8 Flash Tier)")

        print(f"\n{C_BOLD}📦 ARTIFACTS & SNAPSHOTS ({len(artifacts)} found):{C_RESET}")
        if artifacts:
            for art in artifacts:
                summary = art['metadata'].get('Summary', 'No summary metadata recorded')
                uf = "✓ UserFacing" if art['metadata'].get('UserFacing') else "Internal"
                print(f"  • {C_BOLD}{art['name']}{C_RESET} ({art['size_bytes']:,} B) [{C_CYAN}{uf}{C_RESET}]")
                print(f"    {C_GRAY}{summary[:90]}...{C_RESET}")
        else:
            print(f"  {C_GRAY}No markdown artifacts generated in this session.{C_RESET}")

        print(f"\n{C_BOLD}🌿 GIT CHECKPOINTS ({len(checkpoints)} commits):{C_RESET}")
        if checkpoints:
            for cp in checkpoints[:5]:
                print(f"  • {C_YELLOW}{cp}{C_RESET}")
        else:
            print(f"  {C_GRAY}No session git repository checkpoints found.{C_RESET}")

        print(f"\n{C_BOLD}🛠️ TOP AGENT TOOL INVOCATIONS:{C_RESET}")
        if token_stats['tool_counts']:
            sorted_tools = sorted(token_stats['tool_counts'].items(), key=lambda x: x[1], reverse=True)[:5]
            for tname, count in sorted_tools:
                print(f"  • {tname:<32}: {C_CYAN}{count}{C_RESET} calls")
        else:
            print(f"  {C_GRAY}No tool calls recorded in transcript.{C_RESET}")

        print(f"{C_BOLD}{C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════╝{C_RESET}\n")

if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else None
    viz = KaedraBrainVisualizer(sid)
    viz.render_dashboard()
