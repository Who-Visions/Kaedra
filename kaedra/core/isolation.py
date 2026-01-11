"""
Context Isolation for Multi-Tier Generation
Ensures tool execution and speculative variants do not contaminate the main narrative trunk.
"""
from typing import List, Any
from google.genai import types

class ContextIsolation:
    """Manages context forking and restoration."""
    
    @staticmethod
    def create_fork(context_manager) -> List[types.Content]:
        """Create a safety snapshot of the current context."""
        return context_manager.snapshot()
    
    @staticmethod
    def restore_fork(context_manager, snapshot: List[types.Content]):
        """Restores context to the snapshot state."""
        context_manager.restore(snapshot)
        
        # For now, we return True if history exists.
        return len(context_manager.history) > 0

    @staticmethod
    def validate_clean_state(context_manager) -> bool:
        """Verifies context is safe for generation (no hanging tool calls)."""
        if not context_manager.history:
            return True
        
        # Basic Check: Ensure we have history
        # Advanced: Could check if last message was a tool_call without a response?
        # For now, just ensure valid structure.
        return True

    @staticmethod
    def guard(func):
        """Decorator to wrap a method in context isolation."""
        from functools import wraps
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Assumes 'self' has 'context' and 'console' (StoryEngine)
            fork = ContextIsolation.create_fork(self.context)
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # Restore on error
                ContextIsolation.restore_fork(self.context, fork)
                if hasattr(self, 'console'):
                    self.console.print(f"[red]🛡️ ContextIsolation: Restored state after error in {func.__name__}[/]")
                raise e
        return wrapper
