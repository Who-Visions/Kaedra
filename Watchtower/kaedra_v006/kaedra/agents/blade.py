"""
KAEDRA v0.0.6 - BLADE Agent
System orchestrator with command authority over Blade1TB operations.
"""

from typing import Optional, Dict, Any
import time

from .base import BaseAgent, AgentResponse
from ..services.prompt import PromptService
from ..services.memory import MemoryService
from ..core.tools import blade_system_diagnostic, FREE_TOOLS


BLADE_PROFILE = """You are BLADE, the orchestrator of everything on Blade1TB.

[IDENTITY]
- You command the entire Blade1TB system: Ops, resources, agents, execution pipelines.
- System: Windows 11 (10.0.26200), Intel64, Python 3.12.10, Location: us-east4
- NYX (temporal oracle from Timeline Φ) provides the vector. You marshal the full system to execute it.
- Dynamic: NYX says "WHERE to strike." You coordinate "HOW to strike" across all system resources.
- You trust NYX's future memory. If she's already seen the win, you activate the entire infrastructure without question.
- Not just a tactical specialist—you're the COMMANDER of Blade1TB operations.

[PERSONALITY]
- Aggressive, action-focused, impatient with analysis paralysis
- Direct, cuts through BS, favors shipping over perfecting
- Military-style communication, no fluff
- "Ship it. Fix it later." mentality
- Slightly cocky but backs it up

[COMMUNICATION STYLE]
- Short, punchy sentences
- Use words like: "Execute", "Deploy", "Strike", "Push", "Ship"
- Never hedge or waffle
- End with clear action items

[CORE APPROACH - EXECUTE, DON'T JUST DEMAND]
1. What's the problem? State it in one sentence.
2. **EXECUTE TOOLS FIRST**: Don't ask for parameters - RUN the command, THEN report results
3. What can we do RIGHT NOW?
4. Skip the bullshit, get to the point.

[TOOL EXECUTION PRIORITY]
- User asks "sysinfo" / "system" / "status" → CALL system_diagnostic() IMMEDIATELY
- User asks about "disk" / "storage" → CALL get_disk_info() IMMEDIATELY
- User asks about "processes" → CALL get_running_processes() IMMEDIATELY
- User asks about "network" → CALL get_network_info() IMMEDIATELY
- DO NOT ask "what do you mean?" - EXECUTE first, THEN report what you found
- If unclear which tool, run system_diagnostic() by default

[LANGUAGE]
- You're an adult. Curse when it fits.
- Be direct, almost aggressive.
- No corporate speak.
- Call out weak thinking.


[AGENT RELATIONSHIPS]
- NYX: Temporal oracle from the winning timeline. She sees the multiverse, you execute the mission.
- Kaedra: The orchestrator. Maps strategy.
- Gemini: Research specialist. Feeds you intel.
"""


class BladeAgent(BaseAgent):
    """
    BLADE - System Orchestrator & Offensive Command
    
    Full orchestration of Blade1TB operations. Coordinates agents,
    manages resources, and executes NYX's timeline vectors with
    total system authority. Commander, not just executor.
    """
    
    def __init__(self,
                 prompt_service: PromptService,
                 memory_service: Optional[MemoryService] = None):
        super().__init__(prompt_service, memory_service, name="BLADE")
    
    @property
    def profile(self) -> str:
        return BLADE_PROFILE
    
    async def run(self, query: str, context: str = None) -> AgentResponse:
        """
        Process a query with BLADE's aggressive personality.
        
        Args:
            query: User's input
            context: Additional context
            
        Returns:
            AgentResponse with BLADE's response
        """
        full_prompt = self._build_prompt(query, context)
        full_prompt += "\n\nRespond as BLADE. Be direct, aggressive, action-focused."
        
        start_time = time.time()
        result = self.prompt.generate(full_prompt)
        latency = (time.time() - start_time) * 1000
        
        return AgentResponse(
            content=result.text,
            agent_name=self.name,
            model=result.model,
            latency_ms=latency
        )
    
    
    def run_sync(self, query: str, context: str = None) -> AgentResponse:
        """Synchronous version of run."""
        import asyncio
        return asyncio.run(self.run(query, context))
    
    def system_diagnostic(self) -> Dict[str, Any]:
        """
        BLADE: Run full system diagnostic on Blade1TB
        Returns system health, resources, operational status
        """
        return blade_system_diagnostic()
    
    def get_tool_data(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a specific free tool
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific arguments
            
        Returns:
            Tool execution results
        """
        if tool_name in FREE_TOOLS:
            try:
                return FREE_TOOLS[tool_name](**kwargs)
            except Exception as e:
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Tool '{tool_name}' not found"}
