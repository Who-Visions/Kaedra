"""
StoryEngine Doctrine Kernel (v8.0)
Enforces narrative rules as runtime state.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal

MiceType = Literal["milieu", "inquiry", "character", "event"]
TryFailType = Literal["yes_but", "no_and", "clean_yes", "clean_no"]

@dataclass
class MiceThread:
    kind: MiceType
    label: str
    opened_scene: int
    close_condition: str

@dataclass
class PromiseLedger:
    tone: str = ""
    plot: str = ""
    character_arc: str = ""

@dataclass
class DoctrineState:
    mice_stack: List[MiceThread] = field(default_factory=list)
    promises: PromiseLedger = field(default_factory=PromiseLedger)
    progress_markers: List[str] = field(default_factory=list)
    
    # Metrics
    red_marks: float = 0.0
    green_marks: float = 0.0
    abstraction_debt: int = 0
    
    # Recent history
    last_try_fail: Optional[TryFailType] = None
    last_fresh_news: str = ""

    # Character State
    wound: str = "Unknown"
    identity_stage: int = 1
    pattern: str = "HELD"

class MiceManager:
    """Enforces LIFO (Last-In, First-Out) nesting for MICE threads."""
    def __init__(self, state: DoctrineState):
        self.state = state

    def open_thread(self, kind: MiceType, label: str, scene: int, close_condition: str):
        self.state.mice_stack.append(MiceThread(kind, label, scene, close_condition))

    def close_thread(self, kind: MiceType, label: Optional[str] = None) -> bool:
        if not self.state.mice_stack:
            return False

        top = self.state.mice_stack[-1]
        
        # Strict LIFO check
        if top.kind != kind:
            return False
            
        if label and top.label != label:
            return False

        self.state.mice_stack.pop()
        return True

    def blockers_for(self, kind_to_close: MiceType) -> List[MiceThread]:
        """Returns threads that must be closed before the requested kind (LIFO enforcement)."""
        blockers = []
        # Iterate from top of stack down
        for t in reversed(self.state.mice_stack):
            if t.kind == kind_to_close:
                break
            blockers.append(t)
        return blockers

ABSTRACT_WORDS = {
    "destiny", "meaning", "ideology", "myth", "essence", "spirit", 
    "power", "truth", "fear", "love", "soul", "purpose", "void", "chaos",
    "identity"
}
SENSORY_WORDS = {
    "smell", "metal", "dust", "heat", "cold", "breath", "blood", "rust", 
    "ozone", "grit", "shadow", "light", "sweat", "taste", "shiver", "click",
    "pressure"
}

def score_output(text: str) -> Dict[str, float]:
    """Audit the output text and update debt metrics."""
    t = (text or "").lower()
    
    # Count occurrences
    abs_count = sum(t.count(w) for w in ABSTRACT_WORDS)
    sen_count = sum(t.count(w) for w in SENSORY_WORDS)

    # Abstraction Debt: Penalty if abstract > sensory
    turn_debt = 0
    if abs_count > sen_count:
        turn_debt = abs_count - sen_count
        
    # Green Marks (Good Habits)
    turn_green = 0.0
    if any(k in t for k in ["fresh news", "suddenly", "but then", "until"]):
        turn_green += 1.0
    if "?" in t: # Curiosity hook
        turn_green += 0.5

    # Red Marks (Bad Habits)
    turn_red = 0.0
    if turn_debt > 6:
        turn_red += 1.0
    
    return {
        "debt": float(turn_debt), 
        "red": turn_red, 
        "green": turn_green
    }

def doctrine_directives(state: DoctrineState) -> List[str]:
    """Generate actionable directives for the prompt based on current state."""
    directives = []

    # 1. MICE Enforcement
    if state.mice_stack:
        top = state.mice_stack[-1]
        directives.append(f"FOCUS: The active thread is {top.kind.upper()} ('{top.label}'). Close this before moving to other threads.")

    # 2. Abstraction Debt
    if state.abstraction_debt > 5:
        directives.append(f"WARNING: High Abstraction Debt ({state.abstraction_debt}). You are forbidden from using abstract concepts. Force 3 lines of concrete sensory detail.")
    elif state.abstraction_debt > 0:
        directives.append("GUIDANCE: Pay abstraction debt first using concrete sensory detail.")

    # 3. Red/Green Balance
    if state.red_marks > state.green_marks + 2:
        directives.append("CRITICAL: Reader patience is low. Trigger a 'Fresh News' event or a high-stakes action immediately.")

    # 4. Progress Markers
    if not state.progress_markers:
        directives.append("STRUCTURE: Add one visible progress marker toward the umbrella goal.")
        
    # 5. Try/Fail defaults
    if not state.last_try_fail:
        directives.append("ACTION: Use a try fail outcome: yes_but or no_and.")

    return directives[:7] # Limit to prevent context flooding
