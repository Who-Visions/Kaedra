"""
StoryEngine Tension Curve
Manages narrative tension with target curves.
"""
from dataclasses import dataclass


@dataclass
class TensionCurve:
    """Manages narrative tension with target curves."""
    current: float = 0.2
    target: float = 0.5
    velocity: float = 0.0
    
    # Predefined dramatic curves
    CURVES = {
        "rising": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "falling": [0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1],
        "sawtooth": [0.3, 0.5, 0.7, 0.4, 0.6, 0.8, 0.5, 0.9, 0.3],
        "climax": [0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 0.3],
        "dread": [0.5, 0.55, 0.6, 0.62, 0.65, 0.7, 0.75, 0.9, 1.0],
    }
    
    def tick(self, scene: int, total_scenes: int = 10) -> float:
        """Advance tension based on narrative position."""
        # Spring physics toward target
        force = (self.target - self.current) * 0.2
        self.velocity = self.velocity * 0.8 + force
        self.current = max(0.0, min(1.0, self.current + self.velocity))
        return self.current
    
    def set_curve(self, curve_name: str) -> None:
        """Load a predefined tension curve."""
        if curve_name in self.CURVES:
            self._curve_points = self.CURVES[curve_name]
            self._curve_index = 0
    
    def advance_curve(self) -> None:
        """Move to next point in loaded curve."""
        if hasattr(self, '_curve_points') and self._curve_index < len(self._curve_points):
            self.target = self._curve_points[self._curve_index]
            self._curve_index += 1
