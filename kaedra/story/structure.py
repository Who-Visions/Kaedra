"""
StoryEngine Narrative Structure
Tracks the 5-Act structure and 'Roadmap of Change' (Yorke's framework).
"""
from dataclasses import dataclass
from typing import List


@dataclass
class NarrativeStructure:
    """Tracks the 5-Act structure and 'Roadmap of Change'."""
    act: int = 1
    progress: float = 0.0  # 0.0 to 1.0 (Narrative Completion)
    knowledge_state: float = 0.0 # 0.0 (Ignorance) -> 1.0 (Mastery)
    
    # Tentpole Thresholds
    INCITING_INCIDENT_THRESHOLD = 0.15
    PLOT_POINT_1_THRESHOLD = 0.25
    MIDPOINT_THRESHOLD = 0.50
    ALL_IS_LOST_THRESHOLD = 0.75
    CLIMAX_THRESHOLD = 0.90
    
    def tick(self, scene_count: int, target_length: int = 20) -> List[str]:
        """Advance narrative clock and return any structural directives."""
        old_phase = self.progress
        self.progress = min(1.0, scene_count / target_length)
        directives = []
        
        # Detect threshold crossings
        if old_phase < self.INCITING_INCIDENT_THRESHOLD <= self.progress:
            self.act = 1
            directives.append("DIRECTIVE: TRIGGER INCITING INCIDENT. Disrupt equilibrium. Create a Need.")
            
        elif old_phase < self.PLOT_POINT_1_THRESHOLD <= self.progress:
            self.act = 2
            directives.append("DIRECTIVE: CROSS THE THRESHOLD. The protagonist enters the Special World.")
            
        elif old_phase < self.MIDPOINT_THRESHOLD <= self.progress:
            self.act = 3
            directives.append("DIRECTIVE: EXECUTE MIDPOINT TWIST. Recontextualize previous events. Shift False Belief -> Truth.")
            self.knowledge_state = 0.5
            
        elif old_phase < self.ALL_IS_LOST_THRESHOLD <= self.progress:
            self.act = 4
            directives.append("DIRECTIVE: ALL IS LOST. The plan fails. Force a sacrifice.")
            
        elif old_phase < self.CLIMAX_THRESHOLD <= self.progress:
            self.act = 5
            directives.append("DIRECTIVE: TRIGGER CLIMAX. Final confrontation. Proof of change.")
            self.knowledge_state = 0.9
            
        return directives
