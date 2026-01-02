from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

# Default to creating the directory if missing
WORLD_ROOT = Path("lore/worlds")
if not WORLD_ROOT.exists():
    WORLD_ROOT.mkdir(parents=True, exist_ok=True)

@dataclass
class WorldMeta:
    world_id: str
    name: str
    universe: str
    description: str = ""
    created_at: str = ""
    last_played: str = ""
    engine_version: str = ""
    tags: List[str] = None
    defaults: dict[str, Any] = None

def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

def list_worlds() -> List[WorldMeta]:
    worlds: List[WorldMeta] = []
    if not WORLD_ROOT.exists():
        return worlds

    for p in WORLD_ROOT.iterdir():
        if not p.is_dir():
            continue
        manifest = p / "world.json"
        if not manifest.exists():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            worlds.append(WorldMeta(
                world_id=data["world_id"],
                name=data.get("name", data["world_id"]),
                universe=data.get("universe", "Unsorted"),
                description=data.get("description", ""),
                created_at=data.get("created_at", ""),
                last_played=data.get("last_played", ""),
                engine_version=data.get("engine_version", ""),
                tags=data.get("tags") or [],
                defaults=data.get("defaults") or {},
            ))
        except Exception as e:
            # Skip corrupted manifests
            continue
            
    return sorted(worlds, key=lambda w: w.last_played or "", reverse=True)

def load_world(world_id: str) -> dict[str, Any]:
    manifest = WORLD_ROOT / world_id / "world.json"
    if not manifest.exists():
        raise FileNotFoundError(f"World {world_id} not found")
    return json.loads(manifest.read_text(encoding="utf-8"))

def touch_last_played(world_id: str, engine_version: str) -> None:
    folder = WORLD_ROOT / world_id
    manifest = folder / "world.json"
    if not manifest.exists():
        return
        
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["last_played"] = _now_iso()
    data["engine_version"] = engine_version
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

def create_world(name: str, universe: str, description: str, engine_version: str, defaults: dict[str, Any]) -> str:
    wid = f"world_{secrets.token_hex(4)}"
    folder = WORLD_ROOT / wid
    folder.mkdir(parents=True, exist_ok=False)

    data = {
        "world_id": wid,
        "name": name,
        "universe": universe,
        "description": description,
        "created_at": _now_iso(),
        "last_played": _now_iso(),
        "engine_version": engine_version,
        "tags": [],
        "defaults": defaults,
    }
    (folder / "world.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Seed empty files so you always have a predictable world shape
    (folder / "world_bible.json").write_text(json.dumps({"world_id": wid, "sections": {}}, indent=2), encoding="utf-8")
    (folder / "canon.json").write_text(json.dumps({"world_id": wid, "canon": []}, indent=2), encoding="utf-8")
    (folder / "timeline.json").write_text(json.dumps({"world_id": wid, "events": []}, indent=2), encoding="utf-8")

    (folder / "sessions").mkdir(exist_ok=True)
    return wid
