"""
StoryEngine UI Components
Console, theme, highlighter, and logging setup.
"""
import logging
import time
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from rich.logging import RichHandler
from rich.panel import Panel

# === STORY HIGHLIGHTER (ELITE) ===
class StoryHighlighter(RegexHighlighter):
    """Deep narrative highlighter for immersive chat."""
    base_style = "story."
    highlights = [
        # Entities
        r"(?P<entity>\b(Kaedra|Dave|Xoah|Gorr|Blade|Narrator|Aether)\b)",
        # Specialized Tech
        r"(?P<tech>\b(System|AI|Notion|LIFX|Gemini|Flash|Pro|Engine|Vertex|Aura|Neural)\b)",
        # Emotional States / Stats
        r"(?P<stat>\b(Fear|Rage|Hope|Desire|Tension|Emotion|Momentum|Coherence|Entropy)\b)",
        # Cinematic Actions
        r"(?P<action>\b(Zoom|Freeze|Escalate|Calm|Rewind|Bridge|Shift|Next|Transition)\b)",
        # Mars / Lore Context
        r"(?P<lore>\b(Mars|Olympus Mons|Tharsis|Caldera|Martian|Crimson|Dust|Low-G|Valles Marineris)\b)",
        # Dialogue
        r"(?P<quote>\"[^\"]*\")",
        # Engine Modes
        r"(?P<mode>\[(?:NORMAL|FREEZE|ZOOM|ESCALATE|GOD|DIRECTOR|SHIFT_POV|REWIND)\])",
        # Thought Signatures
        r"(?P<thought>\{[^}]*\})",
    ]

# === PREMIUM THEME ===
# Using hex codes for a "Visions" aesthetic
THEME = Theme({
    "story.entity": "bold #D700FF",    # Vivid Magenta
    "story.tech": "#00E5FF",           # Neon Cyan
    "story.stat": "bold italic #FFD700", # Gold
    "story.action": "bold underline #FFFFFF",
    "story.lore": "bold #FF4500",      # Deep Orange (Martian)
    "story.quote": "italic #76FF03",   # Neon Green
    "story.mode": "bold reverse #00E5FF",
    "story.thought": "dim #B0BEC5",    # Soft Blue-Grey
    "markdown.code": "bold #82B1FF",
    "markdown.h1": "bold #D700FF",
    "markdown.h2": "bold #00E5FF",
    "repr.number": "bold #FFD700",
})

# === CONSOLE ===
console = Console(theme=THEME, highlighter=StoryHighlighter())

# === LOGGING ===
logging.getLogger("google.generativeai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)]
)
log = logging.getLogger("kaedra")

from rich.text import Text

def render_hud(mode: str, scene: int, pov: str, tension: float, emotions: dict) -> Text:
    """Subtle, non-dashboard HUD for Elite Chat."""
    # Tension Bar (Minimalist but pulsing)
    bar_width = 15
    filled = int(tension * bar_width)
    pulse = "!" if (time.time() % 1.0 > 0.5 and tension > 0.8) else "░"
    bar = "█" * filled + pulse * (bar_width - filled)
    
    # Dom Emotion
    if emotions:
        dom_emo = max(emotions, key=emotions.get).upper()
        dom_val = emotions[dom_emo.lower()]
    else:
        dom_emo, dom_val = "NULL", 0.0
        
    hud_line = f" [bold cyan]{mode}[/] | [bold white]SCENE {scene}[/] | [bold magenta]{pov}[/] | [bold yellow]TENSION:[/] [red]{bar}[/] [bold yellow]{tension:.2f}[/] | [dim]{dom_emo} {dom_val:.2f}[/]"
    
    return Text.from_markup(hud_line)
