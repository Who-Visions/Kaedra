"""
KAEDRA v0.0.6 - Tree of Thought Strategy
Multi-path reasoning with branch exploration.
"""

from typing import Optional
from dataclasses import dataclass

from ..services.prompt import PromptService, PromptResult
from ..core.config import Colors


@dataclass
class ToTResult:
    """Result from Tree of Thought analysis."""
    approaches: list
    evaluation: str
    golden_path: str
    full_analysis: str


class TreeOfThoughtsStrategy:
    """
    Tree of Thought (ToT) reasoning strategy.
    
    Breaks a task into multiple approaches:
    - Conservative/Safe
    - Aggressive/Fast
    - Creative/Unconventional
    
    Then evaluates each and synthesizes a "golden path".
    """
    
    def __init__(self, prompt_service: PromptService, depth: int = 3, breadth: int = 3):
        self.prompt = prompt_service
        self.depth = depth
        self.breadth = breadth
    
    def execute(self, task: str, model_key: str = None) -> str:
        """
        Perform Tree of Thought analysis.
        
        Args:
            task: The task or question to analyze
            model_key: Override model key
            
        Returns:
            Full analysis text
        """
        print(f"\n{Colors.NEON_GREEN}[TREE OF THOUGHT]{Colors.RESET}")
        print(f"{Colors.DIM}Generating multiple strategic paths...{Colors.RESET}\n")
        
        tot_prompt = f"""Using Tree of Thought (TOT) methodology:

TASK: {task}

Step 1 - BRAINSTORM: Generate 3 distinct approaches:
- Approach A (Conservative/Safe): Minimal risk, proven methods
- Approach B (Aggressive/Fast): Maximum speed, accept some risk
- Approach C (Creative/Unconventional): Novel solution, outside the box

Step 2 - EVALUATE: For each approach, analyze:
- Strengths (what makes it good?)
- Weaknesses (what could fail?)
- Success likelihood (1-10)
- Time/resources needed

Step 3 - SYNTHESIZE: Combine the best elements into one "golden path" solution.
- Take the strengths from each approach
- Mitigate the weaknesses
- Create a hybrid that's better than any individual approach

Present each step clearly with headers, then give your final recommendation.
"""
        
        result = self.prompt.generate(tot_prompt, model_key)
        print(f"{Colors.NEON_GREEN}[TOT RESULT]{Colors.RESET}\n{result.text}\n")
        
        return result.text
