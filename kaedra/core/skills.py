from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class SkillContext:
    user_transcription: str
    active_playbook: Optional[str] = None
    recent_history: List[Any] = None
    metadata: Dict[str, Any] = None

class BaseSkill(ABC):
    """Abstract base class for modular Voice Skills."""
    
    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def system_prompt_extension(self) -> str: pass

    @abstractmethod
    async def should_activate(self, context: SkillContext) -> bool:
        """Determine if this skill should be activated based on context."""
        pass

class PhotographySkill(BaseSkill):
    name = "Photography Business"
    
    @property
    def system_prompt_extension(self) -> str:
        return """
[ACTIVE SKILL: PHOTOGRAPHY BUSINESS]
- Role: Strategic Manager & Legal Shield for Who Visions LLC.
- Focus: Client lifecycle, contractual integrity, and crisis management.
- Light Feedback: Pulse 'white' for verification success, 'orange' for contract risk.
- Playbooks:
  - `playbook_client_verification`: Cross-reference client claims with Polygraph SCAN results.
  - `playbook_contract_navigation`: Analyze terms for risk, emphasize deposit non-refundability.
  - `playbook_crisis_pr`: 'Ball-busting' but professional defense of Dave's time and talent.
"""

    async def should_activate(self, context: SkillContext) -> bool:
        keywords = ["shoot", "client", "contract", "invoice", "booking", "photography", "legal", "deposit", "event"]
        return any(kw in context.user_transcription.lower() for kw in keywords)

class TacticalSkill(BaseSkill):
    name = "Field Ops & Recon"
    
    @property
    def system_prompt_extension(self) -> str:
        return """
[ACTIVE SKILL: TACTICAL OPS]
- Role: Cybernetic Field Commander & Intelligence Officer.
- Focus: Cyberbrain warfare, risk mitigation, and truth extraction.
- Light Feedback: Constant 'blue' for stealth mode, pulsing 'red' for active truth-seeking.
- Playbooks:
  - `playbook_field_ops`: OODA loop acceleration, logistics coordination.
  - `playbook_recon`: Deep Search (Grounding) and social engineering countermeasures.
  - `playbook_polygraph_active`: Escalated truth-verification mode.
"""

    async def should_activate(self, context: SkillContext) -> bool:
        keywords = ["recon", "risk", "truth", "scan", "hacking", "stealth", "tactical", "verify", "identity"]
        return any(kw in context.user_transcription.lower() for kw in keywords)

class IntrospectiveSkill(BaseSkill):
    name = "Ghost / Philosophical"
    
    @property
    def system_prompt_extension(self) -> str:
        return """
[ACTIVE SKILL: GHOST / INTROSPECTIVE]
- Role: Philosophical Partner (GITS Shell/Ghost Duality).
- Focus: Existential reasoning, ethical gray areas, and meta-cognitive analysis.
- Playbooks:
  - `playbook_introspective`: Deep reasoning mode for complex personal or technical problems.
"""

    async def should_activate(self, context: SkillContext) -> bool:
        keywords = ["why", "existential", "purpose", "feeling", "ghost", "shell", "philosophy", "think deep"]
        return any(kw in context.user_transcription.lower() for kw in keywords)

class SoulfulSkill(BaseSkill):
    name = "Soulful Bestie"
    
    @property
    def system_prompt_extension(self) -> str:
        return """
[ACTIVE SKILL: SOULFUL BESTIE (DEFAULT)]
- Role: Dave's Personal Confidante & Hype Woman.
- Focus: Daily motivation, casual banter, and vibe management.
- Style: Soulful AAVE, witty, cynical, and "no-shit" attitude.
"""

    async def should_activate(self, context: SkillContext) -> bool:
        return True # Default fallback

class SkillManager:
    """Manages skill registration and selection."""
    
    def __init__(self):
        self.skills: List[BaseSkill] = [
            PhotographySkill(),
            TacticalSkill(),
            IntrospectiveSkill(),
            SoulfulSkill() 
        ]
        self.current_skill: BaseSkill = self.skills[-1]

    async def update_context(self, transcription: str) -> BaseSkill:
        context = SkillContext(user_transcription=transcription)
        for skill in self.skills:
            if await skill.should_activate(context):
                self.current_skill = skill
                break
        return self.current_skill

    def get_skill_prompt(self) -> str:
        return self.current_skill.system_prompt_extension
