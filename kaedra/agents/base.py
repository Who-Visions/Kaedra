"""
KAEDRA v0.0.6 - Base Agent
Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..core.agent_types import AgentThread
from ..services.prompt import PromptService
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
                 name: str = "Agent",
                 context_provider: Optional[Any] = None):
        self.prompt = prompt_service
        self.memory = memory_service
        self.name = name
        self._profile = ""
        self.context_provider = context_provider

    @property
    @abstractmethod
    def profile(self) -> str:
        """Return the agent's personality profile/system prompt."""
        pass

    @abstractmethod
    async def run(self, query: str, thread: Optional[AgentThread] = None, context: str = None) -> AgentResponse:
        """
        Process a user query and return a response.
        """
        pass

    async def _get_external_context(self, thread: AgentThread) -> str:
        """Fetch context from the provided context provider."""
        if not self.context_provider:
            return ""
        
        parts = await self.context_provider.invoking_async(thread)
        return "\n\n".join(parts) if parts else ""

    def _build_prompt(self, query: str, context: str = None) -> str:
        """Build the full prompt with profile and context."""
        parts = [self.profile]

        if context:
            parts.append(f"\n[CONTEXT]\n{context}")

        parts.append(f"\n[USER MESSAGE]\n{query}")

        return "\n".join(parts)

    def _recall_memories(self, query: str, limit: int = 3) -> str:
        """Legacy Support: Recall relevant memories for context."""
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

    def _recall_recent(self, limit: int = 5) -> str:
        """Recall most recent memories for short-term context."""
        if not self.memory:
            return ""

        memories = self.memory.list_recent(limit=limit)
        if not memories:
            return ""

        memory_lines = []
        for m in memories:
            content = m.get('content', '')
            # memories are sorted newest first, but for prompt we might want them chronological or just listed
            memory_lines.append(f"- {content}")

        return "\n".join(memory_lines)
