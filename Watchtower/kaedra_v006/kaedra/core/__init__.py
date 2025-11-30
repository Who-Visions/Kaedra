"""KAEDRA Core - Configuration, routing, and version metadata."""

from .version import __version__, __codename__
from .config import Colors, MODELS, LOCATION, PROJECT_ID
from .router import ResponseRouter, Response, get_router

__all__ = [
    '__version__', '__codename__',
    'Colors', 'MODELS', 'LOCATION', 'PROJECT_ID',
    'ResponseRouter', 'Response', 'get_router'
]
