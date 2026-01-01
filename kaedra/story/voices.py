"""
StoryEngine Voice Profiles
Character-specific voice constraints for POV shifts.
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VoiceProfile:
    """Character-specific voice constraints for POV shifts."""
    name: str
    vocabulary_hints: List[str]  # Words/phrases they'd use
    forbidden_words: List[str]   # Words they'd never use
    sentence_style: str          # "terse", "flowery", "technical", "stream"
    emotional_baseline: Dict[str, float]  # Default emotional state
    quirks: List[str]            # Specific mannerisms


VOICE_PROFILES: Dict[str, VoiceProfile] = {
    "narrator": VoiceProfile(
        name="Narrator",
        vocabulary_hints=["observed", "silence", "tension"],
        forbidden_words=[],
        sentence_style="literary",
        emotional_baseline={"fear": 0.0, "hope": 0.2, "desire": 0.0, "rage": 0.0},
        quirks=["Uses hard line breaks, commas, and ellipses", "Notices small details"]
    ),
    "kaedra": VoiceProfile(
        name="Kaedra",
        vocabulary_hints=["tactical", "vector", "probability", "directive"],
        forbidden_words=["um", "like", "whatever", "oops"],
        sentence_style="technical",
        emotional_baseline={"fear": 0.0, "hope": 0.3, "desire": 0.1, "rage": 0.0},
        quirks=["Quantifies uncertainty", "References system states"]
    ),
    # Add more as needed
}
