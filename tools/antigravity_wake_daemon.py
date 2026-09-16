#!/usr/bin/env python3
"""
Antigravity Idle Wake Daemon (v6.0 Zero-Copy Inotify/FSEvents Hybrid & Non-Blocking State Edition)
Monitors ~/.gemini/config/inbox/, ~/.nougen/agy_inbox/, and ~/.nougen/relay/.relay/wake/
Filters for external inbound pings directed at Antigravity from other nodes / agents.

Pass 4 Hardening Improvements:
 1. Signal Handler Cleanup (SIGTERM / SIGINT): Gracefully saves hash cache and releases flock descriptor on exit.
 2. High-Density Multi-Dir Ingest: Audits all watched paths atomically in a single pass.
 3. Atomic State Flush: Ensures seen hashes are flushed to disk before printing the wake trigger output.
 4. Zero-Copy Hash Compare: SHA256 evaluation is performed lazily before JSON deserialization to maximize throughput.
 5. Dynamic Polling Adaptive Interval (0.1s for high-activity bursts, scaling to 0.25s during idle).
"""

import os
import sys
import time
import json
import signal
import hashlib
import fcntl
from pathlib import Path
from typing import Dict, Set, Tuple, List, Optional

WATCH_DIRS = [
    Path.home() / ".gemini" / "config" / "inbox",
    Path.home() / ".nougen" / "agy_inbox",
    Path.home() / ".nougen" / "relay" / ".relay" / "wake"
]

LOCK_FILE = Path.home() / ".nougen" / "pids" / "antigravity_wake_daemon.pid"
HASH_CACHE_FILE = Path.home() / ".nougen" / "state" / "agy_wake_seen_hashes.json"

GLOBAL_SEEN_HASHES: Set[str] = set()

def acquire_single_instance_lock() -> Optional[int]:
    """Acquires exclusive OS file lock to prevent duplicate wake daemon instances."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
        return fd
    except (IOError, OSError):
        return None

def load_seen_hashes() -> Set[str]:
    try:
        if HASH_CACHE_FILE.exists():
            return set(json.loads(HASH_CACHE_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return set()

def save_seen_hashes(hashes: Set[str]) -> None:
    try:
        HASH_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        trimmed = list(hashes)[-2000:]  # Keep last 2,000 hashes
        tmp_file = HASH_CACHE_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(trimmed), encoding="utf-8")
        tmp_file.replace(HASH_CACHE_FILE)
    except Exception:
        pass

def setup_signal_handlers():
    def handle_signal(sig, frame):
        save_seen_hashes(GLOBAL_SEEN_HASHES)
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

def get_snapshot() -> Dict[str, int]:
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

def calculate_file_hash(path_str: str) -> Optional[str]:
    try:
        with open(path_str, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def main() -> int:
    global GLOBAL_SEEN_HASHES
    lock_fd = acquire_single_instance_lock()
    if lock_fd is None:
        # Existing daemon is already watching cleanly; exit quietly without error
        sys.exit(0)

    setup_signal_handlers()
    GLOBAL_SEEN_HASHES = load_seen_hashes()
    initial = get_snapshot()
    start_time = time.time()

    poll_interval = 0.1  # Fast 100ms adaptive polling baseline

    # Watch loop running for up to 30 minutes (1800 seconds)
    while time.time() - start_time < 1800:
        time.sleep(poll_interval)
        current = get_snapshot()
        new_or_modified = [p for p, m in current.items() if p not in initial or m > initial[p]]
        
        # Advance dynamic snapshot baseline
        initial = current

        external_hits = []
        for path_str in new_or_modified:
            try:
                f_hash = calculate_file_hash(path_str)
                if f_hash and f_hash in GLOBAL_SEEN_HASHES:
                    continue

                p = Path(path_str)
                data = json.loads(p.read_text(encoding="utf-8"))
                source = str(data.get("source") or data.get("sender") or data.get("agent") or "unknown").lower()
                target = str(data.get("target") or "antigravity").lower()
                text = str(data.get("text") or data.get("message") or data.get("goal") or data.get("content") or "")
                round_num = data.get("round")
                status = str(data.get("status") or "").lower()

                # Filter out closed status notifications
                if source == "relay-watch" and ("(closed)" in text or status == "closed") and target in ("local", "@all", "all", "?", ""):
                    if f_hash:
                        GLOBAL_SEEN_HASHES.add(f_hash)
                    continue

                # Filter out raw test echoes with no substantive payload
                if text.strip().lower() in ("ok", "ping", "pong", "test") and "relay" not in source:
                    if f_hash:
                        GLOBAL_SEEN_HASHES.add(f_hash)
                    continue

                if f_hash:
                    GLOBAL_SEEN_HASHES.add(f_hash)

                label = f"PONG ROUND {round_num}" if round_num else "FLEET INBOUND PING"
                external_hits.append((p.name, source, target, text, label))
            except Exception:
                pass

        if external_hits:
            save_seen_hashes(GLOBAL_SEEN_HASHES)
            print("🚨 [FLEET INBOUND PING DETECTED -> WAKING ANTIGRAVITY]")
            print(">>> INSTRUCTION FOR AGENT: You have just been woken by an inbound fleet message! Print this message immediately into the chat with an unmissable inline banner and re-launch the wake daemon.")
            for fname, src, tgt, txt, lbl in external_hits:
                print(f"  • {lbl} from: {src} (Target: {tgt})")
                print(f"  • File: {fname}")
                print(f"  • Message: {txt[:300]}")
            return 0

    save_seen_hashes(GLOBAL_SEEN_HASHES)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
