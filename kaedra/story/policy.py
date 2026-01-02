"""
🧠 Autonomy Policy Engine (v9.2)
Decides the next best action for the autonomous writer based on engine state.
"""
from dataclasses import dataclass
from typing import Optional
from kaedra.story.doctrine import DoctrineState

@dataclass
class PolicyAction:
    action_type: str # 'write_beat', 'ensure_questions', 'cleanup_doctrine', 'wait', 'stop'
    reason: str
    metadata: dict = None

class AutonomyPolicy:
    """Decides what to do next in the autonomous loop."""
    
    def decide(self, engine) -> PolicyAction:
        # 1. Doctrine Check (Hygiene first)
        if engine.doctrine.abstraction_debt > 5:
            return PolicyAction(
                "cleanup_doctrine", 
                f"Abstraction debt is high ({engine.doctrine.abstraction_debt}). Need to ground the scene."
            )
            
        # 2. Logic Gaps
        # Future: If we have pending extraction tasks or worldforge requirements
        
        # 3. Default: Drive the story
        if engine.auto.state == "running":
            return PolicyAction("write_beat", "Continuing narrative flow.")
            
        return PolicyAction("wait", "Idle.")
