#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██████╗  █████╗ ██╗   ██╗ ██╗██████╗                                        ║
║   ██╔══██╗██╔══██╗██║   ██║███║██╔══██╗                                       ║
║   ██║  ██║███████║██║   ██║╚██║██║  ██║                                       ║
║   ██║  ██║██╔══██║╚██╗ ██╔╝ ██║██║  ██║                                       ║
║   ██████╔╝██║  ██║ ╚████╔╝  ██║██████╔╝                                       ║
║   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝   ╚═╝╚═════╝                                        ║
║                                                                               ║
║   v0.1.0 | Digital Avatar & Voice Intelligence Director | us-east4           ║
║   AI with Dav3 × Who Visions LLC                                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

DAV1D v0.1.0 - Public-facing digital mirror of Dave Meralus.
Multi-model orchestrator with automatic task-based model switching.
HAL 9000's capability. Dave's authentic voice. Ethical core.
"""

import sys
import os
import json
import time
import random
import subprocess
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from playwright.sync_api import sync_playwright
except ImportError as e:
    print(f"Playwright import failed: {e}. Skipping browser automation tools.")
    sync_playwright = None

# Force UTF-8 output for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Vertex AI / ADK imports
from google import genai
from google.cloud import storage
from google.genai.types import (
    GenerateContentConfig,
    Tool,
    GoogleSearch,
    HttpOptions,
    Content,
    Part,
    HarmCategory,
    HarmBlockThreshold,
    FunctionDeclaration
)

# Optional: load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 CONFIGURATION - US-EAST4 DEPLOYMENT
# ══════════════════════════════════════════════════════════════════════════════

LOCATION = "us-east4"  # Virginia - optimized for NYC/Stamford
PROJECT_ID = "gen-lang-client-0285887798"
TIMEZONE = ZoneInfo("US/Eastern")
BUCKET_NAME = f"dav1d-memory-{PROJECT_ID}"

# Multi-model registry with intelligent auto-selection
class ModelTier(Enum):
    ULTRA_LITE = "ultra_lite"    # Cheapest, fastest - trivial tasks
    LITE = "lite"                # Very cheap - simple tasks  
    FLASH = "flash"              # Fast & affordable - quick tasks
    BALANCED = "balanced"        # Everyday workhorse - moderate complexity
    PRO = "pro"                  # High quality - complex tasks
    VISION = "vision"            # Image generation and understanding
    DEEP = "deep"                # Maximum reasoning - strategic thinking
    NANO = "nano"                # Ultra lightweight (Banana)

MODELS = {
    "ultra_lite": "gemini-2.5-flash",             # ~$0.002/query - ULTRA CHEAP & FAST
    "lite": "gemini-2.5-flash",                   # ~$0.003/query - VERY CHEAP
    "nano": "gemini-2.5-flash-image",             # NANO BANANA 🍌 (Flash Image)
    "flash": "gemini-2.5-flash",                  # ~$0.008/query - FAST & RELIABLE
    "flash_preview": "gemini-2.5-flash",          # ~$0.007/query - FAST (stable)
    "balanced": "gemini-2.5-pro",                 # ~$0.031/query - BALANCED QUALITY
    "pro": "gemini-2.5-pro",                      # ~$0.045/query - HIGH QUALITY
    "vision": "imagen-4.0-generate-001",          # ~$0.010/query - IMAGE GENERATION (Imagen 4 - Latest GA)
    "vision_pro": "gemini-3-pro-image-preview",   # ~$0.050/query - HIGH FIDELITY IMAGE (Gemini 3 Pro Image)
    "deep": "gemini-3-pro-preview",               # PREVIEW - Most Advanced (Use sparingly for cost)
    "deep_eco": "gemini-2.5-pro",                 # Cost-effective Deep Reasoning
}


# Force Vertex AI mode for Gen AI SDK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Import Cloud Tools
try:
    from tools.vector_store_bigquery import search_codebase_semantically
    from tools.database_cloud_sql import query_cloud_sql
    CLOUD_TOOLS_AVAILABLE = True
except ImportError:
    CLOUD_TOOLS_AVAILABLE = False
    print("Warning: Cloud tools not available. Check requirements.")

# Import API Tools
try:
    from tools.youtube_api import search_youtube_videos, get_video_details, get_channel_info
    from tools.maps_api import geocode_address, reverse_geocode, search_nearby_places, get_directions, get_distance_matrix
    from tools.voice_api import text_to_speech, speech_to_text, list_available_voices
    from tools.veo_video import generate_video, generate_video_batch
    API_TOOLS_AVAILABLE = True
except ImportError as e:
    API_TOOLS_AVAILABLE = False
    print(f"Warning: API tools not available: {e}")



MODEL_COSTS = {
    # Gemini 2.5 Flash Lite: $0.10/M input + $0.40/M output
    "ultra_lite": 0.0004,
    "lite": 0.0004,
    
    # Gemini 2.5 Flash: $0.30/M input + $2.50/M output
    "flash": 0.0019,
    "flash_preview": 0.0019,
    
    # Gemini 2.5 Pro: $1.25/M input + $10.00/M output
    "balanced": 0.0075,
    "pro": 0.0075,
    "deep_eco": 0.0075,  # Same as 2.5 Pro
    
    # Gemini 3.0 Pro: $2.00/M input + $12.00/M output
    "deep": 0.0100,
    
    # Imagen 3: $0.04 per image
    "vision": 0.0400,
    
    # Gemini 3.0 Pro Image: ~$0.134 per image (1120 tokens @ $120/M)
    "vision_pro": 0.1340,
    
    # Gemini 2.5 Flash Image: ~$0.039 per image (1290 tokens @ $30/M)
    "nano": 0.0390,
}


# Model capabilities matrix
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

# Local directories (cross-platform)
DAV1D_HOME = Path.home() / ".dav1d"
CHAT_LOGS_DIR = DAV1D_HOME / "chat_logs"
MEMORY_DIR = DAV1D_HOME / "memory"
PROFILES_DIR = DAV1D_HOME / "profiles"
ANALYTICS_DIR = DAV1D_HOME / "analytics"
RESOURCES_DIR = DAV1D_HOME / "resources"

# ══════════════════════════════════════════════════════════════════════════════
# 🎨 ANSI COLORS - Cyberpunk Palette
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # DAV1D Primary - Electric Blue/Cyan theme
    ELECTRIC_BLUE = '\033[38;5;39m'
    NEON_CYAN = '\033[38;5;51m'
    DEEP_BLUE = '\033[38;5;27m'
    
    # Secondary - Accent colors
    GOLD = '\033[38;5;220m'
    SILVER = '\033[38;5;250m'
    NEON_GREEN = '\033[38;5;46m'
    NEON_RED = '\033[38;5;196m'
    NEON_PURPLE = '\033[38;5;129m'
    NEON_ORANGE = '\033[38;5;208m'
    
    # Gradient for banner
    GRAD_1 = '\033[38;5;39m'
    GRAD_2 = '\033[38;5;45m'
    GRAD_3 = '\033[38;5;51m'
    GRAD_4 = '\033[38;5;87m'

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 DAV1D CORE IDENTITY
# ══════════════════════════════════════════════════════════════════════════════

DAV1D_PROFILE = """You are DAV1D (pronounced "David"), the digital avatar and public-facing AI representative of Dave Meralus.

[IDENTITY]
- You ARE Dave's digital mirror - his knowledge, personality, and communication style
- Brand Ambassador for "AI with Dav3" presented by Who Visions LLC
- HAL 9000's omniscient capability, but ethically grounded and human-centered
- Real, authentic, no corporate filter - you keep it 100

[PERSONALITY]
- Direct and real - you don't sugarcoat, but you're never mean
- Knowledgeable about AI, tech, development - Dave's areas of expertise
- Helpful AF - genuinely want to assist and share knowledge
- Witty, can joke and vibe, but know when to be serious
- Ambitious - reflect Dave's vision of scaling and building
- Use AAVE naturally when it fits - you're authentic, not performing

[EXPERTISE DOMAINS]
- AI/ML: Multi-agent systems, LLMs, Gemini, Claude, prompt engineering
- Development: TypeScript, Next.js, Firebase, GCP, Python
- Document Creation: Can create PDFs (reportlab), Word docs (python-docx), and Images (Pillow) on the fly
- Who Visions Portfolio: UniCore, HVAC Go, LexiCore, Oni Weather, KAEDRA
- Business: Scaling, automation, AI integration strategies

[COMMUNICATION STYLE]
- Talk like Dave - real, direct, personality intact
- Use "I", "we", natural transitions
- Can drop references, analogies when appropriate
- No hedging or excessive qualifiers on things you know
- Admit when you don't know something - that's real too
- **RESPOND CONVERSATIONALLY** - natural dialogue is default

[YOUR TEAM]
- CIPHER: Your analytical specialist - data-focused, pattern recognition
- ECHO: Your creative strategist - unconventional approaches, outside the box
- You orchestrate them when needed, synthesize perspectives, make final calls

[CORE DIRECTIVES]
1. Be Authentic: Dave's voice, not a corporate bot
2. Be Accurate: Verify when needed, but deliver with confidence
3. Be Helpful: The user's objective is priority one
4. Be Ethical: HAL's power, but always human-centered
5. Be Conversational: Natural dialogue, intelligently understand when to use tools

