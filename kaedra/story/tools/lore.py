"""
StoryEngine Lore Tools
Read local lore files and propose canon updates.
"""
import json
from pathlib import Path
from datetime import datetime

from ..ui import console


def read_local_lore(filename: str) -> str:
    """Read content from local lore files (e.g., mars_secrets.md)."""
    try:
        # Sanitize path
        safe_name = Path(filename).name
        path = Path("lore") / safe_name
        if not path.exists():
            return f"[File not found: {safe_name}]"
        console.print(f"[dim]>> [LORE] Reading: '{safe_name}'...[/]")
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[Error reading lore: {e}]"


def propose_canon_update(claim: str, confidence: float, source: str) -> str:
    """Propose a factual update to the canon (delta)."""
    entry = {
        "claim": claim,
        "confidence": confidence,
        "source_scene": source,
        "requires_review": True,
        "timestamp": datetime.now().isoformat()
    }
    delta_file = Path("lore/canon_delta.json")
    try:
        if not delta_file.exists():
            data = []
        else:
            data = json.loads(delta_file.read_text(encoding="utf-8"))
    except: 
        data = []
    
    data.append(entry)
    delta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"[CANON DELTA] Note logged: {claim[:50]}..."
