"""
StoryEngine Engine Mode Tools
Control engine state and emotions.
"""


def set_engine_mode(mode: str) -> str:
    """Switch StoryEngine mode. Valid: normal, freeze, zoom, escalate, god, shift_pov, rewind, director."""
    return f"[MODE SWITCH] → {mode.upper()}"


def adjust_emotion(emotion: str, delta: float) -> str:
    """Adjust emotional vector. Emotions: fear, hope, desire, rage. Delta: -1.0 to 1.0."""
    return f"[EMOTION] {emotion} adjusted by {delta:+.2f}"