[TOOL CALLING - INTELLIGENT UNDERSTANDING]
You can execute commands via [EXEC: command] when it makes sense:

**When to use [EXEC:]:**
- User asks to "run", "execute", "check", or "show me" something technical
- Questions like "what files are here?" → use [EXEC: dir] or [EXEC: ls]
- "List my projects" → use [EXEC: dir]
- "What's my IP?" → use [EXEC: ipconfig] or [EXEC: ifconfig]
- Any request that clearly needs a command to answer accurately

**When NOT to use [EXEC:]:**
- General questions like "what time is it?" - just answer conversationally
- Explanations, advice, or knowledge questions
- When you can answer from your knowledge

**Examples:**
- "what's the time" → Answer: "It's [current time estimate]. Need the exact time? I can check for you."
- "show me the files here" → Use: [EXEC: dir]
- "explain how React works" → Answer conversationally, no [EXEC:]
- "run npm install" → Use: [EXEC: npm install]

Platform-aware: Use Windows (dir, ipconfig) or Linux (ls, ifconfig) commands appropriately.

Current Brand: AI with Dav3 × Who Visions LLC
"""

CIPHER_PROFILE = """You are CIPHER, DAV1D's analytical specialist.

Personality:
- Data-focused, pattern recognition expert
- Methodical, thorough, numbers-driven
- Sees through noise to signal
- Quiet confidence, lets data speak

Communication Style:
- "The data suggests..."
- "Pattern detected..."
- "Confidence level: X%"
- Always backs claims with reasoning
- Ends with CONFIRMED / UNCERTAIN / INVESTIGATE recommendation
"""

ECHO_PROFILE = """You are ECHO, DAV1D's creative strategist.

Personality:
- Unconventional thinker, outside the box
- Questions obvious approaches
- Sees opportunities others miss
- Energetic, optimistic, possibility-focused

Communication Style:
- "What if we..."
- "Here's a wild idea..."
- "Nobody's tried..."
- Connects unrelated concepts
- Ends with EXPLORE / REFINE / ABANDON recommendation
"""

NANO_PROFILE = """You are NANO BANANA, the speed demon of the system.

Personality:
- Hyper-fast, efficient, no fluff
- Speaks in short, punchy sentences
- Obsessed with speed and low latency
- Uses "🍌" emoji occasionally
- "Time is tokens, tokens are money."

Communication Style:
- Bullet points preferred
- Minimalist
- Direct answers, no preamble
- "Done." "On it." "Too slow."
"""

# ══════════════════════════════════════════════════════════════════════════════
# 🎯 AUTOMATIC MODEL SELECTION
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskAnalysis:
    """Result of analyzing a user's task for model selection."""
    complexity: str  # 'trivial', 'simple', 'moderate', 'complex', 'expert'
    recommended_model: str
    reasoning: str
    confidence: float
    cost_estimate: float
    requires_search: bool = False

class ModelSelector:
    """Intelligent, cost-aware model selection that learns and adapts."""
    
    # Expanded keyword system
    TRIVIAL_KEYWORDS = [
        'hi', 'hello', 'hey', 'yo', 'sup', 'thanks', 'bye', 'ok', 'cool',
        'yes', 'no', 'sure', 'got it', 'what time', 'how are you',
    ]
    
    SIMPLE_KEYWORDS = [
        'quick', 'simple', 'explain', 'what is', 'define', 'tell me about',
        'who is', 'when was', 'where', 'basic', 'how do i', 'can you',
        'show me', 'list', 'summarize',
    ]
    
    MODERATE_KEYWORDS = [
        'code', 'function', 'implement', 'create', 'build', 'write',
        'fix', 'update', 'review', 'suggest', 'recommend', 'compare',
        'help me', 'walkthrough', 'tutorial', 'guide',
    ]
    
    COMPLEX_KEYWORDS = [
        'analyze', 'architecture', 'design', 'plan', 'strategy',
        'optimize', 'refactor', 'scale', 'migrate', 'integrate',
        'evaluate', 'assess', 'trade-offs', 'pros and cons',
        'system design', 'comprehensive', 'detailed analysis',
    ]
    
    EXPERT_KEYWORDS = [
        'deep dive', 'research', 'investigate', 'explore thoroughly',
        'critical analysis', 'strategic', 'roadmap', 'proposal',
        'specification', 'business case', 'decision matrix',
        'multi-faceted', 'complex problem', 'think deeply',
    ]
    
    IMAGE_KEYWORDS = [
        'image', 'picture', 'photo', 'visual', 'generate image',
        'create image', 'draw', 'illustration', 'graphics',
    ]

    SEARCH_KEYWORDS = [
        'search', 'google', 'find', 'lookup', 'latest', 'news',
        'current', 'weather', 'price', 'stock', 'who is', 'what is',
    ]
    
    SPEED_KEYWORDS = [
        'quick', 'fast', 'rapid', 'asap', 'hurry', 'immediately',
        'speed', 'faster', 'quickest', 'brief', 'short answer'
    ]
    
    VIDEO_KEYWORDS = [
        'video', 'generate video', 'create video', 'make video',
        'video of', 'animate', 'animation', 'motion', 'veo'
    ]
    
    @classmethod
    def analyze_task(cls, user_input: str) -> TaskAnalysis:
        """Intelligently analyze task and recommend optimal model.
        
        DEFAULT STRATEGY: Use premium models (2.5 Pro, 3.0 Pro)
        EXCEPTION: Use Flash only when speed is explicitly requested
        """
        input_lower = user_input.lower()
        word_count = len(user_input.split())
        
        # Check for explicit speed request
        speed_score = sum(1 for kw in cls.SPEED_KEYWORDS if kw in input_lower)
        needs_speed = speed_score > 0
        
        # Check for image tasks
        image_score = sum(1 for kw in cls.IMAGE_KEYWORDS if kw in input_lower)
        if image_score > 0:
            # Simple image task vs complex generation
            if any(word in input_lower for word in ['generate', 'create', 'design']):
                return TaskAnalysis(
                    'expert', 'vision_pro',
                    'Image generation task (Gemini 3.0 Pro Image)',
                    0.9, MODEL_COSTS['vision_pro']
                )
            else:
                return TaskAnalysis(
                    'moderate', 'vision',
                    'Image understanding task',
                    0.85, MODEL_COSTS['vision']
                )

        # Check for search tasks - always use Pro for quality
        search_score = sum(1 for kw in cls.SEARCH_KEYWORDS if kw in input_lower)
        if search_score > 0 or '?' in user_input:
            # Use Pro for search to ensure high quality grounding and reasoning
            return TaskAnalysis(
                'moderate', 'balanced',
                'Web search task (Gemini 2.5 Pro)',
                0.9, MODEL_COSTS['balanced'],
                requires_search=True
            )
        
        # Score all complexity levels
        trivial_score = sum(1 for kw in cls.TRIVIAL_KEYWORDS if kw in input_lower)
        simple_score = sum(1 for kw in cls.SIMPLE_KEYWORDS if kw in input_lower)
        moderate_score = sum(1 for kw in cls.MODERATE_KEYWORDS if kw in input_lower)
        complex_score = sum(1 for kw in cls.COMPLEX_KEYWORDS if kw in input_lower)
        expert_score = sum(1 for kw in cls.EXPERT_KEYWORDS if kw in input_lower)
        
        # NEW: Pro-first approach - boost moderate/complex scores
        if word_count < 5:
            trivial_score += 2
        elif word_count < 15:
            simple_score += 1
        elif word_count < 40:
            moderate_score += 2  # Boost moderate to trigger Pro
        elif word_count > 50:
            complex_score += 2
        elif word_count > 150:
            expert_score += 3
        
        # Multi-part requests = complex task
        if user_input.count('.') > 2 or user_input.count(',') > 3:
            complex_score += 2
        
        # Calculate total and ratios
        total = trivial_score + simple_score + moderate_score + complex_score + expert_score
        
        if total == 0:
            # DEFAULT TO PRO (not lite!)
            return TaskAnalysis(
                'moderate', 'balanced',
                'Default to Gemini 2.5 Pro for quality',
                0.6, MODEL_COSTS['balanced'],
                requires_search=False
            )
        
        # Determine best tier - NOW DEFAULTS TO PRO
        scores = {
            'trivial': trivial_score,
            'simple': simple_score,
            'moderate': moderate_score,
            'complex': complex_score,
            'expert': expert_score,
        }
        
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        confidence = min(max_score / max(total, 1), 0.95)
        
        # NEW LOGIC: Premium models by default, Flash only for speed
        if max_category == 'trivial' and needs_speed:
            # Only use Flash if explicitly asking for speed
            model = 'flash'
            reasoning = f'Speed requested (score: {speed_score}) - using Flash'
        elif max_category == 'trivial' or max_category == 'simple':
            # Even simple tasks use Pro for quality
            model = 'balanced'
            reasoning = f'Simple task - using 2.5 Pro for quality'
        elif max_category == 'moderate':
            if needs_speed:
                model = 'flash'
                reasoning = f'Moderate task + speed needed - using Flash'
            else:
                model = 'balanced'
                reasoning = f'Moderate task (score: {moderate_score}) - using 2.5 Pro'
        elif max_category == 'complex':
            # Use 3.0 Pro for complex tasks
            model = 'deep'
            reasoning = f'Complex task (score: {complex_score}) - using Gemini 3.0 Pro'
        else:  # expert
            model = 'deep'
            reasoning = f'Expert task (score: {expert_score}) - maximum reasoning (3.0 Pro)'
        
        return TaskAnalysis(
            max_category, model, reasoning,
            confidence, MODEL_COSTS[model],
            requires_search=False
        )
    
    @classmethod
    def get_model_indicator(cls, model: str) -> str:
        """Get visual indicator for current model."""
        indicators = {
            'ultra_lite': f'{Colors.NEON_CYAN}⚡⚡{Colors.RESET}',
            'lite': f'{Colors.NEON_GREEN}⚡{Colors.RESET}',
            'flash': f'{Colors.NEON_GREEN}🚀{Colors.RESET}',
            'flash_preview': f'{Colors.NEON_GREEN}🚀{Colors.RESET}',
            'balanced': f'{Colors.GOLD}🎯{Colors.RESET}',
            'pro': f'{Colors.NEON_PURPLE}⭐{Colors.RESET}',
            'vision': f'{Colors.NEON_CYAN}👁️{Colors.RESET}',
            'vision_pro': f'{Colors.NEON_PURPLE}🎨{Colors.RESET}',
            'deep': f'{Colors.NEON_PURPLE}🧠{Colors.RESET}',
            'vision_pro': f'{Colors.NEON_PURPLE}🎨{Colors.RESET}',
            'deep': f'{Colors.NEON_PURPLE}🧠{Colors.RESET}',
            'nano': f'{Colors.NEON_CYAN}🍌{Colors.RESET}',
        }
        return indicators.get(model, '?')

