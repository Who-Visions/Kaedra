"""
KAEDRA v0.0.6 - Council
Multi-agent discussion orchestration.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging
import asyncio

from .base import BaseAgent
from .kaedra import KaedraAgent
from .blade import BladeAgent
from .nyx import NyxAgent
from ..services.prompt import PromptService, PromptResult
from ..services.memory import MemoryService
from ..core.exceptions import AgentError


logger = logging.getLogger("kaedra.agents.council")


@dataclass
class CouncilResult:
    """Result of a council discussion."""
    query: str
    blade_response: str
    nyx_response: str
    kaedra_synthesis: str
    model: str
    total_latency_ms: float
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "blade": self.blade_response,
            "nyx": self.nyx_response,
            "synthesis": self.kaedra_synthesis,
            "model": self.model,
            "latency_ms": self.total_latency_ms
        }


class Council:
    """
    Multi-agent council for complex decision-making.
    
    Flow:
    1. BLADE provides action-focused perspective
    2. NYX provides risk-focused perspective
    3. KAEDRA synthesizes and makes final call
    """
    
    def __init__(
        self,
        prompt_service: PromptService,
        memory_service: MemoryService = None
    ):
        self.prompt = prompt_service
        self.memory = memory_service
        
        # Initialize agents
        self.kaedra = KaedraAgent(prompt_service, memory_service)
        self.blade = BladeAgent(prompt_service, memory_service)
        self.nyx = NyxAgent(prompt_service, memory_service)
        
        logger.info("Council initialized with KAEDRA, BLADE, NYX")
    
    async def convene(
        self,
        query: str,
        model: str = None,
        parallel: bool = False
    ) -> CouncilResult:
        """
        Convene the council to discuss a query.
        
        Args:
            query: Topic/question to discuss
            model: Model key to use
            parallel: Run BLADE and NYX in parallel (faster but less contextual)
        
        Returns:
            CouncilResult with all perspectives and synthesis
        """
        import time
        start_time = time.time()
        
        logger.info(f"Council convened for: {query[:50]}...")
        
        # Build BLADE prompt
        blade_prompt = f"""COUNCIL DISCUSSION

Topic: {query}

As BLADE, provide your action-focused perspective.
- What's the core opportunity or problem?
- What's the most direct path to action?
- What should we do RIGHT NOW?

Be direct. 2-4 sentences. End with a clear action.
"""
        
        if parallel:
            # Run BLADE and NYX in parallel
            blade_task = self.blade.run(blade_prompt, model)
            nyx_prompt = f"""COUNCIL DISCUSSION

Topic: {query}

As NYX, provide your strategic risk perspective.
- What patterns do you see?
- What risks might we miss?
- Should we PROCEED / PIVOT / PAUSE?

Be thorough but concise. 2-4 sentences.
"""
            nyx_task = self.nyx.run(nyx_prompt, model)
            
            blade_result, nyx_result = await asyncio.gather(blade_task, nyx_task)
        else:
            # Sequential (NYX can respond to BLADE)
            blade_result = await self.blade.run(blade_prompt, model)
            
            nyx_prompt = f"""COUNCIL DISCUSSION

Topic: {query}

BLADE's Position:
{blade_result.text}

As NYX, respond to BLADE's take.
- Where do you agree?
- What risks is BLADE missing?
- Should we PROCEED / PIVOT / PAUSE?

Be thorough but concise. 2-4 sentences.
"""
            nyx_result = await self.nyx.run(nyx_prompt, model)
        
        # KAEDRA synthesizes
        synthesis_prompt = f"""COUNCIL SYNTHESIS

Topic: {query}

BLADE's Position (Action-Focused):
{blade_result.text}

NYX's Position (Risk-Focused):
{nyx_result.text}

As KAEDRA, synthesize both perspectives and make the final call.

Structure:
1. Where do they agree?
2. Where do they disagree, and why?
3. What's the balanced path?
4. Your final directive.

3-5 sentences. Be decisive. End with "Here's what we're doing..."
"""
        
        synthesis_result = await self.kaedra.run(synthesis_prompt, model)
        
        total_latency = (time.time() - start_time) * 1000
        
        result = CouncilResult(
            query=query,
            blade_response=blade_result.text,
            nyx_response=nyx_result.text,
            kaedra_synthesis=synthesis_result.text,
            model=blade_result.model,
            total_latency_ms=total_latency
        )
        
        logger.info(f"Council concluded in {total_latency:.0f}ms")
        
        return result
    
    async def debate(
        self,
        topic: str,
        rounds: int = 2,
        model: str = None
    ) -> List[Dict[str, str]]:
        """
        Extended debate between BLADE and NYX.
        
        Args:
            topic: Topic to debate
            rounds: Number of back-and-forth rounds
            model: Model key
        
        Returns:
            List of debate turns
        """
        debate_log = []
        
        # BLADE opens
        blade_opener = f"""DEBATE: {topic}

You're opening the debate. State your position clearly and forcefully.
"""
        blade_result = await self.blade.run(blade_opener, model)
        debate_log.append({"agent": "BLADE", "content": blade_result.text})
        
        # Debate rounds
        for round_num in range(rounds):
            # NYX responds
            nyx_prompt = f"""DEBATE: {topic}
Round {round_num + 1}

BLADE just said:
{debate_log[-1]['content']}

Challenge their position. Find weaknesses. Make your counter-argument.
"""
            nyx_result = await self.nyx.run(nyx_prompt, model)
            debate_log.append({"agent": "NYX", "content": nyx_result.text})
            
            # BLADE responds
            blade_prompt = f"""DEBATE: {topic}
Round {round_num + 1}

NYX just said:
{debate_log[-1]['content']}

Defend your position. Counter their arguments. Stand your ground.
"""
            blade_result = await self.blade.run(blade_prompt, model)
            debate_log.append({"agent": "BLADE", "content": blade_result.text})
        
        # KAEDRA judges
        debate_summary = "\n\n".join([
            f"[{turn['agent']}]: {turn['content']}"
            for turn in debate_log
        ])
        
        judge_prompt = f"""DEBATE JUDGMENT: {topic}

Full debate:
{debate_summary}

As the judge, determine:
1. Strongest arguments from each side
2. Who made the better case overall
3. What the truth likely is
4. Final ruling
"""
        
        judgment = await self.kaedra.run(judge_prompt, model)
        debate_log.append({"agent": "KAEDRA (Judge)", "content": judgment.text})
        
        return debate_log
    
    def get_agents(self) -> Dict[str, BaseAgent]:
        """Get all council agents."""
        return {
            "kaedra": self.kaedra,
            "blade": self.blade,
            "nyx": self.nyx
        }
