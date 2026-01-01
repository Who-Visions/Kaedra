"""
StoryEngine Story Snapshot
Captures state for rewind functionality.
"""
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
import rich.repr

from .config import Mode


@rich.repr.auto
@dataclass
class StorySnapshot:
    scene: int
    pov: str
    mode: Mode
    tension: float
    emotion_state: Dict[str, Any]
    history_hash: str  # Hash of history state for integrity
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "mode": self.mode.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StorySnapshot':
        data["mode"] = Mode(data["mode"])
        return cls(**data)