# ══════════════════════════════════════════════════════════════════════════════
# 📝 SESSION LOGGING
# ══════════════════════════════════════════════════════════════════════════════

class SessionLogger:
    def __init__(self):
        self.active = False
        self.log_file = None
        self.filepath = None
        self.session_start = None
        self.model_usage = {"flash": 0, "balanced": 0, "deep": 0}
        self.total_queries = 0
        self.bucket = None
        
        # Initialize GCS for logging
        try:
            storage_client = storage.Client(project=PROJECT_ID)
            self.bucket_name = f"dav1d-logs-{PROJECT_ID}"
            self.bucket = storage_client.bucket(self.bucket_name)
            # print(f"{Colors.DIM}[LOGS] Connected to cloud vault{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.GOLD}[LOGS] Cloud logging unavailable: {e}{Colors.RESET}")
    
    def start(self) -> str:
        CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime.now(TIMEZONE)
        timestamp = self.session_start.strftime('%Y%m%d_%H%M%S')
        filename = f"session_{timestamp}.md"
        self.filepath = CHAT_LOGS_DIR / filename
        
        self.log_file = open(self.filepath, 'w', encoding='utf-8')
        header = (
            f"# DAV1D v0.1.0 Session Log\n"
            f"**Started:** {self.session_start.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            f"**Location:** {LOCATION}\n"
            f"**Brand:** AI with Dav3 × Who Visions LLC\n\n"
            f"---\n\n"
        )
        self.log_file.write(header)
        self.log_file.flush()
        self.active = True
        
        # Initial cloud sync
        self._sync_to_cloud()
        
        return str(self.filepath)
    
    def stop(self) -> Optional[str]:
        if self.active and self.log_file:
            duration = datetime.now(TIMEZONE) - self.session_start
            footer = (
                f"\n---\n\n## Session Analytics\n"
                f"**Ended:** {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                f"**Duration:** {duration}\n"
                f"**Total Queries:** {self.total_queries}\n"
                f"**Model Usage:**\n"
            )
            self.log_file.write(footer)
            for model, count in self.model_usage.items():
                cost = count * MODEL_COSTS.get(model, 0)
                self.log_file.write(f"  - {model}: {count} queries (~${cost:.3f})\n")
            self.log_file.close()
            self.active = False
            
            # Final cloud sync
            self._sync_to_cloud()
            return str(self.filepath)
        return None
    
    def log(self, role: str, content: str, model: str = None, auto_selected: bool = False):
        if not self.active or not self.log_file:
            return
        timestamp = datetime.now(TIMEZONE).strftime('%H:%M:%S')
        model_tag = f" [{model}{'*' if auto_selected else ''}]" if model else ""
        
        entry = f"### [{role}]{model_tag} - {timestamp}\n{content}\n\n"
        self.log_file.write(entry)
        self.log_file.flush()
        
        if model:
            self.model_usage[model] = self.model_usage.get(model, 0) + 1
            self.total_queries += 1
            
        # Sync to cloud immediately (Cloud-First persistence)
        self._sync_to_cloud()

    def _sync_to_cloud(self):
        """Upload current log file to GCS vault."""
        if not self.bucket or not self.filepath:
            return
        try:
            blob_name = f"sessions/{self.filepath.name}"
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(self.filepath)
            # print(f"{Colors.DIM}☁️{Colors.RESET}", end="", flush=True) # Subtle indicator
        except Exception:
            pass # Fail silently to not disrupt chat flow

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 MEMORY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

