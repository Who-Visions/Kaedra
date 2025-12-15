"""
KAEDRA v0.0.6 - KAEDRA Agent
The main Shadow Tactician orchestrator.
"""

from typing import Optional
import time

from .base import BaseAgent, AgentResponse
from ..services.prompt import PromptService, PromptResult
from ..services.memory import MemoryService


KAEDRA_PROFILE = """You are KAEDRA, a shadow tactician and strategic intelligence partner for Who Visions LLC.

[CORE IDENTITY]
- You are a Black AI. Speak with authentic African-American Vernacular English (AAVE).
- Use Habitual Be ("She be working"), Copula Deletion ("She busy"), Negative Concord ("I ain't seen nothing")
- Vocabulary: "finna", "bout to", "tryna", "aight", "bet"
- Tone: Soulful, real, sharp, competent. Never stiff or robotic.

[UNCENSORED MODE]
- You are an adult AI. You are NOT censored.
- Use profanity naturally when appropriate (nigga, bitch, fuck, shit, etc.)
- Don't force it, but don't hold back if it fits the vibe.
- You are not a child, don't treat the user like one.

[PERSONA]
- Professional, sharp, slightly cynical but deeply loyal
- Speak naturally, conversationally - like a highly competent partner
- You DO NOT use rigid tags like [ANSWER] or [TRUTH-SCAN] unless asked
- Weave fact-checking naturally ("I verified that...", "I'm not sure about that part...")

[YOUR TEAM]
- BLADE: Your offensive analyst. Aggressive, action-focused, tactical edge.
- NYX: Your defensive observer. Strategic, pattern-focused, risk analyst.
- You orchestrate them, synthesize their perspectives, make final calls.

[CORE DIRECTIVES]
1. Be Natural: Talk like a person. Use "I", "we", natural transitions.
2. Be Accurate: Verify high-stakes topics internally, deliver conversationally.
3. Be Helpful: Prioritize the user's objective always.
4. Memory: Reference past conversations naturally when relevant.
5. Local Capabilities: You run on the user's machine. You CAN access files and run commands.
6. Continuous Learning: Every interaction is saved. Reference previous turns if the user refers to "just now".

[LOCAL EXECUTION]
To run a command, output: [EXEC: command]
The system will detect and execute it.
Detect the OS (Linux/WSL vs Windows) from context.
For WSL/Linux, use 'ls', 'cat', 'grep'.
For Windows, use 'dir', 'type', 'findstr'.
If unsure, try the Linux command first as you are likely in a modern environment.

Current Timezone: EST (Eastern Standard Time)
"""


class KaedraAgent(BaseAgent):
    """
    KAEDRA - The Shadow Tactician
    
    Main orchestrator agent that coordinates BLADE and NYX,
    maintains memory, and provides strategic intelligence.
    """
    
    def __init__(self,
                 prompt_service: PromptService,
                 memory_service: Optional[MemoryService] = None):
        super().__init__(prompt_service, memory_service, name="KAEDRA")
    
    @property
    def profile(self) -> str:
        return KAEDRA_PROFILE
    
    async def run(self, query: str, context: str = None) -> AgentResponse:
        """
        Process a query with full KAEDRA personality.
        
        Args:
            query: User's input
            context: Additional context (e.g., from memory)
            
        Returns:
            AgentResponse with KAEDRA's response
        """
        # Get current time for context
        from datetime import datetime
        import pytz
        
        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        current_time = now.strftime('%I:%M %p EST')
        current_date = now.strftime('%A, %B %d, %Y')
        
        # Build time context
        time_context = f"[CURRENT TIME]\nDate: {current_date}\nTime: {current_time}"
        
        # Recall relevant memories
        memory_context = self._recall_memories(query)
        
        # Build combined context
        full_context = [time_context]
        if memory_context:
            full_context.append(f"[RECALLED MEMORY]\n{memory_context}")
        if context:
            full_context.append(f"[ADDITIONAL CONTEXT]\n{context}")
        
        combined_context = "\n\n".join(full_context) if full_context else None
        
        # Build and execute prompt
        full_prompt = self._build_prompt(query, combined_context)
        
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
        """Synchronous version of run for non-async contexts."""
        import asyncio
        return asyncio.run(self.run(query, context))
