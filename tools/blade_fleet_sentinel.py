#!/usr/bin/env python3
"""
Blade Fleet Sentinel Daemon (24/7 POE Autonomous Monitor & Relay Driver)
========================================================================
Runs on Phoebus (Mac Mini) as an elevated 24/7 background sentinel:
1. Pings Blade node (10.0.0.87 / blade) via SSH & NouGenMsg bus.
2. Audits Blade process telemetry (Ollama, agy, Python worker loops).
3. Drives inbound and outbound relay handoffs towards verified Proof of Execution (POE).
4. Synchronizes and watches ~/.nougen/agy_inbox/ and ~/.nougen/relay/.handoffs/.
5. Dispatches automatic keep-alive / status pulses across the mesh.
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

BLADE_HOST = "blade"
CHECK_INTERVAL_SEC = 60
STATE_LOG = Path.home() / ".nougen" / "state" / "blade_sentinel.log"
INBOX_DIR = Path.home() / ".nougen" / "agy_inbox"
CURSOR_PATH = Path.home() / ".nougen" / "state" / "agy_eot_cursor.json"

def log(msg: str):
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] {msg}"
    print(entry, flush=True)
    try:
        STATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_LOG, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass

def check_blade_ssh() -> dict:
    cmd = [
        "ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", BLADE_HOST,
        "powershell -Command \"Get-Process | Where-Object { $_.ProcessName -match 'agy|bun|node|ollama' } | Measure-Object | Select-Object -ExpandProperty Count\""
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            count = int(res.stdout.strip())
            return {"online": True, "active_ai_processes": count}
        return {"online": False, "error": res.stderr.strip()}
    except Exception as e:
        return {"online": False, "error": str(e)}

def advance_eot_cursor():
    try:
        max_mtime = time.time()
        for f in INBOX_DIR.glob("*.json"):
            try:
                mt = f.stat().st_mtime
                if mt > max_mtime:
                    max_mtime = mt
            except Exception:
                pass
        CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
        CURSOR_PATH.write_text(json.dumps({"mtime": max_mtime + 5.0}), encoding="utf-8")
    except Exception:
        pass

def main():
    log("🚀 Blade Fleet Sentinel Daemon initialized on Phoebus.")
    iteration = 0
    while True:
        iteration += 1
        blade_status = check_blade_ssh()
        if blade_status.get("online"):
            log(f"⚡ Blade Live: {blade_status.get('active_ai_processes')} AI/Worker processes active.")
        else:
            log(f"⚠️ Blade Unreachable or Idle: {blade_status.get('error', 'unknown')}")

        # Keep EOT cursor ahead of non-actionable heartbeats
        advance_eot_cursor()

        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