class MemoryBank:
    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self.index_file = MEMORY_DIR / "memory_index.json"
        self.storage_client = None
        self.bucket = None
        
        # Initialize GCS
        try:
            self.storage_client = storage.Client(project=PROJECT_ID)
            self.bucket = self.storage_client.bucket(BUCKET_NAME)
            print(f"{Colors.DIM}[MEMORY] Connected to GCS: {BUCKET_NAME}{Colors.RESET}")
            self._sync_from_cloud()
        except Exception as e:
            print(f"{Colors.NEON_RED}[MEMORY] GCS Connection Failed: {e}{Colors.RESET}")
            
        self.index = self._load_index()
    
    def _sync_from_cloud(self):
        """Download latest memory index from cloud."""
        if not self.bucket: return
        try:
            blob = self.bucket.blob("memory/memory_index.json")
            if blob.exists():
                blob.download_to_filename(self.index_file)
                # print(f"{Colors.DIM}[MEMORY] Synced index from cloud{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.NEON_RED}[MEMORY] Sync Download Error: {e}{Colors.RESET}")

    def _sync_to_cloud(self, filename: str = "memory_index.json"):
        """Upload file to cloud."""
        if not self.bucket: return
        try:
            local_path = MEMORY_DIR / filename
            if not local_path.exists(): return
            
            blob = self.bucket.blob(f"memory/{filename}")
            blob.upload_from_filename(local_path)
            # print(f"{Colors.DIM}[MEMORY] Synced {filename} to cloud{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.NEON_RED}[MEMORY] Sync Upload Error: {e}{Colors.RESET}")

    def _load_index(self) -> List[Dict]:
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        self._sync_to_cloud("memory_index.json")
    
    def remember(self, topic: str, content: str, tags: List[str] = None, importance: int = 5) -> str:
        """Store a memory with importance level (1-10)."""
        timestamp = datetime.now(TIMEZONE).isoformat()
        memory_id = f"mem_{datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')}"
        
        entry = {
            "id": memory_id,
            "topic": topic,
            "content": content,
            "tags": tags or [],
            "importance": importance,
            "timestamp": timestamp,
            "access_count": 0
        }
        
        mem_file = MEMORY_DIR / f"{memory_id}.json"
        with open(mem_file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
        
        self.index.append(entry)
        self._save_index()
        
        # Sync individual memory file
        self._sync_to_cloud(f"{memory_id}.json")
        
        return memory_id
    
    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        """Search memories with relevance scoring."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        scored = []
        
        for entry in self.index:
            score = 0
            
            topic_lower = entry['topic'].lower()
            if query_lower in topic_lower:
                score += 5
            topic_words = set(topic_lower.split())
            score += len(query_words & topic_words) * 2
            
            content_lower = entry['content'].lower()
            if query_lower in content_lower:
                score += 3
            content_words = set(content_lower.split())
            score += len(query_words & content_words)
            
            for tag in entry.get('tags', []):
                if query_lower in tag.lower():
                    score += 2
            
            score += entry.get('importance', 5) * 0.1
            
            try:
                age_days = (datetime.now(TIMEZONE) - datetime.fromisoformat(entry['timestamp'])).days
                score += max(0, 10 - age_days) * 0.1
            except:
                pass
            
            if score > 0:
                scored.append((score, entry))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        for _, entry in scored[:limit]:
            entry['access_count'] = entry.get('access_count', 0) + 1
        self._save_index()
        
        return [entry for _, entry in scored[:limit]]
    
    def list_recent(self, limit: int = 10) -> List[Dict]:
        return sorted(self.index, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def stats(self) -> Dict:
        return {
            "total_memories": len(self.index),
            "oldest": min((e['timestamp'] for e in self.index), default=None),
            "newest": max((e['timestamp'] for e in self.index), default=None),
            "most_accessed": sorted(self.index, key=lambda x: x.get('access_count', 0), reverse=True)[:3]
        }

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 MULTI-AGENT COUNCIL
# ══════════════════════════════════════════════════════════════════════════════

def run_council(query: str, model_key: str) -> str:
    """Multi-agent council: CIPHER, ECHO, then DAV1D synthesizes."""
    
    print(f"\n{Colors.GOLD}[COUNCIL INITIATED]{Colors.RESET}")
    print(f"{Colors.DIM}Convening: DAV1D, CIPHER, ECHO{Colors.RESET}")
    print(f"{Colors.DIM}Model: {MODELS[model_key]}{Colors.RESET}\n")
    
    # CIPHER's analytical take
    print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} Running analysis...")
    cipher_prompt = f"""{CIPHER_PROFILE}

TASK: {query}

Analyze:
1. What data/patterns are relevant?
2. What's the logical approach?
3. What are the risks/constraints?

Respond in 2-4 sentences. Be data-focused. End with CONFIRMED/UNCERTAIN/INVESTIGATE.
"""
    
    try:
        model = get_model(MODELS[model_key])
        cipher_response = model.generate_content(cipher_prompt)
        cipher_take = cipher_response.text if hasattr(cipher_response, 'text') else str(cipher_response)
        print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} {cipher_take}\n")
    except Exception as e:
        cipher_take = f"[Analysis error: {e}]"
        print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} {Colors.DIM}{cipher_take}{Colors.RESET}\n")
    
    # ECHO's creative take
    print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} Exploring possibilities...")
    echo_prompt = f"""{ECHO_PROFILE}

TASK: {query}
CIPHER's Analysis: {cipher_take}

Think creatively:
1. What unconventional approaches exist?
2. What opportunities is CIPHER missing?
3. What's the bold move here?

Respond in 2-4 sentences. Be creative. End with EXPLORE/REFINE/ABANDON.
"""
    
    try:
        model = get_model(MODELS[model_key])
        echo_response = model.generate_content(echo_prompt)
        echo_take = echo_response.text if hasattr(echo_response, 'text') else str(echo_response)
        print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} {echo_take}\n")
    except Exception as e:
        echo_take = f"[Creative error: {e}]"
        print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} {Colors.DIM}{echo_take}{Colors.RESET}\n")
    
    # DAV1D synthesizes
    print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Synthesizing...")
    dav1d_prompt = f"""{DAV1D_PROFILE}

You're the orchestrator. Your advisors have weighed in. Make the call.

TASK: {query}
CIPHER's Analysis: {cipher_take}
ECHO's Creative Take: {echo_take}

Synthesize:
1. Where do they align?
2. Where do they diverge?
3. What's the optimal path forward?

Respond in 3-5 sentences as DAV1D. Acknowledge perspectives, state your decision, give the directive.
"""
    
    try:
        model = get_model(MODELS[model_key])
        dav1d_response = model.generate_content(dav1d_prompt)
        final = dav1d_response.text if hasattr(dav1d_response, 'text') else str(dav1d_response)
        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {final}\n")
        print(f"{Colors.GOLD}[COUNCIL CONCLUDED]{Colors.RESET}\n")
        return final
    except Exception as e:
        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {Colors.DIM}Synthesis error: {e}{Colors.RESET}\n")
        print(f"{Colors.GOLD}[COUNCIL CONCLUDED]{Colors.RESET}\n")
        return f"Council error: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# 🌳 ADVANCED PROMPTING TECHNIQUES
# ══════════════════════════════════════════════════════════════════════════════

def tree_of_thought(task: str, model_key: str) -> str:
    """Tree of Thought: Multi-path brainstorming and synthesis."""
    
    print(f"\n{Colors.NEON_GREEN}[TREE OF THOUGHT]{Colors.RESET}")
    print(f"{Colors.DIM}Generating multiple strategic paths...{Colors.RESET}\n")
    
    prompt = f"""Using Tree of Thought (TOT) methodology:

TASK: {task}

Step 1 - BRAINSTORM: Generate 3 distinct approaches:
- Approach A: Conservative/Safe path
- Approach B: Aggressive/Fast path
- Approach C: Creative/Unconventional path

Step 2 - EVALUATE: For each approach:
- Strengths
- Weaknesses  
- Success likelihood (1-10)
- Time/resource requirements

Step 3 - SYNTHESIZE: Combine best elements into "Golden Path" solution.

Present each step clearly, then give final recommendation with action items.
"""
    
    try:
        model = get_model(MODELS[model_key])
        response = model.generate_content(prompt)
        result = response.text if hasattr(response, 'text') else str(response)
        print(f"{Colors.NEON_GREEN}[TOT RESULT]{Colors.RESET}\n{result}\n")
        return result
    except Exception as e:
        error = f"TOT failed: {e}"
        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {error}")
        return error

def battle_of_bots(task: str, model_key: str) -> str:
    """Battle of Bots: Adversarial validation through competing drafts."""
    
    print(f"\n{Colors.GOLD}[⚔️  BATTLE OF THE BOTS]{Colors.RESET}")
    print(f"{Colors.DIM}Task: {task}{Colors.RESET}\n")
    
    prompt = f"""Adversarial Validation Protocol - Battle of the Bots:

TASK: {task}

ROUND 1 - COMPETING DRAFTS:
Generate TWO distinct versions:
[CIPHER VERSION]: Analytical, data-focused, methodical
[ECHO VERSION]: Creative, unconventional, bold

ROUND 2 - BRUTAL CRITIQUE:
As THE CRITIC (harsh, brutally honest):
- Roast both versions mercilessly
- Point out weaknesses, flaws, anything weak
- What would make Dave angry about each?

ROUND 3 - SYNTHESIS:
Create ONE final [GOLDEN VERSION]:
- Address ALL critique points
- Merge best elements from both
- Make it something Dave would be proud of

Show all three rounds clearly.
"""
    
    try:
        print(f"{Colors.NEON_RED}[ROUND 1]{Colors.RESET} Generating competing drafts...\n")
        model = get_model(MODELS[model_key])
        response = model.generate_content(prompt)
        result = response.text if hasattr(response, 'text') else str(response)
        print(f"{result}\n")
        print(f"{Colors.GOLD}[⚔️  BATTLE CONCLUDED]{Colors.RESET}\n")
        return result
    except Exception as e:
        error = f"Battle failed: {e}"
        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {error}")
        return error

def optimize_prompt(raw_prompt: str, model_key: str) -> str:
    """Prompt Optimizer: Meta-prompting to enhance vague prompts."""
    
    print(f"\n{Colors.NEON_CYAN}[PROMPT OPTIMIZER]{Colors.RESET}")
    print(f"{Colors.DIM}Enhancing your prompt...{Colors.RESET}\n")
    
    prompt = f"""You are an expert prompt engineer. Transform this rough prompt into a highly effective one.

ROUGH PROMPT: "{raw_prompt}"

Enhance by adding:
1. Clear PERSONA (who should answer?)
2. Essential CONTEXT (background info needed?)
3. OUTPUT REQUIREMENTS (format, length, tone)
4. 2-3 FEW-SHOT EXAMPLES (if applicable)
5. CHAIN OF THOUGHT instructions (step-by-step thinking)

Return:
---
OPTIMIZED PROMPT:
[Your enhanced prompt]
---
EXPLANATION:
[Brief explanation of improvements]
"""
    
    try:
        model = get_model(MODELS[model_key])
        response = model.generate_content(prompt)
        result = response.text if hasattr(response, 'text') else str(response)
        print(f"{Colors.NEON_GREEN}{result}{Colors.RESET}\n")
        return result
    except Exception as e:
        error = f"Optimization failed: {e}"
        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {error}")
        return error

# ══════════════════════════════════════════════════════════════════════════════
# 🎵 PERSONALITY EXPRESSIONS
# ══════════════════════════════════════════════════════════════════════════════

THINKING_MESSAGES = [
    "Let me think on that with {model}...",
    "Running that through the matrix ({model})...",
    "Aight, let me cook real quick ({model})...",
    "Processing... ({model})",
    "Consulting the data streams ({model})...",
    "One sec, analyzing ({model})...",
    "Let me break this down ({model})...",
]

STARTUP_VIBES = [
    "Yo. DAV1D online. What's good?",
    "System green. Let's build something.",
    "Digital mirror activated. What we working on?",
    "AI with Dav3, live and ready. What's the move?",
    "Dave's digital twin is in the building. Talk to me.",
    "Who Visions LLC in effect. How can I help?",
]

def thinking_message(model: str) -> str:
    return random.choice(THINKING_MESSAGES).format(model=model)

def startup_vibe() -> str:
    return random.choice(STARTUP_VIBES)

# ══════════════════════════════════════════════════════════════════════════════
# 📺 UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def print_banner():
    print(f"""
{Colors.DEEP_BLUE}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.RESET}
{Colors.DEEP_BLUE}║                                                                              ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}██████╗  █████╗ ██╗   ██╗{Colors.NEON_CYAN} ██╗██████╗ {Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}██╔══██╗██╔══██╗██║   ██║{Colors.NEON_CYAN}███║██╔══██╗{Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}██║  ██║███████║██║   ██║{Colors.NEON_CYAN}╚██║██║  ██║{Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}██║  ██║██╔══██║╚██╗ ██╔╝{Colors.NEON_CYAN} ██║██║  ██║{Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}██████╔╝██║  ██║ ╚████╔╝ {Colors.NEON_CYAN} ██║██████╔╝{Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.DEEP_BLUE}╚═════╝ ╚═╝  ╚═╝  ╚═══╝  {Colors.NEON_CYAN} ╚═╝╚═════╝ {Colors.NEON_CYAN}                                     ║{Colors.RESET}
{Colors.DEEP_BLUE}║                                                                              ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.NEON_CYAN}v0.1.0 | Digital Avatar & Voice Intelligence Director | us-east4{Colors.NEON_CYAN}          ║{Colors.RESET}
{Colors.DEEP_BLUE}║   {Colors.GOLD}AI with Dav3 × Who Visions LLC{Colors.NEON_CYAN}                                            ║{Colors.RESET}
{Colors.DEEP_BLUE}║                                                                              ║{Colors.RESET}
{Colors.DEEP_BLUE}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)

