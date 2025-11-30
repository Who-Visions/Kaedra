"""
KAEDRA v0.0.6 - Base Agent
Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..services.prompt import PromptService, PromptResult
from ..services.memory import MemoryService


@dataclass
class AgentResponse:
    """Structured response from an agent."""
    content: str
    agent_name: str
    model: str
    latency_ms: float
    metadata: Optional[Dict] = None


class BaseAgent(ABC):
    """
    Abstract base class for KAEDRA agents.
    
    All agents (KAEDRA, BLADE, NYX) inherit from this class
    and implement their own personality and behavior.
    """
    
    def __init__(self, 
                 prompt_service: PromptService,
                 memory_service: Optional[MemoryService] = None,
                 name: str = "Agent"):
        self.prompt = prompt_service
        self.memory = memory_service
        self.name = name
        self._profile = ""
    
    @property
    @abstractmethod
    def profile(self) -> str:
        """Return the agent's personality profile/system prompt."""
        pass
    
    @abstractmethod
    async def run(self, query: str, context: str = None) -> AgentResponse:
        """
        Process a user query and return a response.
        
        Args:
            query: The user's input
            context: Optional additional context
            
        Returns:
            AgentResponse with the agent's response
        """
        pass
    
    def _build_prompt(self, query: str, context: str = None) -> str:
        """Build the full prompt with profile and context."""
        parts = [self.profile]
        
        if context:
            parts.append(f"\n[CONTEXT]\n{context}")
        
        parts.append(f"\n[USER MESSAGE]\n{query}")
        
        return "\n".join(parts)
    
    def _recall_memories(self, query: str, limit: int = 3) -> str:
        """Recall relevant memories for context."""
        if not self.memory:
            return ""
        
        memories = self.memory.recall(query, top_k=limit)
        if not memories:
            return ""
        
        memory_lines = []
        for m in memories:
            date = m.get('timestamp', '').split('T')[0]
            topic = m.get('topic', 'general')
            content = m.get('content', '')
            memory_lines.append(f"- [{date}] {topic}: {content}")
        
        return "\n".join(memory_lines)
