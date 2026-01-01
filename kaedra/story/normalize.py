"""
StoryEngine Normalization Helpers
Utilities for normalizing history turns and text.
"""
import re
import hashlib
import json
from typing import Any, Dict


def to_text(x: Any) -> str:
    """Normalize anything into a safe string for logs, JSON, or signatures."""
    if x is None:
        return ""
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    if isinstance(x, str):
        return x
    try:
        return str(x)
    except Exception:
        return ""


def tool_sig(name: str, payload: dict) -> str:
    """Compute signature for tool calls."""
    try:
        raw = json.dumps({"name": name, "payload": payload}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    except Exception:
        return ""


def normalize_turn(t: Any) -> Dict:
    """Ensure a history turn is in the normalized format (Internal dict schema)."""
    # 1. Capture raw role
    if isinstance(t, dict):
        raw_role = t.get("role", "user")
    else:
        raw_role = getattr(t, "role", "user")
        
    # 2. Map role
    role_map = {
        "assistant": "model",
        "model": "model",
        "user": "user",
        "system": "user", 
    }
    role = role_map.get(str(raw_role).lower(), "user")
    
    # 3. Capture and normalize parts
    if isinstance(t, dict):
        parts_in = t.get("parts", [])
        if not parts_in:
             # Handle legacy single-string turns
             text = t.get("content") or t.get("text") or ""
             parts_in = [{"text": str(text)}] if text else []
    else:
        parts_in = getattr(t, "parts", [])

    parts_out = []
    for p in parts_in:
        # Capture thought_signature if present
        sig = None
        if hasattr(p, "thought_signature") and p.thought_signature:
            sig = p.thought_signature
        elif isinstance(p, dict) and p.get("thought_signature"):
            sig = p["thought_signature"]

        part_dict = {}
        # Text
        if hasattr(p, "text") and p.text:
            part_dict["text"] = str(p.text)
        elif isinstance(p, dict) and p.get("text"):
            part_dict["text"] = str(p["text"])
        # Function Call
        elif hasattr(p, "function_call") and p.function_call:
            fc = p.function_call
            part_dict["function_call"] = {"name": fc.name, "args": dict(fc.args or {})}
        elif isinstance(p, dict) and p.get("function_call"):
            part_dict["function_call"] = p["function_call"]
        # Function Response
        elif hasattr(p, "function_response") and p.function_response:
            fr = p.function_response
            part_dict["function_response"] = {"name": fr.name, "response": fr.response}
        elif isinstance(p, dict) and p.get("function_response"):
            part_dict["function_response"] = p["function_response"]

        # Attach signature if present (CRITICAL for tool calls)
        if sig:
            part_dict["thought_signature"] = sig

        if part_dict:
            parts_out.append(part_dict)
            
    # 4. Return unified dict
    return {"role": role, "parts": parts_out}


def normalize_text(s: str) -> str:
    """Normalize whitespace and newlines for clean ingest."""
    if not s:
        return ""
    # Collapse multiple spaces/newlines
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s


def clean_event_text(s: str) -> str:
    return normalize_text(s)


def event_sort_key(e: dict):
    return (e.get("year") or 9999, e.get("month") or 99, e.get("day") or 99)


def normalize_timeline(events: list) -> list:
    """Clean, sort, and merge timeline events."""
    if not events:
        return []
    
    cleaned = []
    for e in events:
        if not isinstance(e, dict):
            continue
        c = {
            "year": e.get("year"),
            "month": e.get("month"),
            "day": e.get("day"),
            "event": clean_event_text(e.get("event", "")),
            "source": e.get("source", "unknown"),
            "confidence": e.get("confidence", 0.5),
        }
        # Skip empty events
        if not c["event"]:
            continue
        cleaned.append(c)
    
    # Sort by date
    cleaned.sort(key=event_sort_key)
    
    # Merge exact duplicates
    seen = set()
    merged = []
    for e in cleaned:
        sig = (e["year"], e["month"], e["day"], e["event"][:100])
        if sig not in seen:
            seen.add(sig)
            merged.append(e)
    
    return merged