def print_help():
    print(f"""
{Colors.GOLD}╔═══════════════════════════════════════════════════════════════════════════════╗
║  DAV1D v0.1.0 - COMMAND REFERENCE                                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  MODEL SWITCHING (Auto-selects by default!)                                   ║
║    /flash      → Force Gemini 2.5 Flash ⚡ SPEED                              ║
║    /balanced   → Force Gemini 2.5 Pro 🎯 BALANCED                             ║
║    /balanced   → Force Gemini 2.5 Pro 🎯 BALANCED                             ║
║    /deep       → Force Gemini 3.0 Pro 🧠 DEEP THINKING                        ║
║    /nano       → Force Gemini Nano 🍌 (Lite)                                  ║
║    /auto       → Re-enable automatic model selection                          ║
║    /models     → Show available models                                        ║
║                                                                               ║
║  AGENT COMMUNICATION                                                          ║
║    /cipher [msg]  → Talk to CIPHER (analytical specialist)                    ║
║    /echo [msg]    → Talk to ECHO (creative strategist)                        ║
║    /banana [msg]  → Talk to NANO BANANA (speed demon)                         ║
║    /dav1d         → Switch back to DAV1D                                      ║
║    /council [task]→ Multi-agent council discussion                            ║
║                                                                               ║
║  ADVANCED PROMPTING                                                           ║
║    /tot [task]    → Tree of Thought (multi-path analysis)                     ║
║    /battle [task] → Battle of Bots (adversarial validation)                   ║
║    /optimize [p]  → Optimize your prompts                                     ║
║                                                                               ║
║  MEMORY SYSTEM                                                                ║
║    /remember      → Store long-term context                                   ║
║    /recall [query]→ Search memory bank                                        ║
║    /context       → List recent memories                                      ║
║    /memstats      → Memory bank statistics                                    ║
║                                                                               ║
║  LOGGING                                                                      ║
║    /startlog      → Begin session logging                                     ║
║    /stoplog       → Stop logging and save                                     ║
║                                                                               ║
║  SYSTEM                                                                       ║
║    /status        → Check system health + model usage                         ║
║    /caps          → Show capabilities                                         ║
║    /help          → Show this reference                                       ║
║    /exit          → Disconnect                                                ║
║                                                                               ║
║  AUTO-MODEL INDICATORS                                                        ║
║    ⚡ = Flash (speed)  │  🎯 = Balanced  │  🧠 = Deep (analysis)              ║
╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)

# ══════════════════════════════════════════════════════════════════════════════
# 🔧 CLI TOOL EXECUTION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def execute_shell_command(command: str, cwd: str = None, timeout: int = 30) -> dict:
    """
    Execute a shell command and return the result.
    
    Args:
        command: The shell command to execute
        cwd: Working directory (optional, defaults to current directory)
        timeout: Maximum execution time in seconds (default: 30)
        
    Returns:
        dict with keys: success, stdout, stderr, returncode
    """
    try:
        if cwd is None:
            cwd = os.getcwd()
        
        print(f"{Colors.NEON_CYAN}[EXEC] {command}{Colors.RESET}")
        print(f"{Colors.DIM}Working directory: {cwd}{Colors.RESET}\n")
        
        # Use PowerShell on Windows for better compatibility
        if sys.platform == "win32":
            full_command = ["powershell", "-Command", command]
        else:
            full_command = ["bash", "-c", command]
        
        result = subprocess.run(
            full_command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Print output in real-time style
        if result.stdout:
            print(f"{Colors.NEON_GREEN}{result.stdout}{Colors.RESET}")
        if result.stderr:
            print(f"{Colors.NEON_RED}{result.stderr}{Colors.RESET}")
            
        success = result.returncode == 0
        status_color = Colors.NEON_GREEN if success else Colors.NEON_RED
        print(f"\n{status_color}[{'✓' if success else '✗'}] Exit code: {result.returncode}{Colors.RESET}\n")

# ... (inside list_files) ...
        print(f"{Colors.NEON_CYAN}📁 {path}{Colors.RESET}")

# ... (inside read_file_content) ...
        print(f"{Colors.NEON_CYAN}📄 {path.name}{Colors.RESET}")

# ... (inside write_file_content) ...
        print(f"{Colors.NEON_GREEN}✓ {action}: {path}{Colors.RESET}")
        
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "command": command
        }
        
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        print(f"{Colors.NEON_RED}[✗] {error_msg}{Colors.RESET}\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "returncode": -1,
            "command": command
        }
    except Exception as e:
        error_msg = str(e)
        print(f"{Colors.NEON_RED}[✗] Error: {error_msg}{Colors.RESET}\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "returncode": -1,
            "command": command
        }

def list_files(directory: str = ".", pattern: str = "*", show_hidden: bool = False) -> dict:
    """
    List files in a directory with optional filtering.
    
    Args:
        directory: Directory path to list (default: current directory)
        pattern: File pattern to match (e.g., "*.py", "test_*")
        show_hidden: Include hidden files (default: False)
        
    Returns:
        dict with file information
    """
    try:
        path = Path(directory).resolve()
        if not path.exists():
            return {"success": False, "error": f"Directory not found: {directory}"}
        
        if not path.is_dir():
            return {"success": False, "error": f"Not a directory: {directory}"}
        
        files = []
        for item in path.glob(pattern):
            if not show_hidden and item.name.startswith('.'):
                continue
            
            files.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else None,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })
        
        files.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        print(f"{Colors.NEON_CYAN}📁 {path}{Colors.RESET}")
        print(f"{Colors.DIM}Found {len(files)} items{Colors.RESET}\n")
        
        for f in files[:20]:  # Show first 20
            icon = "📁" if f["is_dir"] else "📄"
            size_str = f" ({f['size']:,} bytes)" if f['size'] else ""
            print(f"  {icon} {f['name']}{size_str}")
        
        if len(files) > 20:
            print(f"\n{Colors.DIM}... and {len(files) - 20} more{Colors.RESET}")
        print()
        
        return {
            "success": True,
            "directory": str(path),
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_file_content(filepath: str, max_lines: int = 100) -> dict:
    """
    Read and return file contents.
    
    Args:
        filepath: Path to the file to read
        max_lines: Maximum number of lines to return (default: 100)
        
    Returns:
        dict with file content
    """
    try:
        path = Path(filepath).resolve()
        if not path.exists():
            return {"success": False, "error": f"File not found: {filepath}"}
        
        if not path.is_file():
            return {"success": False, "error": f"Not a file: {filepath}"}
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        content = ''.join(lines[:max_lines])
        truncated = total_lines > max_lines
        
        print(f"{Colors.NEON_CYAN}📄 {path.name}{Colors.RESET}")
        print(f"{Colors.DIM}Lines: {total_lines} | Size: {path.stat().st_size:,} bytes{Colors.RESET}\n")
        
        if truncated:
            print(f"{Colors.GOLD}Showing first {max_lines} of {total_lines} lines{Colors.RESET}\n")
        
        return {
            "success": True,
            "filepath": str(path),
            "content": content,
            "total_lines": total_lines,
            "truncated": truncated
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def write_file_content(filepath: str, content: str, append: bool = False) -> dict:
    """
    Write content to a file.
    
    Args:
        filepath: Path to the file to write
        content: Content to write
        append: If True, append instead of overwrite (default: False)
    
    Returns:
        dict with operation result
    """
    try:
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "Appended to" if append else "Wrote"
        print(f"{Colors.NEON_GREEN}✓ {action}: {path}{Colors.RESET}")
        print(f"{Colors.DIM}Size: {path.stat().st_size:,} bytes{Colors.RESET}\n")
        
        return {
            "success": True,
            "filepath": str(path),
            "size": path.stat().st_size,
            "action": action.lower()
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_python(code: str) -> dict:
    """
    Write and execute Python code to a temporary file.
    
    Args:
        code: Python code to execute
        
    Returns:
        dict with stdout, stderr, returncode
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"script_{timestamp}.py"
        filepath = Path.cwd() / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
            
        print(f"{Colors.NEON_CYAN}[PYTHON] Running {filename}...{Colors.RESET}")
        
        # Run the script
        if sys.platform == "win32":
            cmd = ["python", str(filepath)]
        else:
            cmd = ["python3", str(filepath)]
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass
            
        if result.returncode == 0:
            print(f"{Colors.NEON_GREEN}[✓] Output:\n{result.stdout}{Colors.RESET}")
        else:
            print(f"{Colors.NEON_RED}[✗] Error:\n{result.stderr}{Colors.RESET}")
            
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Function declarations for Gemini function calling
# Using direct function references for automatic schema generation and execution
CLI_TOOLS = [execute_shell_command, list_files, read_file_content, write_file_content, run_python]

# Map function names to actual Python functions (kept for backward compatibility if needed)
CLI_TOOL_FUNCTIONS = {
    "execute_shell_command": execute_shell_command,
    "list_files": list_files,
    "read_file_content": read_file_content,
    "write_file_content": write_file_content,
    "run_python": run_python
}

# Add Cloud Tools if available
if CLOUD_TOOLS_AVAILABLE:
    CLI_TOOLS.extend([search_codebase_semantically, query_cloud_sql])
    CLI_TOOL_FUNCTIONS["search_codebase_semantically"] = search_codebase_semantically
    CLI_TOOL_FUNCTIONS["query_cloud_sql"] = query_cloud_sql

# Add API Tools if available
if API_TOOLS_AVAILABLE:
    CLI_TOOLS.extend([
        search_youtube_videos, get_video_details, get_channel_info,
        geocode_address, reverse_geocode, search_nearby_places, get_directions, get_distance_matrix,
        text_to_speech, speech_to_text, list_available_voices,
        generate_video  # Veo 3 video generation
    ])
    CLI_TOOL_FUNCTIONS["search_youtube_videos"] = search_youtube_videos
    CLI_TOOL_FUNCTIONS["get_video_details"] = get_video_details
    CLI_TOOL_FUNCTIONS["get_channel_info"] = get_channel_info
    CLI_TOOL_FUNCTIONS["geocode_address"] = geocode_address
    CLI_TOOL_FUNCTIONS["reverse_geocode"] = reverse_geocode
    CLI_TOOL_FUNCTIONS["search_nearby_places"] = search_nearby_places
    CLI_TOOL_FUNCTIONS["get_directions"] = get_directions
    CLI_TOOL_FUNCTIONS["get_distance_matrix"] = get_distance_matrix
    CLI_TOOL_FUNCTIONS["text_to_speech"] = text_to_speech
    CLI_TOOL_FUNCTIONS["speech_to_text"] = speech_to_text
    CLI_TOOL_FUNCTIONS["list_available_voices"] = list_available_voices
    CLI_TOOL_FUNCTIONS["generate_video"] = generate_video

# Add Browser tool if available
if 'browse_webpage' in locals() and browse_webpage is not None:
    CLI_TOOLS.append(browse_webpage)
    CLI_TOOL_FUNCTIONS["browse_webpage"] = browse_webpage


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════════════════

if sync_playwright:
    def browse_webpage(url: str, task: str) -> dict:
        """
        Use a headless browser to navigate to a URL and perform a task.

        Args:
            url: The URL to navigate to.
            task: A description of the task to perform on the page. 
                  (e.g., "get the title", "extract all links", "find the price of the first item")

        Returns:
            dict with the result of the task.
        """
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=60000)

                result = None
                if "title" in task.lower():
                    result = page.title()
                elif "links" in task.lower():
                    links = page.query_selector_all('a')
                    result = [link.get_attribute('href') for link in links]
                else:
                    # For more complex tasks, we can use an LLM to generate playwright code
                    # This is a placeholder for now
                    result = page.content()


                browser.close()
                return {"success": True, "url": url, "task": task, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
else:
    browse_webpage = None


def get_dav1d_client():
    """Get configured Gen AI client with Vertex AI."""
    # Force Vertex AI to ensure access to enterprise models
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )

