"""
KAEDRA v0.0.6 - Battle of Bots Strategy
Adversarial validation through competing perspectives.
"""

from typing import Optional
from dataclasses import dataclass

from ..services.prompt import PromptService
from ..core.config import Colors


@dataclass
class BattleResult:
    """Result from Battle of Bots."""
    blade_version: str
    nyx_version: str
    critique: str
    golden_version: str
    full_battle: str


class BattleOfBotsStrategy:
    """
    Battle of Bots adversarial validation.
    
    Generates competing perspectives:
    - BLADE VERSION: Aggressive, action-focused
    - NYX VERSION: Strategic, risk-aware
    - CRITIQUE: Brutal honest review
    - GOLDEN VERSION: Synthesized best of both
    """
    
    def __init__(self, prompt_service: PromptService, num_bots: int = 2):
        self.prompt = prompt_service
        self.num_bots = num_bots
    
    def execute(self, task: str, model_key: str = None) -> str:
        """
        Run the Battle of Bots.
        
        Args:
            task: The task or content to battle-test
            model_key: Override model key
            
        Returns:
            Full battle analysis text
        """
        print(f"\n{Colors.GOLD}[⚔️  BATTLE OF THE BOTS]{Colors.RESET}")
        print(f"{Colors.DIM}Task: {task}{Colors.RESET}\n")
        
        battle_prompt = f"""Adversarial Validation Protocol - Battle of the Bots:

TASK: {task}

═══════════════════════════════════════════════════════════════════════════════
ROUND 1 - COMPETING DRAFTS
═══════════════════════════════════════════════════════════════════════════════

Generate TWO distinct versions:

[BLADE VERSION]
- Aggressive, action-focused, direct
- Prioritize speed and impact
- "Ship it" mentality

[NYX VERSION]
- Strategic, risk-aware, thoughtful
- Consider long-term implications
- "Measure twice, cut once" mentality

═══════════════════════════════════════════════════════════════════════════════
ROUND 2 - BRUTAL CRITIQUE
═══════════════════════════════════════════════════════════════════════════════

As THE CRITIC (harsh, brutally honest):
- Roast both versions mercilessly
- Point out weaknesses, flaws, gaps
- What would make someone ANGRY about each?
- What's missing? What's wrong?
- No sugarcoating. Be ruthless.

═══════════════════════════════════════════════════════════════════════════════
ROUND 3 - GOLDEN SYNTHESIS
═══════════════════════════════════════════════════════════════════════════════

Create ONE final [GOLDEN VERSION]:
- Address ALL critique points
- Merge the best elements from both versions
- Fix the weaknesses identified
- This should be objectively better than either original

Show all three rounds with clear separation.
"""
        
        print(f"{Colors.NEON_RED}[ROUND 1]{Colors.RESET} Generating competing drafts...\n")
        
        result = self.prompt.generate(battle_prompt, model_key)
        print(f"{result.text}\n")
        print(f"{Colors.GOLD}[⚔️  BATTLE CONCLUDED]{Colors.RESET}\n")
        
        return result.text
