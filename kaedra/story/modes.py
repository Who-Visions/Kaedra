"""
StoryEngine Mode Transitions
Handles side effects when engine modes change.
"""
from typing import Dict, List, Tuple, Callable, Optional, TYPE_CHECKING

from .config import Mode
from .ui import log

if TYPE_CHECKING:
    from .engine import StoryEngine


class ModeTransition:
    """Handles side effects when modes change."""
    
    def __init__(self, engine: 'StoryEngine'):
        self.engine = engine
        self.hooks: Dict[Tuple[Optional[Mode], Optional[Mode]], List[Callable]] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default transition behaviors."""
        # Escalate entry: spike fear/rage
        self.register(None, Mode.ESCALATE, self._on_escalate_enter)
        # Freeze entry: snapshot emotional state
        self.register(None, Mode.FREEZE, self._on_freeze_enter)
        # God exit: clear temp context
        self.register(Mode.GOD, None, self._on_god_exit)
        # Any → Normal: decay boost
        self.register(None, Mode.NORMAL, self._on_normal_enter)
        
    def register(self, from_mode: Optional[Mode], to_mode: Optional[Mode], hook: Callable):
        """Register a transition hook. None = wildcard."""
        key = (from_mode, to_mode)
        if key not in self.hooks:
            self.hooks[key] = []
        self.hooks[key].append(hook)
    
    def execute(self, from_mode: Mode, to_mode: Mode):
        """Execute all matching hooks for a transition."""
        # Check specific transition
        for key in [(from_mode, to_mode), (None, to_mode), (from_mode, None)]:
            if key in self.hooks:
                for hook in self.hooks[key]:
                    try:
                        hook(from_mode, to_mode)
                    except Exception as e:
                        log.warning(f"Hook failed: {e}")
    
    def _on_escalate_enter(self, from_mode: Mode, to_mode: Mode):
        self.engine.emotions.pulse("fear", 0.3)
        self.engine.emotions.pulse("rage", 0.2)
        self.engine.tension.target = min(1.0, self.engine.tension.current + 0.3)
        
    def _on_freeze_enter(self, from_mode: Mode, to_mode: Mode):
        self.engine._frozen_emotion_state = self.engine.emotions.serialize()
        
    def _on_god_exit(self, from_mode: Mode, to_mode: Mode):
        # God mode queries don't affect narrative state
        pass
        
    def _on_normal_enter(self, from_mode: Mode, to_mode: Mode):
        # Slight hope boost when returning to normal
        self.engine.emotions.pulse("hope", 0.1)
