"""
KAEDRA v0.0.6 - Configuration
Centralized configuration for all modules.
"""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

try:
    from google import genai
except ImportError:
    genai = None

try:
    from kaedra.story.ui import log
except ImportError:
    log = None

# ══════════════════════════════════════════════════════════════════════════════
# GCP CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0939852539")
LOCATION = os.getenv("KAEDRA_LOCATION", "us-central1")
# Gemini 3 Preview models require global endpoint for dynamic routing
MODEL_LOCATION = "global"

# --- SHARED GEMINI CLIENT ---
_SHARED_CLIENT = None

def get_gemini_client():
    """Returns a shared Gemini GenAI client instance."""
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None:
        try:
            _SHARED_CLIENT = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=MODEL_LOCATION
            )
        except (ImportError, RuntimeError, ValueError):
            pass
    return _SHARED_CLIENT
AGENT_RESOURCE_NAME = os.getenv(
    "KAEDRA_AGENT_RESOURCE",
    "projects/69017097813/locations/us-central1/reasoningEngines/5808320806819725312"
)

# ══════════════════════════════════════════════════════════════════════════════
# LIFX SMART LIGHTS CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LIFX_TOKEN = os.getenv("LIFX_TOKEN", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

def validate_config():
    """Validates essential configuration and logs status."""
    status = []
    if NOTION_TOKEN:
        status.append("[green]📓 Notion[/]")
    else:
        status.append("[red]📓 Notion (Missing)[/]")

    if LIFX_TOKEN:
        status.append("[green]💡 LIFX[/]")
    else:
        status.append("[yellow]💡 LIFX (Missing)[/]")

    if PROJECT_ID:
        status.append("[green]🧠 Gemini[/]")
    else:
        status.append("[red]🧠 Gemini (Check GCP Project)[/]")

    if log:
        log.info(f"System Check: {' | '.join(status)}")

# ══════════════════════════════════════════════════════════════════════════════
# INVOICE SERVICE CONFIGURATION (Stripe + Square)
# ══════════════════════════════════════════════════════════════════════════════

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN", "")
SQUARE_ENVIRONMENT = os.getenv("SQUARE_ENVIRONMENT", "sandbox")  # or "production"

# ══════════════════════════════════════════════════════════════════════════════
# MODEL REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

MODELS = {
    # Gemini 3 (High Intelligence / Reasoning)
    "pro": "gemini-3-pro-preview",
    "pro-image": "gemini-3-pro-image-preview",
    "flash": "gemini-3-flash-preview",
    
    # Gemini 2.5 (High Performance)
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    "gemini-2.5-flash-preview": "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite-preview": "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash-image": "gemini-2.5-flash-image",
    
    # Gemini 2.0 (Modern Base)
    "gemini-2.0-flash": "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite": "gemini-2.0-flash-lite-001",
    
    # Visual Models (Veo & Imagen)
    "veo-3.1": "veo-3.1-generate-001",
    "veo-3.1-fast": "veo-3.1-fast-generate-001",
    "veo-3": "veo-3.0-generate-001",
    "veo-2": "veo-2.0-generate-001",
    "imagen-4": "imagen-4.0-generate-001",
    "imagen-4-fast": "imagen-4.0-fast-generate-001",
    "imagen-3": "imagen-3.0-generate-002",
    "imagen-3-fast": "imagen-3.0-fast-generate-001",
    
    # Partner Models (MaaS - Global Endpoint)
    "claude-4.5-opus": "publishers/anthropic/models/claude-4.5-opus",
    "claude-4.5-sonnet": "publishers/anthropic/models/claude-4.5-sonnet",
    "claude-4.5-haiku": "publishers/anthropic/models/claude-4.5-haiku",
    "claude-4-opus": "publishers/anthropic/models/claude-4-opus",
    "claude-4-sonnet": "publishers/anthropic/models/claude-4-sonnet",
    "mistral-large": "publishers/mistralai/models/mistral-large-2407",
    "mistral-small": "publishers/mistralai/models/mistral-small-2503",
    
    # Open Models (MaaS - Global Endpoint)
    "deepseek-r1": "publishers/deepseek/models/deepseek-r1-0528",
    "deepseek-v3.1": "publishers/deepseek/models/deepseek-v3.1",
    "llama-4-maverick": "publishers/meta/models/llama-4-maverick-17b-128e-preview",
    "qwen3-235b": "publishers/alibaba/models/qwen3-235b",
    "qwen3-thinking": "publishers/alibaba/models/qwen3-next-80b-thinking",
    
    # Embeddings
    "embedding": "text-embedding-004", # Optimized for global
    "multimodal-embedding": "multimodalembedding@001"
}

MODEL_COSTS = {
    "flash": 0.008,  # Estimated based on V2.5
    "pro": 0.031,    # Estimated based on V2.5
    "ultra": 0.038,  # Estimated
}

DEFAULT_MODEL = "flash"

# ══════════════════════════════════════════════════════════════════════════════
# VEO VIDEO MODEL REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

