"""KAEDRA Interface - CLI and TUI entry points."""

from .cli import main as cli_main

try:
    from .rich_cli import main as rich_cli_main
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    rich_cli_main = cli_main

__all__ = ['cli_main', 'rich_cli_main', 'RICH_AVAILABLE']
