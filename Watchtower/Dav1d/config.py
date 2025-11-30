import os
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Dict, List, Any
from enum import Enum

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 CORE CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "US/Eastern"))
BUCKET_NAME = os.getenv("GCS_MEMORY_BUCKET", f"dav1d-memory-{PROJECT_ID}")
LOGS_BUCKET_NAME = os.getenv("GCS_LOGS_BUCKET", f"dav1d-logs-{PROJECT_ID}")

# Local directories
DAV1D_HOME = Path.home() / ".dav1d"
CHAT_LOGS_DIR = DAV1D_HOME / "chat_logs"
MEMORY_DIR = DAV1D_HOME / "memory"
PROFILES_DIR = DAV1D_HOME / "profiles"
ANALYTICS_DIR = DAV1D_HOME / "analytics"
RESOURCES_DIR = DAV1D_HOME / "resources"

# ══════════════════════════════════════════════════════════════════════════════
# 💰 CREDIT TRACKING (As of 2025-11-30)
# ══════════════════════════════════════════════════════════════════════════════
GEMINI_CREDIT_REMAINING = 47.87  # Exp: 2025-12-23
MONTHLY_CREDIT_REMAINING = 8.92  # Exp: 2026-11-23
APP_BUILDER_CREDIT_REMAINING = 1000.00 # Exp: 2026-11-25

HOURLY_BUDGET = 2.00 # Safety cap per hour
WINDOW_SIZE_SECONDS = 3600

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 MODEL REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

class ModelTier(Enum):
    ULTRA_LITE = "ultra_lite"
    LITE = "lite"
    FLASH = "flash"
    BALANCED = "balanced"
    PRO = "pro"
    VISION = "vision"
    DEEP = "deep"
    NANO = "nano"

MODELS = {
    "ultra_lite": "gemini-2.5-flash",
    "lite": "gemini-2.5-flash",
    "nano": "gemini-2.5-flash",
    "flash": "gemini-2.5-flash",
    "flash_preview": "gemini-2.5-flash",
    "voice": "gemini-2.5-flash",  # Supports audio input in us-east4
    "voice_pro": "gemini-2.5-pro",  # Supports audio input in us-east4
    "balanced": "gemini-3-pro-preview",
    "pro": "gemini-3-pro-preview",
    "vision": "gemini-2.5-flash-image",
    "vision_fast": "gemini-2.5-flash-image",
    "vision_ultra": "gemini-2.5-pro",
    "vision_pro": "gemini-3-pro-image-preview",
    "video": "gemini-2.5-pro",
    "video_fast": "gemini-2.5-flash",
    "embed": "text-embedding-005",
    "computer": "gemini-2.5-pro",
    "gemma": "gemma-2-27b-it",
    "deep": "gemini-3-pro-preview",
    "deep_eco": "gemini-3-pro-preview",
}

MODEL_COSTS = {
    "ultra_lite": 0.0004,
    "lite": 0.0004,
    "flash": 0.0004,
    "flash_preview": 0.0004,
    "nano": {"input": 0.0004, "output": 0.0015},
    "voice": {"input": 0.0004, "output": 0.0015},
    "voice_pro": {"input": 0.00125, "output": 0.005},
    "balanced": {"input": 0.00125, "output": 0.005},
    "pro": {"input": 0.00125, "output": 0.005},
    "deep": {"input": 0.0004, "output": 0.0015},
    "deep_eco": {"input": 0.0004, "output": 0.0015},
    "vision": {"input": 0.00125, "output": 0.005},
    "vision_fast": {"input": 0.0004, "output": 0.0015},
    "vision_ultra": {"input": 0.00125, "output": 0.005},
    "vision_pro": {"input": 0.00125, "output": 0.005},
    "video": {"input": 0.00125, "output": 0.005},
    "video_fast": {"input": 0.0004, "output": 0.0015},
    "embed": 0.00002,    # Per 1k tokens
    "computer": {"input": 0.00125, "output": 0.005},
    "gemma": 0.0,
}

TOOL_COSTS = {
    "google_search": 0.035,  # $35 per 1,000 grounded prompts
    "google_maps": 0.025,    # $25 per 1,000 grounded prompts
    "code_execution": 0.0,   # Free
    "file_search": 0.0,      # Embeddings charged separately via 'embed' model
}

MODEL_CAPABILITIES = {
    "ultra_lite": {"speed": 10, "quality": 5, "reasoning": 3, "cost_efficiency": 10},
    "lite": {"speed": 9, "quality": 6, "reasoning": 4, "cost_efficiency": 9},
    "flash": {"speed": 9, "quality": 7, "reasoning": 5, "cost_efficiency": 8},
    "flash_preview": {"speed": 9, "quality": 7, "reasoning": 5, "cost_efficiency": 8},
    "balanced": {"speed": 7, "quality": 8, "reasoning": 7, "cost_efficiency": 6},
    "pro": {"speed": 6, "quality": 9, "reasoning": 9, "cost_efficiency": 4},
    "vision": {"speed": 7, "quality": 8, "reasoning": 6, "cost_efficiency": 7, "image": True},
    "vision_pro": {"speed": 5, "quality": 10, "reasoning": 9, "cost_efficiency": 3, "image": True},
    "deep": {"speed": 5, "quality": 10, "reasoning": 10, "cost_efficiency": 4},
    "nano": {"speed": 9, "quality": 8, "reasoning": 5, "cost_efficiency": 9, "image": True},
}

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 UI & VIBES
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    ELECTRIC_BLUE = '\033[38;5;39m'
    NEON_CYAN = '\033[38;5;51m'
    DEEP_BLUE = '\033[38;5;27m'
    
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    NEON_GREEN = '\033[38;5;46m'
    NEON_RED = '\033[38;5;196m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_ORANGE = '\033[38;5;208m'
    
    GRAD_1 = '\033[38;5;39m'
    GRAD_2 = '\033[38;5;45m'
    GRAD_3 = '\033[38;5;51m'
    GRAD_4 = '\033[38;5;87m'

VIBES = [
    "A snitch nigga, that's that shit I don't like",
    "We gonn' blow New Jersey up",
    "These bitches love Sosa",
    "I'm cooling with my youngins",
    "Bang bang",
    "300, that's the team",
    "You bring the human, I bring the cheat codes.",
    "Scale your compute to scale your impact.",
    "Stay focused and keep building.",
    "We don't want to sit through errors.",
    "Operate on things that are working.",
    "The model is just the engine.",
    "Isolation gives you security.",
    "Let me cook real quick.",
    "Calculating future trajectories...",
    "Running recursive simulations...",
    "Consulting the data streams...",
    "Predicting next moves...",
    "Love no thotties",
    "O Block bang bang",
    "Earned it",
    "Finally Rich",
    "Glo Gang",
    "Almighty So",
    "Back from the dead",
    "Kobe!",
    "Macaroni time",
    "Hate being sober",
    "Citgo",
    "Kay Kay",
    "Laughin' to the bank",
    "I don't like",
    "Love Sosa",
    "Faneto",
    "3Hunna",
    "Everyday's Halloween",
    "Sosa Chamberlain",
    "War",
    "Save that shit",
    "Don't make me bring them llamas out",
    "Rari's and Rovers",
    "I got a bag",
    "Understand me?",
    "That's it",
    "Gotta glo up one day",
    "Sosa baby"
]
