"""
KAEDRA v0.0.6 - Response Router
Handles async response dispatch to multiple handlers (logging, TUI, webhooks).
"""

import asyncio
from typing import Callable, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Response:
    """Structured response from an agent."""
    content: str
    agent: str
    model: str
    timestamp: datetime
    metadata: Optional[dict] = None


class ResponseRouter:
    """
    Routes agent responses to multiple async handlers.
    
    Supports:
    - Logging handlers
    - TUI update handlers
    - Webhook handlers (Notion, etc.)
    - Background analysis handlers
    """
    
    def __init__(self):
        self._handlers: List[Callable] = []
        self._async_handlers: List[Callable] = []
    
    def register(self, handler: Callable, is_async: bool = False):
        """Register a response handler."""
        if is_async:
            self._async_handlers.append(handler)
        else:
            self._handlers.append(handler)
    
    def unregister(self, handler: Callable):
        """Remove a handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)
        if handler in self._async_handlers:
            self._async_handlers.remove(handler)
    
    async def dispatch(self, response: Response):
        """
        Dispatch response to all registered handlers.
        Sync handlers run first, then async handlers run concurrently.
        """
        # Run sync handlers
        for handler in self._handlers:
            try:
                handler(response)
            except Exception as e:
                print(f"[ROUTER] Handler error: {e}")
        
        # Run async handlers concurrently
        if self._async_handlers:
            tasks = [
                asyncio.create_task(self._safe_async_call(handler, response))
                for handler in self._async_handlers
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_async_call(self, handler: Callable, response: Response):
        """Safely call an async handler with error handling."""
        try:
            await handler(response)
        except Exception as e:
            print(f"[ROUTER] Async handler error: {e}")
    
    def dispatch_sync(self, response: Response):
        """
        Synchronous dispatch for non-async contexts.
        Runs async handlers in a new event loop.
        """
        asyncio.run(self.dispatch(response))


# Global router instance
_router: Optional[ResponseRouter] = None


def get_router() -> ResponseRouter:
    """Get or create the global router instance."""
    global _router
    if _router is None:
        _router = ResponseRouter()
    return _router