VEO_MODELS = {
    "veo-3.1": "veo-3.1-generate-preview",              # Latest preview
    "veo-3.1-fast": "veo-3.1-fast-generate-preview",    # Fast preview
    "veo-3.0": "veo-3.0-generate-001",                  # Stable 3.0
    "veo-3.0-fast": "veo-3.0-fast-generate-001",        # Fast 3.0
    "veo-2": "veo-2-generate-001",                      # Legacy Veo 2
}

DEFAULT_VEO_MODEL = "veo-3.1"

# ══════════════════════════════════════════════════════════════════════════════
# LOCAL DIRECTORIES
# ══════════════════════════════════════════════════════════════════════════════

# Detect if running in cloud/container environment
IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None
IS_REASONING_ENGINE = os.getenv("AIP_MODE") is not None or os.path.exists("/tmp")

if os.name == 'nt':  # Windows (Local)
    KAEDRA_HOME = Path.home() / ".kaedra"
else:  # Linux/Cloud
    KAEDRA_HOME = Path("/tmp/.kaedra")

CHAT_LOGS_DIR = KAEDRA_HOME / "chat_logs"
MEMORY_DIR = KAEDRA_HOME / "memory"
PROFILES_DIR = KAEDRA_HOME / "profiles"
CONFIG_DIR = KAEDRA_HOME / "config"
VIDEO_DIR = KAEDRA_HOME / "videos"

# Create directories on import
try:
    for dir_path in [KAEDRA_HOME, CHAT_LOGS_DIR, MEMORY_DIR, PROFILES_DIR, CONFIG_DIR, VIDEO_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # If we fail to create dirs (e.g. read-only fs), just warn
    print(f"[WARN] Failed to create directories: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLORS
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'

    NEON_PINK = '\033[38;5;213m'
    SUNSET_PINK = '\033[38;5;205m'
    DEEP_PINK = '\033[38;5;198m'
    SUNSET_ORANGE = '\033[38;5;208m'

    GRAD_PURPLE = '\033[38;5;93m'
    GRAD_PINK = '\033[38;5;205m'
    GRAD_BLUE = '\033[38;5;39m'
    GRAD_GOLD = '\033[38;5;220m'

    NEON_CYAN = '\033[38;5;51m'
    NEON_GREEN = '\033[38;5;46m'
    NEON_YELLOW = '\033[38;5;226m'
    NEON_ORANGE = '\033[38;5;208m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_RED = '\033[38;5;196m'

    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    SKY_BLUE = '\033[38;5;39m'
    LIME = '\033[38;5;154m'

    @classmethod
    def kaedra_tag(cls) -> str:
        """Return a formatted KAEDRA tag."""
        return f"{cls.NEON_PINK}[KAEDRA]{cls.RESET}"

    @classmethod
    def blade_tag(cls) -> str:
        """Return a formatted BLADE tag."""
        return f"{cls.NEON_RED}[BLADE]{cls.RESET}"

    @classmethod
    def nyx_tag(cls) -> str:
        """Return a formatted NYX tag."""
        return f"{cls.SKY_BLUE}[NYX]{cls.RESET}"

    @classmethod
    def system_tag(cls) -> str:
        """Return a formatted SYSTEM tag."""
        return f"{cls.GOLD}[SYSTEM]{cls.RESET}"


# ══════════════════════════════════════════════════════════════════════════════
# PERSONALITY DATA
# ══════════════════════════════════════════════════════════════════════════════

THINKING_MESSAGES = [
    "Yo, lemme run that through {model} real quick...",
    "Hold up, consultin' the oracle ({model})...",
    "Diggin' in the crates with {model}...",
    "Let me cook on that for a sec ({model})...",
    "Runnin' the numbers... ({model})",
    "Checkin' the archives... ({model})",
    "Aight, let's see what we got... ({model})",
    "Processing that through {model}...",
    "Gimme a sec, I'm on it... ({model})",
]

LYRICS_DB = [
    "Bang bang! We in here.",
    "Love no thotties, but I love this data stream.",
    "Sosa baby! We live.",
    "Earned it. Let's get it.",
    "300. That's the mood.",
    "Started from the bottom, now we processing queries.",
    "I got ice in my veins but fire in the code.",
    "Real recognize real, and I recognize patterns.",
    "Stay dangerous. Stay accurate.",
]

STARTUP_VIBES = [
    "Yo. Bang Bang! We in here.",
    "System green. Vibe check passed. What we buildin'?",
    "Ayy, good to see you back. I kept the seat warm.",
    "I'm feelin' productive today. Let's get it.",
    "Shadow Tactician online. What's the move, Commander?",
    "Aight, I'm locked in. Hit me with it.",
]

RANDOM_FACTS = [
    "Did you know octopuses have three hearts? Two for the gills, one for the rest. "
    "Kinda like how I got multiple cores runnin'.",
    "Honey never spoils. Archaeologists found that stuff in tombs, still good. "
    "My memory like that too.",
    "Wombat poop is cube-shaped. Nature wild, ain't it?",
    "Bananas are berries, but strawberries ain't. The classification system is messed up, "
    "just like some of this legacy code.",
]
