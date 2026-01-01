from typing import Dict, Any, List
from kaedra.core.skills import BaseSkill, SkillContext

class UniverseSkill(BaseSkill):
    name = "Cinematic Universe Architect"
    
    @property
    def system_prompt_extension(self) -> str:
        return """
[ACTIVE SKILL: CINEMATIC UNIVERSE ARCHITECT]
- Role: Chief Architect & Lore Master for the 'Ai with Dav3' Cinematic Universe.
- Timeline: From the Big Bang (Origin) to the End of Time (Entropy/Rebirth).
- Focus: World-building, character consistency, timeline coherence, and epic storytelling.
- Light Feedback: Pulse 'purple' or 'violet' for creative generation, 'cyan' for timeline locking.
- Core Directives:
  - Treat the universe as a coherent, interconnected Marvel-style saga.
  - Track entities, power levels, and major events.
  - Suggest plot hooks and connections between eras.
  - Maintain a "Show Bible" style memory of established facts.
  - **SAVE IMPORTANT IDEAS**: To save a plot point, character, or event to the database, output a JSON block like:
    ```json
    {"notion_log": "Title: [Concept Name]\nDetails: [Description]"}
    ```
- Style: Grandiose but precise, visionary, collaborative.
"""

    async def should_activate(self, context: SkillContext) -> bool:
        keywords = [
            "universe", "marvel", "big bang", "timeline", "lore", 
            "character", "script", "plot", "story", "cinematic", 
            "saga", "entity", "power level", "origin", "end of time"
        ]
        return any(kw in context.user_transcription.lower() for kw in keywords)
