"""
KAEDRA v1.0 - Memory Service
Persistent memory storage using Vertex AI Memory Bank.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from dataclasses import dataclass, field

import vertexai
from vertexai import types  # pylint: disable=no-name-in-module

from kaedra.core.config import PROJECT_ID, LOCATION, MEMORY_DIR, AGENT_RESOURCE_NAME
from ..core.memory_topics import get_customization_config

@dataclass
class MemoryEntry:
    """Represents a single memory unit."""
    content: str
    role: str = "user"
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class MemoryService:
    """
    Manages persistent memory using Vertex AI Memory Bank (Agent Engine).
    Wraps the Agent Engine API to provide a simplified interface for Kaedra.
    """

    def __init__(self):
        self.project_id = PROJECT_ID
        self.location = LOCATION
        self.engine_name = "kaedra-memory-bank-v1"
        self.user_id = "kaedra-user-main"  # Single user mode for now
        self.session_name = None
        self.agent_engine_resource_name = AGENT_RESOURCE_NAME

        self._hl_client = None

        # We don't initialize client in init to allow pickling
        # self._ensure_client() # Lazy instead

    @property
    def hl_client(self):
        """Lazy-loaded Vertex AI Client."""
        if self._hl_client is None:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            self._hl_client = vertexai.Client(project=self.project_id, location=self.location)

            # Ensure resources exist when client is first accessed
            if not self.agent_engine_resource_name:
                self._ensure_agent_engine()
            else:
                 # Minimal log to avoid spam
                # print(f"[*] Using existing Agent Engine: {self.agent_engine_resource_name}")
                pass

            self._ensure_session()

        return self._hl_client

    @property
    def client(self):
        """Alias for hl_client."""
        return self.hl_client

    def __getstate__(self):
        """Exclude client from pickling."""
        state = self.__dict__.copy()
        if "_hl_client" in state:
            del state["_hl_client"]
        return state

    def __setstate__(self, state):
        """Restore state."""
        self.__dict__.update(state)
        self._hl_client = None

    def _get_model_path(self, model_name: str) -> str:
        """
        Get the full resource path for a model.
        Gemini 3 models must use 'global'.
        """
        location = "global" if "gemini-3" in model_name else self.location
        return (f"projects/{self.project_id}/locations/{location}/"
                f"publishers/google/models/{model_name}")

    def _ensure_agent_engine(self):
        """Find or create the Agent Engine."""
        print(f"[*] Ensuring Agent Engine '{self.engine_name}' exists...")

        try:
            engines = self.hl_client.agent_engines.list()
            for engine in engines:
                if engine.display_name == self.engine_name:
                    self.agent_engine_resource_name = engine.name
                    print(f"[*] Found existing Agent Engine: {self.agent_engine_resource_name}")
                    return
        except (RuntimeError, ValueError, AttributeError) as list_err:
            print(f"[!] Error listing agent engines: {list_err}")

        print(f"[*] Creating new Agent Engine '{self.engine_name}'...")

        model_name = "gemini-3-flash-preview"

        memory_config = types.ReasoningEngineContextSpecMemoryBankConfig(
            similarity_search_config=types.ReasoningEngineContextSpecMemoryBankConfigSimilaritySearchConfig(
                embedding_model=(f"projects/{self.project_id}/locations/{self.location}/"
                                 f"publishers/google/models/text-embedding-005")
            ),
            generation_config=types.ReasoningEngineContextSpecMemoryBankConfigGenerationConfig(
                model=self._get_model_path(model_name)
            ),
            customization_configs=[get_customization_config()]
        )

        try:
            op = self.hl_client.agent_engines.create(
                config={"context_spec": {"memory_bank_config": memory_config}},
                display_name=self.engine_name
            )
            self.agent_engine_resource_name = op.api_resource.name
            print(f"[*] Created Agent Engine: {self.agent_engine_resource_name}")

        except (RuntimeError, ValueError, AttributeError) as create_err:
            print(f"[!] Failed to create Agent Engine: {create_err}")
            raise create_err

    def _ensure_session(self):
        """Ensure a session exists for the user."""
        # We try to keep a persistent session ID file?
        session_file = MEMORY_DIR / "current_session.txt"

        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                self.session_name = f.read().strip()
                return

        print(f"[*] Creating new Session for {self.user_id}...")
        try:
            session = self.hl_client.agent_engines.sessions.create(
                name=self.agent_engine_resource_name,
                user_id=self.user_id,
                config={"display_name": f"Main Session for {self.user_id}"}
            )
            self.session_name = session.response.name

            # Save persist
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(self.session_name)

            print(f"[*] Created Session: {self.session_name}")

        except (RuntimeError, ValueError, AttributeError) as sess_err:
            print(f"[!] Session creation failed: {sess_err}")
            raise sess_err

    def insert(self, content: str, role: str = "user") -> str:
        """
        Add an event to the session memory.
        Note: This does NOT immediately generate a 'Memory' fact.
        It appends to history. You must call `consolidate()` to trigger extraction.
        """
        try:
            # We use a simple counter for invocation? Or UUID?
            # API requires invocation_id (string)
            inv_id = str(uuid.uuid4())

            self.hl_client.agent_engines.sessions.events.append(
                name=self.session_name,
                author=self.user_id if role == "user" else "kaedra",
                invocation_id=inv_id,
                timestamp=datetime.now(tz=timezone.utc),
                config={
                    "content": {"role": role, "parts": [{"text": content}]}
                }
            )
            return inv_id
        except (RuntimeError, ValueError, AttributeError) as ins_err:
            print(f"[!] Insert failed: {ins_err}")
            return ""

    def consolidate(self):
        """Trigger background memory generation from recent events."""
        print("[*] Consolidating memories in background...")
        try:
            # wait_for_completion=False for async background processing
            self.hl_client.agent_engines.memories.generate(
                name=self.agent_engine_resource_name,
                vertex_session_source={"session": self.session_name},
                config={"wait_for_completion": False}
            )
        except (RuntimeError, ValueError, AttributeError) as cons_err:
            print(f"[!] Consolidation failed: {cons_err}")

    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Semantic search over generated memories.
        """
        try:
            results = self.hl_client.agent_engines.memories.retrieve(
                name=self.agent_engine_resource_name,
                scope={"user_id": self.user_id},
                similarity_search_params={
                    "search_query": query,
                    "top_k": top_k,
                },
            )

            # Convert to dict format expected by KaedraAgent
            memories = []
            for item in results:
                mem = item.memory
                memories.append({
                    "content": mem.fact,
                    "topic": "memory_bank", # We don't get the topic label easily in the list view?
                    "timestamp": mem.create_time.isoformat() if mem.create_time else "",
                    "score": item.distance if hasattr(item, 'distance') else 0.0
                })
            return memories

        except (RuntimeError, ValueError, AttributeError) as rec_err:
            print(f"[!] Recall failed: {rec_err}")
            return []

    def list_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent memories (by creation time)."""
        # Retrieve all (scope based) and sort?
        try:
            results = self.hl_client.agent_engines.memories.retrieve(
                name=self.agent_engine_resource_name,
                scope={"user_id": self.user_id}
            )
            # This iterator might be large, but for now it's okay.
            # Convert to list and sort
            items = list(results)
            items.sort(key=lambda x: x.memory.create_time, reverse=True)

            memories = []
            for item in items[:limit]:
                mem = item.memory
                memories.append({
                    "content": mem.fact,
                    "timestamp": mem.create_time.isoformat() if mem.create_time else ""
                })
            return memories
        except (RuntimeError, ValueError, AttributeError) as list_rec_err:
            print(f"[!] List recent failed: {list_rec_err}")
            return []

    def get_stats(self) -> Dict:
        """Helper to get count."""
        try:
            results = self.hl_client.agent_engines.memories.retrieve(
                name=self.agent_engine_resource_name,
                scope={"user_id": self.user_id}
            )
            return {"total": len(list(results))}
        except (RuntimeError, ValueError, AttributeError):
            return {"total": 0}

