"""KAEDRA Services - Memory, Logging, Prompt handling, Web fetching, and Video generation."""

try:
    from .memory import MemoryService, MemoryEntry
    MEMORY_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"[!] MemoryService unavailable: {e}")
    MEMORY_AVAILABLE = False
    MemoryService = None
    MemoryEntry = None

from .logging import LoggingService, SessionInfo
from .prompt import PromptService, PromptResult
from .web import WebService, WebPage

try:
    from .video import VideoService, VideoResult
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    VideoService = None
    VideoResult = None

__all__ = [
    'MemoryService', 'MemoryEntry',
    'LoggingService', 'SessionInfo',
    'PromptService', 'PromptResult',
    'WebService', 'WebPage',
]

if VIDEO_AVAILABLE:
    __all__.extend(['VideoService', 'VideoResult'])
