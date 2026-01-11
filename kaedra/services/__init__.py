"""KAEDRA Services - Memory, Logging, Prompt handling, Web fetching, and Visual generation."""

try:
    from .memory import MemoryService, MemoryEntry
    MEMORY_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"[!] MemoryService unavailable: {e}")
    MEMORY_AVAILABLE = False
    MemoryService = None
    MemoryEntry = None

from .kaedra_logging import LoggingService, SessionInfo
from .prompt import PromptService, PromptResult
from .web import WebService, WebPage

try:
    from .visual import VisualService, VisualResult
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    VisualService = None
    VisualResult = None

__all__ = [
    'MemoryService', 'MemoryEntry',
    'LoggingService', 'SessionInfo',
    'PromptService', 'PromptResult',
    'WebService', 'WebPage',
]

if VIDEO_AVAILABLE:
    __all__.extend(['VisualService', 'VisualResult'])
