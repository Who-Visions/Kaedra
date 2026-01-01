"""
StoryEngine Timeline Tools
Clean and validate timeline data.
"""
import json
from collections import defaultdict


def clean_event_text(s: str) -> str:
    return " ".join(str(s).split())  # collapses newlines and extra whitespace


def event_sort_key(e: dict):
    return (e.get("year", 0), e.get("month", 0), e.get("day", 0))


def normalize_timeline(events: list) -> list:
    """Clean, sort, and merge timeline events."""
    if not isinstance(events, list): 
        return []
    by_date = defaultdict(list)
    for e in events:
        if not isinstance(e, dict): 
            continue
        e = dict(e)
        if "event" in e:
            e["event"] = clean_event_text(e["event"])
        by_date[event_sort_key(e)].append(e)

    out = []
    for key in sorted(by_date.keys()):
        group = by_date[key]
        if len(group) == 1:
            out.append(group[0])
            continue

        # merge duplicates
        merged = {}
        for g in group:
            merged.update({k: v for k, v in g.items() if k not in ("event", "notes", "event_detail_note")})
        events_text = [g.get("event") for g in group if g.get("event")]
        notes_text  = [g.get("notes") or g.get("event_detail_note") for g in group if (g.get("notes") or g.get("event_detail_note"))]

        if events_text:
            merged["event"] = " | ".join(events_text)
        if notes_text:
            merged["notes"] = " | ".join(notes_text)

        out.append(merged)
    return out


def clean_timeline_data(data: list) -> str:
    """Validator/Sorter for timeline JSON data. Returns cleaned JSON string."""
    try:
        cleaned = normalize_timeline(data)
        return json.dumps(cleaned, indent=2)
    except Exception as e:
        return f"[Error cleaning timeline: {e}]"
