"""
KAEDRA v0.0.6 - Colors and Themes
ANSI color codes and theme definitions.
"""

from dataclasses import dataclass
from typing import Dict


class Colors:
    """ANSI color codes."""
    
    # Reset
    RESET = '\033[0m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    HIDDEN = '\033[8m'
    STRIKETHROUGH = '\033[9m'
    
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # 256-color neon palette
    NEON_PINK = '\033[38;5;198m'
    NEON_CYAN = '\033[38;5;51m'
    NEON_GREEN = '\033[38;5;46m'
    NEON_YELLOW = '\033[38;5;226m'
    NEON_ORANGE = '\033[38;5;208m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_RED = '\033[38;5;196m'
    NEON_BLUE = '\033[38;5;33m'
    
    # Special colors
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    SKY_BLUE = '\033[38;5;39m'
    LIME = '\033[38;5;154m'
    CORAL = '\033[38;5;209m'
    LAVENDER = '\033[38;5;183m'
    
    @classmethod
    def rgb(cls, r: int, g: int, b: int) -> str:
        """Generate 24-bit true color code."""
        return f'\033[38;2;{r};{g};{b}m'
    
    @classmethod
    def bg_rgb(cls, r: int, g: int, b: int) -> str:
        """Generate 24-bit true color background."""
        return f'\033[48;2;{r};{g};{b}m'


@dataclass
class Theme:
    """Color theme for KAEDRA interface."""
    
    name: str
    
    # Agent colors
    kaedra: str
    blade: str
    nyx: str
    
    # UI colors
    system: str
    user: str
    prompt: str
    error: str
    warning: str
    success: str
    info: str
    
    # Content colors
    memory: str
    thinking: str
    highlight: str
    
    @classmethod
    def cyberpunk(cls) -> "Theme":
        """Default cyberpunk theme."""
        return cls(
            name="cyberpunk",
            kaedra=Colors.NEON_PINK,
            blade=Colors.NEON_RED,
            nyx=Colors.SKY_BLUE,
            system=Colors.GOLD,
            user=Colors.NEON_CYAN,
            prompt=Colors.NEON_GREEN,
            error=Colors.NEON_RED,
            warning=Colors.NEON_ORANGE,
            success=Colors.NEON_GREEN,
            info=Colors.NEON_CYAN,
            memory=Colors.NEON_PURPLE,
            thinking=Colors.DIM,
            highlight=Colors.NEON_YELLOW
        )
    
    @classmethod
    def minimal(cls) -> "Theme":
        """Minimal theme with less color."""
        return cls(
            name="minimal",
            kaedra=Colors.BRIGHT_MAGENTA,
            blade=Colors.BRIGHT_RED,
            nyx=Colors.BRIGHT_BLUE,
            system=Colors.BRIGHT_YELLOW,
            user=Colors.BRIGHT_GREEN,
            prompt=Colors.WHITE,
            error=Colors.RED,
            warning=Colors.YELLOW,
            success=Colors.GREEN,
            info=Colors.CYAN,
            memory=Colors.MAGENTA,
            thinking=Colors.DIM,
            highlight=Colors.BOLD
        )
    
    @classmethod
    def matrix(cls) -> "Theme":
        """Matrix-inspired green theme."""
        return cls(
            name="matrix",
            kaedra=Colors.BRIGHT_GREEN,
            blade=Colors.NEON_GREEN,
            nyx=Colors.LIME,
            system=Colors.NEON_GREEN,
            user=Colors.WHITE,
            prompt=Colors.NEON_GREEN,
            error=Colors.RED,
            warning=Colors.YELLOW,
            success=Colors.NEON_GREEN,
            info=Colors.LIME,
            memory=Colors.BRIGHT_GREEN,
            thinking=Colors.DIM,
            highlight=Colors.BOLD + Colors.NEON_GREEN
        )
    
    def colorize(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{Colors.RESET}"
    
    def agent(self, name: str) -> str:
        """Get color for an agent."""
        return {
            "kaedra": self.kaedra,
            "blade": self.blade,
            "nyx": self.nyx
        }.get(name.lower(), self.system)


# Default theme
DEFAULT_THEME = Theme.cyberpunk()


def get_theme(name: str) -> Theme:
    """Get a theme by name."""
    themes = {
        "cyberpunk": Theme.cyberpunk,
        "minimal": Theme.minimal,
        "matrix": Theme.matrix
    }
    return themes.get(name, Theme.cyberpunk)()