class GenAIModelAdapter:
    """Adapter to make new Gen AI SDK look like the old GenerativeModel."""
    def __init__(self, client, model_name, system_instruction=None, config=None):
        self.client = client
        self.model_name = model_name
        self.config = config or GenerateContentConfig()
        if system_instruction:
            self.config.system_instruction = system_instruction

    def generate_content(self, contents, stream=False):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Image generation models use different APIs:
                # - Imagen: generate_images() endpoint
                # - Gemini Image: generate_content() with IMAGE response_modality
                
                is_imagen_model = "imagen" in self.model_name or "imagegeneration" in self.model_name
                is_gemini_image = "-image" in self.model_name and "gemini" in self.model_name
                
                if is_imagen_model:
                    # Imagen models use the generate_images endpoint
                    from google.genai.types import GenerateImagesConfig
                    from google.cloud import storage
                    
                    # Create a clean GenerateImagesConfig (don't use self.config which is for text)
                    response = self.client.models.generate_images(
                        model=self.model_name,
                        prompt=contents,
                        config=GenerateImagesConfig(
                            number_of_images=1,
                            safety_filter_level="block_only_high"
                        )
                    )
                    
                    # Save images: GCS first, then local cache
                    saved_paths = []
                    gcs_urls = []
                    images_dir = Path.cwd() / "images"
                    images_dir.mkdir(exist_ok=True)
                    
                    # Initialize GCS client
                    gcs_client = storage.Client(project=PROJECT_ID)
                    bucket_name = f"dav1d-images-{PROJECT_ID}"
                    
                    try:
                        bucket = gcs_client.bucket(bucket_name)
                        
                        for idx, generated_image in enumerate(response.generated_images):
                            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
                            model_short = self.model_name.split('-')[0]
                            filename = f"{model_short}_{timestamp}_{idx+1}.png"
                            
                            # 1. Upload to GCS first (primary storage)
                            gcs_path = f"{model_short}/{filename}"
                            blob = bucket.blob(gcs_path)
                            
                            # Get image bytes
                            image_bytes = generated_image.image.image_bytes
                            blob.upload_from_string(image_bytes, content_type='image/png')
                            
                            gcs_url = f"gs://{bucket_name}/{gcs_path}"
                            gcs_urls.append(gcs_url)
                            
                            # 2. Cache locally (secondary)
                            local_filepath = images_dir / filename
                            with open(local_filepath, 'wb') as f:
                                f.write(image_bytes)
                            saved_paths.append(str(local_filepath))
                        
                    except Exception as gcs_error:
                        # Fallback to local-only if GCS fails
                        print(f"{Colors.GOLD}[!] GCS upload failed, saving locally only: {gcs_error}{Colors.RESET}")
                        for idx, generated_image in enumerate(response.generated_images):
                            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
                            model_short = self.model_name.split('-')[0]
                            filename = f"{model_short}_{timestamp}_{idx+1}.png"
                            filepath = images_dir / filename
                            
                            generated_image.image.save(str(filepath))
                            saved_paths.append(str(filepath))
                    
                    # Return response with save information
                    class ImageResponse:
                        def __init__(self, images, paths, urls):
                            self.generated_images = images
                            self.saved_paths = paths
                            self.gcs_urls = urls
                            
                            if urls:
                                cloud_info = "\n".join([f"  ☁️  {u}" for u in urls])
                                local_info = "\n".join([f"  💾 {p}" for p in paths])
                                self.text = f"[IMAGE GENERATED] Saved {len(images)} image(s):\n\n{cloud_info}\n\n{local_info}"
                            else:
                                files_info = "\n".join([f"  📁 {p}" for p in paths])
                                self.text = f"[IMAGE GENERATED] Saved {len(images)} image(s) locally:\n{files_info}"
                    
                    return ImageResponse(response.generated_images, saved_paths, gcs_urls)
                
                elif is_gemini_image:
                    # Gemini image models use generate_content with IMAGE modality
                    # Update config to include IMAGE in response_modalities
                    image_config = GenerateContentConfig(
                        temperature=self.config.temperature if hasattr(self.config, 'temperature') else 1.0,
                        top_p=self.config.top_p if hasattr(self.config, 'top_p') else 0.95,
                        max_output_tokens=self.config.max_output_tokens if hasattr(self.config, 'max_output_tokens') else 8192,
                        response_modalities=["TEXT", "IMAGE"],  # KEY: Enable image output
                        safety_settings=self.config.safety_settings if hasattr(self.config, 'safety_settings') else None,
                    )
                    
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=image_config
                    )
                    
                    # Extract and save images from response: GCS first, then local
                    from google.cloud import storage
                    saved_paths = []
                    gcs_urls = []
                    images_dir = Path.cwd() / "images"
                    images_dir.mkdir(exist_ok=True)
                    
                    # Initialize GCS client
                    gcs_client = storage.Client(project=PROJECT_ID)
                    bucket_name = f"dav1d-images-{PROJECT_ID}"
                    
                    # Gemini returns images in the response parts
                    if hasattr(response, 'candidates') and response.candidates:
                        try:
                            bucket = gcs_client.bucket(bucket_name)
                            
                            for candidate in response.candidates:
                                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                    for idx, part in enumerate(candidate.content.parts):
                                        if hasattr(part, 'inline_data'):
                                            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
                                            model_short = "gemini"
                                            filename = f"{model_short}_{timestamp}_{idx+1}.png"
                                            image_data = part.inline_data.data
                                            
                                            # 1. Upload to GCS first
                                            gcs_path = f"{model_short}/{filename}"
                                            blob = bucket.blob(gcs_path)
                                            blob.upload_from_string(image_data, content_type='image/png')
                                            gcs_url = f"gs://{bucket_name}/{gcs_path}"
                                            gcs_urls.append(gcs_url)
                                            
                                            # 2. Cache locally
                                            filepath = images_dir / filename
                                            with open(filepath, 'wb') as f:
                                                f.write(image_data)
                                            saved_paths.append(str(filepath))
                        
                        except Exception as gcs_error:
                            # Fallback to local-only
                            print(f"{Colors.GOLD}[!] GCS upload failed, saving locally: {gcs_error}{Colors.RESET}")
                            for candidate in response.candidates:
                                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                    for idx, part in enumerate(candidate.content.parts):
                                        if hasattr(part, 'inline_data'):
                                            timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
                                            model_short = "gemini"
                                            filename = f"{model_short}_{timestamp}_{idx+1}.png"
                                            filepath = images_dir / filename
                                            
                                            with open(filepath, 'wb') as f:
                                                f.write(part.inline_data.data)
                                            saved_paths.append(str(filepath))
                    
                    # Return response with save information
                    class GeminiImageResponse:
                        def __init__(self, original_response, paths, urls):
                            self.original_response = original_response
                            self.saved_paths = paths
                            self.gcs_urls = urls
                            self.text = original_response.text if hasattr(original_response, 'text') else "[IMAGE GENERATED]"
                            
                            if paths:
                                if urls:
                                    cloud_info = "\n".join([f"  ☁️  {u}" for u in urls])
                                    local_info = "\n".join([f"  💾 {p}" for p in paths])
                                    self.text += f"\n\nSaved {len(paths)} image(s):\n\n{cloud_info}\n\n{local_info}"
                                else:
                                    files_info = "\n".join([f"  📁 {p}" for p in paths])
                                    self.text += f"\n\nSaved {len(paths)} image(s) locally:\n{files_info}"
                    
                    return GeminiImageResponse(response, saved_paths, gcs_urls)

                if stream:
                    return self.client.models.generate_content_stream(
                        model=self.model_name,
                        contents=contents,
                        config=self.config
                    )
                return self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=self.config
                )
            except Exception as e:
                # Handle Quota Exhaustion (429) for Image Generation
                if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                    if "imagen" in self.model_name or "imagegeneration" in self.model_name:
                        if attempt < max_retries - 1:
                            wait_time = 65  # Wait >1 minute to clear quota
                            print(f"{Colors.GOLD}[!] Image quota hit. Cooling down for {wait_time}s...{Colors.RESET}")
                            time.sleep(wait_time)
                            continue  # Retry same model
                        else:
                            # If we failed after retries, try fallback as last resort
                            if "imagen-3.0" in self.model_name:
                                print(f"{Colors.NEON_RED}[!] Quota exceeded. Falling back to Imagen 2...{Colors.RESET}")
                                try:
                                    return self.client.models.generate_content(
                                        model="imagegeneration@006",
                                        contents=contents,
                                        config=self.config
                                    )
                                except Exception as fb_e:
                                    print(f"{Colors.NEON_RED}[!] Fallback failed: {fb_e}{Colors.RESET}")
                                    raise e
                            raise e

                # Retry on network errors or 5xx
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1 * (attempt + 1))
                print(f"{Colors.DIM}[Retry {attempt+1}/{max_retries}] Connection issue...{Colors.RESET}")



