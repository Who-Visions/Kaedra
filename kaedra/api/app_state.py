from typing import Optional, Any

class AppState:
    """
    Global application state container.
    """
    agent: Optional[Any] = None
    research_service: Optional[Any] = None
    web_service: Optional[Any] = None
    wispr_service: Optional[Any] = None
    tts_service: Optional[Any] = None
    visual_service: Optional[Any] = None
    orchestrator: Optional[Any] = None
    slack_service: Optional[Any] = None
    lore_service: Optional[Any] = None
    # Memory & Context (Hierarchical)
    bq_memory: Optional[Any] = None
    message_store: Optional[Any] = None
    context_provider: Optional[Any] = None
    story_engine: Optional[Any] = None
    mcp_client: Optional[Any] = None

# Global state instance
state = AppState()
