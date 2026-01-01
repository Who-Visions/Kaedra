"""
StoryEngine Emotion Physics
Manages emotional state with physics-based dynamics.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from collections import deque

from .config import EmotionConfig


class EmotionEngine:
    """Manages emotional state with physics-based dynamics."""
    
    def __init__(self, config: Optional[EmotionConfig] = None):
        self.config = config or EmotionConfig()
        self.state: Dict[str, float] = {
            "fear": 0.0, "hope": 0.0, "desire": 0.0, "rage": 0.0
        }
        self.momentum: Dict[str, float] = {k: 0.0 for k in self.state}
        self.history: deque = deque(maxlen=50)  # Track emotional trajectory
        
    def pulse(self, emotion: str, delta: float) -> None:
        """Apply an emotional impulse with momentum."""
        if emotion not in self.state:
            return
        
        # Apply with momentum amplification
        effective_delta = delta * (1 + abs(self.momentum[emotion]) * self.config.momentum_factor)
        self.state[emotion] = max(
            self.config.floor,
            min(self.config.ceiling, self.state[emotion] + effective_delta)
        )
        
        # Update momentum (direction matters)
        self.momentum[emotion] = self.momentum[emotion] * 0.7 + (delta * 0.3)
        
    def tick(self) -> Dict[str, float]:
        """Process one turn of emotional physics. Returns deltas."""
        deltas = {}
        
        # 1. Apply bleed (emotion contamination)
        bleed_deltas = {k: 0.0 for k in self.state}
        for src, targets in self.config.bleed_matrix.items():
            if self.state[src] > 0.2:  # Only bleed from significant emotions
                for tgt, mult in targets.items():
                    bleed_deltas[tgt] += self.state[src] * mult * self.config.bleed_rate
        
        # 2. Apply decay toward neutral
        for emo in self.state:
            old_val = self.state[emo]
            
            # Decay
            decay = self.state[emo] * self.config.decay_rate
            self.state[emo] -= decay
            
            # Apply bleed
            self.state[emo] += bleed_deltas[emo]
            
            # Clamp
            self.state[emo] = max(self.config.floor, min(self.config.ceiling, self.state[emo]))
            
            # Decay momentum
            self.momentum[emo] *= 0.9
            
            deltas[emo] = self.state[emo] - old_val
        
        # Record history
        self.history.append(self.state.copy())
        
        return deltas
    
    def dominant(self) -> Tuple[str, float]:
        """Return the dominant emotion and its value."""
        emo = max(self.state, key=self.state.get)
        return emo, self.state[emo]
    
    def intensity(self) -> float:
        """Total emotional intensity (0-4 scale)."""
        return sum(self.state.values())
    
    def serialize(self) -> Dict:
        return {"state": self.state.copy(), "momentum": self.momentum.copy()}
    
    def deserialize(self, data: Dict) -> None:
        self.state = data.get("state", self.state)
        self.momentum = data.get("momentum", self.momentum)
