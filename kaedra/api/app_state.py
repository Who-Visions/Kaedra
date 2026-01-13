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

# Global state instance
state = AppState()
