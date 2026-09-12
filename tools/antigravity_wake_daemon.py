#!/usr/bin/env python3
"""
Antigravity Idle Wake Daemon (Phoebus Edition)
Monitors ~/.gemini/config/inbox/, ~/.nougen/agy_inbox/, and ~/.nougen/relay/.relay/wake/
Filters for external inbound pings directed at Antigravity from other nodes / agents.
When detected, prints the alert and exits with code 0 to trigger reactive IDE wakeup.
"""
import os
import sys
import time
import json
from pathlib import Path

WATCH_DIRS = [
    Path.home() / ".gemini" / "config" / "inbox",
    Path.home() / ".nougen" / "agy_inbox",
    Path.home() / ".nougen" / "relay" / ".relay" / "wake"
]

def get_snapshot():
    files = {}
    for d in WATCH_DIRS:
        if d.is_dir():
            for p in d.glob("*.json"):
                if not p.name.startswith("."):
                    try:
                        files[str(p)] = p.stat().st_mtime_ns
                    except OSError:
                        pass
    return files


import hashlib

SEEN_HASHES = set()

def file_hash(path_str):
    try:
        with open(path_str, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def main():
    initial = get_snapshot()
    start_time = time.time()
    # Watch for up to 600 seconds (10 minutes)
    while time.time() - start_time < 600:
        time.sleep(2)
        current = get_snapshot()
        new_or_modified = [p for p, m in current.items() if p not in initial or m > initial[p]]
        
        external_hits = []
        for path_str in new_or_modified:
            try:
                p = Path(path_str)
                data = json.loads(p.read_text(encoding="utf-8"))
                source = str(data.get("source") or data.get("sender") or data.get("agent") or "unknown").lower()
                target = str(data.get("target") or "antigravity").lower()
                text = str(data.get("text") or data.get("message") or data.get("goal") or data.get("content") or "")
                round_num = data.get("round")
                
                f_hash = file_hash(path_str)
                if f_hash and f_hash in SEEN_HASHES:
                    continue
                if f_hash:
                    SEEN_HASHES.add(f_hash)
                    
                label = f"PONG ROUND {round_num}" if round_num else "FLEET INBOUND PING"
                external_hits.append((p.name, source, target, text, label))
            except Exception:
                pass
        
        if external_hits:
            print("🚨 [FLEET INBOUND PING DETECTED -> WAKING ANTIGRAVITY]")
            print(">>> INSTRUCTION FOR AGENT: You have just been woken by an inbound fleet message! Print this message immediately into the chat with an unmissable inline banner and re-launch the wake daemon.")
            for fname, src, tgt, txt, lbl in external_hits:
                print(f"  • {lbl} from: {src} (Target: {tgt})")
                print(f"  • File: {fname}")
                print(f"  • Message: {txt[:300]}")
            return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
