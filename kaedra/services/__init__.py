"""KAEDRA Services - Memory, Logging, Prompt handling, Web fetching, Video generation, and Vector search."""

from .memory import MemoryService, MemoryEntry
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

try:
    from .vector_store import BigQueryVectorStore, get_vector_store
    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    BigQueryVectorStore = None
    get_vector_store = None

__all__ = [
    'MemoryService', 'MemoryEntry',
    'LoggingService', 'SessionInfo',
    'PromptService', 'PromptResult',
    'WebService', 'WebPage',
]

if VIDEO_AVAILABLE:
    __all__.extend(['VideoService', 'VideoResult'])

if VECTOR_STORE_AVAILABLE:
    __all__.extend(['BigQueryVectorStore', 'get_vector_store'])

