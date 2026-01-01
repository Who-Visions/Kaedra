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

# ══════════════════════════════════════════════════════════════════════════════
# GCP CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "69017097813")
LOCATION = os.getenv("KAEDRA_LOCATION", "us-central1")
MODEL_LOCATION = "global" # Gemini 3 Preview models require global endpoint
AGENT_RESOURCE_NAME = os.getenv(
    "KAEDRA_AGENT_RESOURCE",
    "projects/69017097813/locations/us-central1/reasoningEngines/9098403744265011200"
)

# ══════════════════════════════════════════════════════════════════════════════
# LIFX SMART LIGHTS CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LIFX_TOKEN = os.getenv("LIFX_TOKEN", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

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
    "flash": "gemini-3-flash-preview",         # Latest Flash V3 (Preview)
    "pro": "gemini-3-pro-preview",             # Latest Pro V3 (Preview)
    "ultra": "gemini-3-pro-preview",           # Using Pro V3 for Ultra slot
    "tts-flash": "gemini-2.5-flash-preview-tts:Kore", # Gemini 2.5 Flash TTS (Updated)
    "tts-flash-lite": "gemini-2.5-flash-preview-tts:Kore", # Fallback to Flash for now
    "tts-pro": "gemini-2.5-pro-preview-tts:Aoede",     # Gemini 2.5 Pro TTS (Updated)
    "tts": "gemini-2.5-flash-preview-tts:Kore",        # Default to Native Gemini 2.5
    "chirp-kore": "en-US-Chirp3-HD-Kore",      # Chirp 3 HD (US, Female) - Fast Stream
    "hifi-kore": "gemini-2.5-flash-preview-tts:Kore", # High Fidelity (24kHz)
    "hifi-pro": "gemini-2.5-pro-preview-tts:Aoede",    # Ultra High Detail (24kHz)
    "lite-kore": "gemini-2.5-flash-lite-preview-tts:Kore", # Cost Efficient HiFi
    "chirp-leda": "en-US-Chirp3-HD-Leda",      # Chirp 3 HD (US, Female)
    "chirp-zephyr": "en-US-Chirp3-HD-Zephyr",  # Chirp 3 HD (US, Female)
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
        return f"{cls.NEON_PINK}[KAEDRA]{cls.RESET}"
    
    @classmethod
    def blade_tag(cls) -> str:
        return f"{cls.NEON_RED}[BLADE]{cls.RESET}"
    
    @classmethod
    def nyx_tag(cls) -> str:
        return f"{cls.SKY_BLUE}[NYX]{cls.RESET}"
    
    @classmethod
    def system_tag(cls) -> str:
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
    "Did you know octopuses have three hearts? Two for the gills, one for the rest. Kinda like how I got multiple cores runnin'.",
    "Honey never spoils. Archaeologists found that stuff in tombs, still good. My memory like that too.",
    "Wombat poop is cube-shaped. Nature wild, ain't it?",
    "Bananas are berries, but strawberries ain't. The classification system is messed up, just like some of this legacy code.",
]
