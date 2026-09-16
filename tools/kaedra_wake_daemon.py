#!/usr/bin/env python3
"""
Kaedra Idle Wake Daemon (Shadow Dweller Edition)
Monitors ~/.nougen/kaedra_inbox/ for incoming pings and relays directed at Kaedra.
Filters for external inbound pings and dispatches them through Kaedra's local pipeline.
"""
import os
import sys
import time
import json
from pathlib import Path

WATCH_DIR = Path.home() / ".nougen" / "kaedra_inbox"

def get_snapshot():
    files = {}
    if WATCH_DIR.is_dir():
        for p in WATCH_DIR.glob("*.json"):
            if not p.name.startswith("."):
                try:
                    files[str(p)] = p.stat().st_mtime_ns
                except OSError:
                    pass
    return files

def main():
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
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
                source = str(data.get("source") or data.get("sender") or "").lower()
                target = str(data.get("target") or "").lower()
                text = str(data.get("text") or data.get("goal") or "")
                
                external_hits.append((p.name, source, target, text))
            except Exception:
                pass
        
        if external_hits:
            print("🌑 [KAEDRA FLEET INBOUND DETECTED -> SHADOW TACTICIAN WAKE]")
            for fname, src, tgt, txt in external_hits:
                print(f"  • Inbound Ping from: {src} (Target: {tgt})")
                print(f"  • File: {fname}")
                print(f"  • Directive: {txt[:300]}")
            return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