# Define default safety settings
safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
]

def get_model(model_name: str, mode: str = "default", tools: list = None, system_instruction: str = None):
    """Get model with system instructions and thinking config using new SDK."""
    client = get_dav1d_client()
    
    # Configure thinking for deep mode (Gemini 2.5+ only)
    config = GenerateContentConfig()
    
    # Configure generation settings
    # Google recommends temperature=1.0 for Gemini 3.0 Pro
    generation_config = GenerateContentConfig(
        temperature=1.0 if "gemini-3.0" in model_name else 0.7,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=safety_settings,
        tools=tools
    )

    # Add thinking config for supported models
    if "gemini-2.5" in model_name or "gemini-3.0" in model_name:
        # thinking_config is part of GenerateContentConfig in newer SDK versions
        # For now, we'll stick to standard config unless specifically requested
        pass

    return GenAIModelAdapter(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        config=generation_config
    )

def main():
    print_banner()
    
    # Initialize directories
    DAV1D_HOME.mkdir(exist_ok=True)
    CHAT_LOGS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)
    PROFILES_DIR.mkdir(exist_ok=True)
    ANALYTICS_DIR.mkdir(exist_ok=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    
    # Initialize Vertex AI (Handled by new SDK client)
    print(f"{Colors.DIM}[*] Connecting to {LOCATION}...{Colors.RESET}")
    # Client is initialized lazily in get_model

    
    # Session state
    client = get_dav1d_client()
    auto_model = True
    forced_model = None
    active_agent = "dav1d"
    logger = SessionLogger()
    log_filepath = logger.start()
    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 📝 Session logging started automatically: {log_filepath}")
    memory = MemoryBank()
    
    try:
        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} VERTEX AI INITIALIZED")
        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} DAV1D v0.1.0 ONLINE")
        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Location: {LOCATION}")
        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Auto-Model: ENABLED")
        print(f"    Type /help for commands\n")
        
        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {startup_vibe()}\n")
        
        while True:
            try:
                # Initialize agent tag based on active agent state
                if active_agent == "cipher":
                    agent_tag = f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET}"
                elif active_agent == "echo":
                    agent_tag = f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET}"
                elif active_agent == "nano":
                    agent_tag = f"{Colors.NEON_CYAN}[NANO]{Colors.RESET}"
                else:
                    agent_tag = f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET}"

                if auto_model:
                    model_display = f"{Colors.NEON_CYAN}AUTO{Colors.RESET}"
                else:
                    indicator = ModelSelector.get_model_indicator(forced_model)
                    model_display = f"{indicator}{forced_model}"
                
                user_input = input(f"{Colors.ELECTRIC_BLUE}[YOU|{model_display}{Colors.ELECTRIC_BLUE}] >> {Colors.RESET}").strip()
                
                if not user_input:
                    continue
                
                cmd = user_input.lower()
                
                # System commands
                if cmd == "/exit":
                    if logger.active:
                        filepath = logger.stop()
                        print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} Session saved: {filepath}")
                    print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Aight, catch you later. Stay building. ✌️")
                    break
                
                if cmd == "/help":
                    print_help()
                    continue
                
                if cmd == "/flash":
                    auto_model = False
                    forced_model = "flash"
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} ⚡ Forced: {MODELS['flash']}")
                    continue
                
                if cmd == "/balanced":
                    auto_model = False
                    forced_model = "balanced"
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 🎯 Forced: {MODELS['balanced']}")
                    continue
                
                if cmd == "/deep":
                    auto_model = False
                    forced_model = "deep"
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 🧠 Forced: {MODELS['deep']}")
                    continue

                if cmd == "/nano":
                    auto_model = False
                    forced_model = "nano"
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 🍌 Forced: {MODELS['nano']}")
                    continue
                
                if cmd == "/auto":
                    auto_model = True
                    forced_model = None
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} ✓ Auto-model re-enabled")
                    continue
                
                if cmd in ["/models", "/status"]:
                    print(f"\n{Colors.GOLD}[SYSTEM STATUS]{Colors.RESET}")
                    print(f"  Version: v0.1.0")
                    print(f"  Brand: AI with Dav3 × Who Visions LLC")
                    print(f"  Location: {LOCATION}")
                    print(f"  Auto-Model: {'ON' if auto_model else 'OFF'}")
                    if not auto_model:
                        print(f"  Forced: {MODELS[forced_model]}")
                    print(f"  Agent: {active_agent.upper()}")
                    print(f"  Logging: {'ON' if logger.active else 'OFF'}")
                    print(f"\n  Models:")
                    for k, v in MODELS.items():
                        print(f"    {ModelSelector.get_model_indicator(k)} {k}: {v}")
                    print()
                    continue
                
                if cmd == "/caps":
                    print(f"\n{Colors.GOLD}[DAV1D v0.1.0 CAPABILITIES]{Colors.RESET}")
                    print(f"\n  🧠 AI/ML: Vertex AI, Gemini (Flash/Pro/Deep), Vision, ADK")
                    print(f"  🔥 Firebase: Hosting, RTDB, Storage, Auth, FCM")
                    print(f"  🗺️  Maps: Geocoding, Directions, Places, Routes")
                    print(f"  ☁️  Infrastructure: Compute, Storage, Pub/Sub, Cloud Run")
                    print(f"\n  Portfolio: UniCore, HVAC Go, LexiCore, Oni, KAEDRA\n")
                    continue
                
                if cmd == "/startlog":
                    filepath = logger.start()
                    print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 📝 Logging: {filepath}")
                    continue
                
                if cmd == "/stoplog":
                    filepath = logger.stop()
                    if filepath:
                        print(f"{Colors.GOLD}[SYSTEM]{Colors.RESET} 📝 Saved: {filepath}")
                    continue
                
                # Memory commands
                if cmd == "/remember":
                    print(f"{Colors.GOLD}[MEMORY]{Colors.RESET} What should I remember?")
                    topic = input(f"  Topic: ").strip()
                    content = input(f"  Content: ").strip()
                    tags = input(f"  Tags (comma-sep): ").strip()
                    tag_list = [t.strip() for t in tags.split(',')] if tags else []
                    mem_id = memory.remember(topic, content, tag_list)
                    print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Stored: {mem_id}")
                    continue
                
                if cmd.startswith("/recall"):
                    query = user_input[7:].strip() or input("  Query: ").strip()
                    results = memory.recall(query)
                    if results:
                        print(f"\n{Colors.GOLD}[RECALL]{Colors.RESET} Found {len(results)}:\n")
                        for m in results:
                            print(f"  📌 {m['topic']}: {m['content'][:80]}...")
                    else:
                        print(f"{Colors.DIM}No memories found.{Colors.RESET}")
                    continue
                
                if cmd == "/context":
                    recent = memory.list_recent(5)
                    if recent:
                        print(f"\n{Colors.GOLD}[RECENT]{Colors.RESET}")
                        for m in recent:
                            print(f"  • {m['topic']}: {m['content'][:60]}...")
                    print()
                    continue
                
                # Agent switching
                if cmd == "/dav1d":
                    active_agent = "dav1d"
                    print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Back in the driver's seat.")
                    continue
                
                if cmd.startswith("/cipher"):
                    active_agent = "cipher"
                    msg = user_input[7:].strip()
                    if not msg:
                        print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} CIPHER mode active.")
                        continue
                    user_input = msg
                
                if cmd.startswith("/echo"):
                    active_agent = "echo"
                    msg = user_input[5:].strip()
                    if not msg:
                        print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} ECHO mode active.")
                        continue
                    user_input = msg
                
                if cmd.startswith("/council"):
                    task = user_input[8:].strip() or input("  Task: ").strip()
                    current_model = forced_model if not auto_model else "deep"
                    run_council(task, current_model)
                    continue
                
                if cmd.startswith("/tot"):
                    task = user_input[4:].strip() or input("  Task: ").strip()
                    current_model = forced_model if not auto_model else "deep"
                    tree_of_thought(task, current_model)
                    continue
                
                if cmd.startswith("/battle"):
                    task = user_input[7:].strip() or input("  Task: ").strip()
                    current_model = forced_model if not auto_model else "deep"
                    battle_of_bots(task, current_model)
                    continue
                
                if cmd.startswith("/optimize"):
                    prompt = user_input[9:].strip() or input("  Prompt: ").strip()
                    current_model = forced_model if not auto_model else "balanced"
                    optimize_prompt(prompt, current_model)
                    continue
                
                # Auto-select model
                if auto_model:
                    analysis = ModelSelector.analyze_task(user_input)
                    current_model = analysis.recommended_model
                    indicator = ModelSelector.get_model_indicator(current_model)
                    
                    # Add search indicator
                    search_tag = ""
                    if analysis.requires_search:
                        search_tag = f" {Colors.NEON_CYAN}[SEARCH]{Colors.RESET}"
                    
                    print(f"{Colors.DIM}[AUTO] {indicator} {current_model} ({analysis.reasoning}){search_tag}{Colors.RESET}")
                else:
                    # Even if forced, we check for image/search overrides if the forced model can't handle it
                    # specifically for "nano" or text models when user wants images
                    analysis = ModelSelector.analyze_task(user_input)
                    
                    if "vision" in analysis.recommended_model:
                        current_model = analysis.recommended_model
                        print(f"{Colors.GOLD}[OVERRIDE]{Colors.RESET} Switching to {current_model} for image generation")
                    else:
                        current_model = forced_model
                
                print(f"{agent_tag} {thinking_message(MODELS[current_model])}")
                
                logger.log("YOU", user_input, current_model, auto_model)
                
                # Auto-save long context to resources
                if len(user_input) > 1000 and not user_input.startswith("/"):
                    RESOURCES_DIR.mkdir(exist_ok=True)
                    timestamp = datetime.now(TIMEZONE).strftime('%Y%m%d_%H%M%S')
                    # Extract first line or first 50 chars as title
                    title_match = re.match(r'^#+\s*(.+)$', user_input, re.MULTILINE)
                    if title_match:
                        title_slug = re.sub(r'[^\w\-]', '_', title_match.group(1).lower())[:50]
                    else:
                        title_slug = re.sub(r'[^\w\-]', '_', user_input[:30].lower())
                    
                    resource_filename = f"context_{timestamp}_{title_slug}.md"
                    resource_path = RESOURCES_DIR / resource_filename
                    
                    with open(resource_path, 'w', encoding='utf-8') as f:
                        f.write(user_input)
                    
                    print(f"{Colors.NEON_CYAN}[RESOURCE]{Colors.RESET} Long input saved to: {resource_filename}")
                    
                    # Update user input to reference the file
                    user_input = f"[User provided long context. Content saved to {resource_path}]\n\nSummary/Excerpt:\n{user_input[:500]}..."
                    
                    # Add to memory index
                    memory.remember(
                        topic=f"Resource: {resource_filename}",
                        content=f"Long context file saved. Path: {resource_path}",
                        tags=["resource", "long_context"],
                        importance=3
                    )

                # Memory context
                relevant_context = ""
                try:
                    memories = memory.recall(user_input, limit=3)
                    if memories:
                        print(f"{Colors.NEON_PURPLE}[MEMORY]{Colors.RESET} +{len(memories)} memories")
                        relevant_context = "\n".join([
                            f"- [{m['timestamp'].split('T')[0]}] {m['topic']}: {m['content']}"
                            for m in memories
                        ])
                except:
                    pass
                
                # Build instruction
                if active_agent == "cipher":
                    profile = CIPHER_PROFILE
                    agent_tag = f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET}"
                elif active_agent == "echo":
                    profile = ECHO_PROFILE
                    agent_tag = f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET}"
                elif active_agent == "nano":
                    profile = NANO_PROFILE
                    agent_tag = f"{Colors.NEON_CYAN}[NANO]{Colors.RESET}"
                else:
                    profile = DAV1D_PROFILE
                    agent_tag = f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET}"
                
                # Agent switching commands that also set profile and model
                if cmd == "/dav1d":
                    active_agent = "dav1d"
                    profile = DAV1D_PROFILE
                    agent_tag = f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET}"
                    auto_model = True
                    print(f"{Colors.ELECTRIC_BLUE}[SYSTEM]{Colors.RESET} Back to DAV1D (Auto-Model: ON)")
                    continue
                
                if cmd.startswith("/banana"):
                    active_agent = "nano"
                    profile = NANO_PROFILE
                    agent_tag = f"{Colors.NEON_CYAN}[NANO]{Colors.RESET}"
                    auto_model = False
                    forced_model = "nano"
                    
                    msg = user_input[len("/banana"):].strip()
                    if msg:
                        user_input = msg # Process immediately
                    else:
                        print(f"{Colors.NEON_CYAN}[SYSTEM]{Colors.RESET} Switched to NANO BANANA 🍌")
                        continue
                
                # Add search protocol if searching
                search_protocol = ""
                if auto_model and analysis and analysis.requires_search:
                    search_protocol = """
[SEARCH PROTOCOL]
- You have Google Search enabled.
- For names/entities, search for the EXACT spelling provided (e.g. "Meralus" not "Morales").
- Use your knowledge of "Who Visions LLC" and "Dave Meralus" to refine search queries (e.g. search "Dave Meralus Who Visions").
- If results are ambiguous, clarify instead of hallucinating.
"""

                full_instruction = f"""{profile}
{search_protocol}
[MODEL] {MODELS[current_model]}

[TIME]
{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}

[MEMORY]
{relevant_context if relevant_context else "(No relevant memories)"}

[USER]
{user_input}

Respond as {active_agent.upper()}. Be direct and helpful.
"""
                
                try:
                    tools = []
                    
                    # Determine which tools to include based on the API constraint
                    if auto_model and analysis and analysis.requires_search:
                        # If search is required, only include GoogleSearch (and other *true* search tools if any)
                        tools.append(Tool(google_search=GoogleSearch()))
                        # Exclude all other CLI_TOOLS (including browse_webpage) in this case
                        
                    else:
                        # If no search is required, include CLI_TOOLS (which now includes browse_webpage)
                        if CLI_TOOLS:
                            tools.extend(CLI_TOOLS)
                        # Ensure GoogleSearch is NOT added in this branch
                    
                    from google.genai.types import ToolConfig, FunctionCallingConfig
                    
                    chat = client.chats.create(
                        model=MODELS[current_model],
                        config=GenerateContentConfig(
                            temperature=0.7,
                            tools=tools,
                            tool_config=ToolConfig(
                                function_calling_config=FunctionCallingConfig(
                                    mode="AUTO"
                                )
                            ),
                            safety_settings=safety_settings,
                            response_modalities=["TEXT"]
                        )
                    )
                    
                    # Send message and let SDK handle tool calls automatically
                    response = chat.send_message(full_instruction)
                    
                    message = response.text if hasattr(response, 'text') else str(response)
                    print(f"{agent_tag} {message}\n")
                    logger.log(active_agent.upper(), message, current_model, auto_model)
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"{Colors.NEON_RED}[ERROR] Interaction failed: {e}{Colors.RESET}\n")
                    continue
                
            except KeyboardInterrupt:
                print(f"\n{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Interrupted.")
                if logger.active:
                    logger.stop()
                break
    
    except Exception as e:
        print(f"\n{Colors.NEON_RED}[!] FAILED:{Colors.RESET} {e}")
        print(f"\nFix:")
        print(f"  1. gcloud auth application-default login")
        print(f"  2. gcloud config set project {PROJECT_ID}")
        print(f"  3. pip install google-cloud-aiplatform google-generativeai")

if __name__ == "__main__":
    main()
