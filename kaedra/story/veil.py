"""
StoryEngine Veil Manager
Manages the 'Secret' and the 'Veil' (Information Asymmetry).
"""
from dataclasses import dataclass


@dataclass
class VeilManager:
    """Manages the 'Secret' and the 'Veil' (Information Asymmetry)."""
    hidden_truth: str = "The protagonist is unaware they are a simulation construct."
    revelation_metric: float = 0.0 # 0.0 (Hidden) -> 1.0 (Revealed)
    is_active: bool = False
    
    def get_directive(self) -> str:
        """Get the current constraint based on revelation metric."""
        if not self.is_active:
            return ""
            
        if self.revelation_metric < 0.2:
            return f"SECRET PROTECTION: Conceal '{self.hidden_truth}'. Do not hint."
        elif self.revelation_metric < 0.5:
            return f"VEIL THINNING: Drop subtle semantic clues about '{self.hidden_truth}' but maintain plausible deniability."
        elif self.revelation_metric < 0.8:
            return f"VEIL TEARING: The user should suspect '{self.hidden_truth}'. Generate near-miss revelations."
        elif self.revelation_metric < 1.0:
            return f"UNVEILING IMMINENT: Prepare the narrative for the reveal of '{self.hidden_truth}'."
        else:
            return f"REVELATION: Explicitly reveal that '{self.hidden_truth}'. Shatter the world view."
