"""
StoryEngine Configuration
Dataclasses, enums, and constants for the narrative engine.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any

# === ENGINE RESPONSE ===
@dataclass
class EngineResponse:
    """Standardized narrative output packet."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

# === MODE ENUM ===
class Mode(Enum):
    NORMAL = "normal"
    FREEZE = "freeze"
    ZOOM = "zoom"
    ESCALATE = "escalate"
    GOD = "god"
    SHIFT_POV = "shift_pov"
    REWIND = "rewind"
    DIRECTOR = "director"

# === MODEL CONSTANTS ===
FLASH_MODEL = "gemini-3-flash-preview"
PRO_MODEL = "gemini-3-pro-preview"

# === EMOTION PHYSICS ===
@dataclass
class EmotionConfig:
    """Physics parameters for emotional dynamics."""
    decay_rate: float = 0.05        # Per-turn decay toward neutral
    momentum_factor: float = 0.3    # How much current emotion influences next
    bleed_rate: float = 0.1         # Cross-emotion contamination (rage→fear)
    ceiling: float = 1.0
    floor: float = 0.0
    
    # Emotion interactions (source → target, multiplier)
    bleed_matrix: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "rage": {"fear": 0.15, "hope": -0.1},
        "fear": {"rage": 0.1, "hope": -0.2},
        "hope": {"fear": -0.15, "desire": 0.1},
        "desire": {"rage": 0.05, "hope": 0.1},
    })

# === RATE LIMITING ===
@dataclass
class RateLimitConfig:
    min_interval_s: float = 0.35   # global pacing
    max_retries: int = 5
