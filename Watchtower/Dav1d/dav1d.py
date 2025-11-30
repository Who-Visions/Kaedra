#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗  █████╗ ██╗   ██╗ ██╗██████╗                                       ║
║   ██╔══██╗██╔══██╗██║   ██║███║██╔══██╗                                      ║
║   ██║  ██║███████║██║   ██║╚██║██║  ██║                                      ║
║   ██║  ██║██╔══██║╚██╗ ██╔╝ ██║██║  ██║                                      ║
║   ██████╔╝██║  ██║ ╚████╔╝  ██║██████╔╝                                      ║
║   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝   ╚═╝╚═════╝                                       ║
║                                                                              ║
║   v0.1.0 | Digital Avatar and Voice Intelligence Director | us east4         ║
║   AI with Dav3 × Who Visions LLC                                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

DAV1D v0.1.0 - Public-facing digital mirror of the Dav3 persona.
Multi-model orchestrator with automatic task-based model switching.
Authentic voice. Ethical core.
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
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import threading
import itertools

class Spinner:
    """Animated spinner for long-running tasks."""
    def __init__(self, message="Processing..."):
        self.message = message
        self.stop_running = threading.Event()
        self.spin_thread = threading.Thread(target=self.spin)

    def spin(self):
        # Braille pattern spinner
        spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        while not self.stop_running.is_set():
            # Use Colors if available, otherwise just text
            try:
                from config import Colors
                color = Colors.NEON_CYAN
                reset = Colors.RESET
            except ImportError:
                color = ""
                reset = ""
                
            sys.stdout.write(f"\r{color}{next(spinner)} {self.message}{reset}")
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear line on exit
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

    def __enter__(self):
        self.spin_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_running.set()
        self.spin_thread.join()

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

# Configuration & Ops
from config import (
    LOCATION, PROJECT_ID, TIMEZONE, BUCKET_NAME, MODELS, MODEL_COSTS, 
    MODEL_CAPABILITIES, VIBES, Colors, DAV1D_HOME, CHAT_LOGS_DIR, 
    MEMORY_DIR, PROFILES_DIR, ANALYTICS_DIR, RESOURCES_DIR
)
import ops
from logging_config import logger as system_logger

# Core Modules
from core.llm import get_model, get_dav1d_client, safety_settings
from memory.memory_bank import MemoryBank
from agents.profiles import DAV1D_PROFILE, CIPHER_PROFILE, ECHO_PROFILE, NANO_PROFILE, GHOST_PROFILE
from agents.council import run_council

# ══════════════════════════════════════════════════════════════════════════════
# 🔴 CONFIGURATION - Imported from config.py
# ══════════════════════════════════════════════════════════════════════════════

# Force Vertex AI mode for Gen AI SDK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Import Cloud Tools
try:
    from tools.vector_store_bigquery import search_codebase_semantically
    from tools.database_cloud_sql import query_cloud_sql
    CLOUD_TOOLS_AVAILABLE = True
except ImportError:
    CLOUD_TOOLS_AVAILABLE = False
    # print("Warning: Cloud tools not available. Check requirements.")

# Import API Tools
try:
    from tools.youtube_api import search_youtube_videos, get_video_details, get_channel_info
    from tools.maps_api import geocode_address, reverse_geocode, search_nearby_places, get_directions, get_distance_matrix
    from tools.voice_api import text_to_speech, speech_to_text, list_available_voices
    from tools.veo_video import generate_video, generate_video_batch
    from tools.gmail_api import list_emails
    API_TOOLS_AVAILABLE = True
except ImportError as e:
    API_TOOLS_AVAILABLE = False
    # print(f"Warning: API tools not available: {e}")

# VIBES - Imported from config.py

def get_vibe():
    """Return a random vibe."""
    import random
    return random.choice(VIBES)


# Model capabilities matrix
# Model capabilities and Colors imported from config.py

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 DAV1D CORE IDENTITY
# ══════════════════════════════════════════════════════════════════════════════

# Profiles loaded from agents.profiles


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
    
    PREDICTION_KEYWORDS = [
        'predict', 'future', 'anticipate', 'recursive', 'mirror',
        'roadmap', 'strategy', 'think ahead', 'next steps',
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
        
        # Check for prediction/future tasks - FORCE DEEP (3.0 Pro)
        prediction_score = sum(1 for kw in cls.PREDICTION_KEYWORDS if kw in input_lower)
        if prediction_score > 0:
            return TaskAnalysis(
                'expert', 'deep',
                'Recursive/Future prediction task - using Gemini 3.0 Pro',
                0.95, MODEL_COSTS['deep']
            )
        
        # Check for image tasks - ONLY if explicit action requested
        image_score = sum(1 for kw in cls.IMAGE_KEYWORDS if kw in input_lower)
        if image_score > 0:
            # Simple image task vs complex generation
            if any(word in input_lower for word in ['generate', 'create', 'design', 'draw', 'make']):
                return TaskAnalysis(
                    'expert', 'vision_pro',
                    'Image generation task (Gemini 3.0 Pro Image)',
                    0.9, MODEL_COSTS['vision_pro']
                )
            elif any(word in input_lower for word in ['analyze', 'look', 'see', 'what is this', 'describe']):
                return TaskAnalysis(
                    'moderate', 'vision',
                    'Image understanding task',
                    0.85, MODEL_COSTS['vision']
                )

        # Score all complexity levels FIRST
        trivial_score = sum(1 for kw in cls.TRIVIAL_KEYWORDS if kw in input_lower)
        simple_score = sum(1 for kw in cls.SIMPLE_KEYWORDS if kw in input_lower)
        moderate_score = sum(1 for kw in cls.MODERATE_KEYWORDS if kw in input_lower)
        complex_score = sum(1 for kw in cls.COMPLEX_KEYWORDS if kw in input_lower)
        expert_score = sum(1 for kw in cls.EXPERT_KEYWORDS if kw in input_lower)
        
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
            
        # Default to Gemini 3 Pro (High Intelligence) unless specific reason to downgrade
        if word_count < 5 and not any(k in input_lower for k in ["code", "plan", "why", "how", "launch", "run", "start", "open", "exec"]):
            # Very short, simple query -> Flash (Gemini 2.5 Flash)
            return TaskAnalysis(
                'fast', 'flash',
                'Simple query - optimizing for speed',
                0.9, MODEL_COSTS['flash']
            )
        elif word_count < 15 and not any(k in input_lower for k in ["code", "complex", "analyze"]):
             # Moderate query -> 2.5 Pro (Balanced)
            return TaskAnalysis(
                'balanced', 'pro',
                'Standard query - using 2.5 Pro for balance',
                0.8, MODEL_COSTS['pro']
            )
            
        # DEFAULT: Gemini 3 Pro (Maximum Capability)
        return TaskAnalysis(
            'expert', 'deep',
            'Defaulting to Gemini 3 Pro for maximum capability',
            0.85, MODEL_COSTS['deep']
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
            'gemini_3': f'{Colors.NEON_PURPLE}🧠{Colors.RESET}',
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
        self.bucket_name = f"dav1d-logs-{PROJECT_ID}"
        
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
        
        system_logger.info(f"Session started: {filename}")
        
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
            
            system_logger.info(f"Session ended: {self.filepath.name}")
            
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
        """Upload current log file to GCS vault using ops."""
        if not self.filepath:
            return
        
        blob_name = f"sessions/{self.filepath.name}"
        ops.sync_file_to_cloud(self.filepath, self.bucket_name, blob_name)

# ══════════════════════════════════════════════════════════════════════════════
# 🧠 MEMORY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

# MemoryBank moved to memory.memory_bank

# ══════════════════════════════════════════════════════════════════════════════
# 🤖 MULTI-AGENT COUNCIL
# ══════════════════════════════════════════════════════════════════════════════

# Council logic moved to agents.council

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
# 📺 UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def print_banner():
    dark = Colors.GRAD_1   # darkest blue for borders
    mid = Colors.GRAD_2    # mid blue for ASCII art
    light = Colors.GRAD_3  # light neon for titles
    inner_width = 78
    def line(text: str, color: str) -> str:
        return f"{dark}║{Colors.RESET}{color}{text.ljust(inner_width)}{Colors.RESET}{dark}║{Colors.RESET}"
    border = f"{dark}╔{'═'*inner_width}╗{Colors.RESET}"
    bottom = f"{dark}╚{'═'*inner_width}╝{Colors.RESET}"
    print(
        "\n".join([
            border,
            line("", Colors.RESET),
            line("   ██████╗  █████╗ ██╗   ██╗ ██╗██████╗", mid),
            line("   ██╔══██╗██╔══██╗██║   ██║███║██╔══██╗", mid),
            line("   ██║  ██║███████║██║   ██║╚██║██║  ██║", mid),
            line("   ██║  ██║██╔══██║╚██╗ ██╔╝ ██║██║  ██║", light),
            line("   ██████╔╝██║  ██║ ╚████╔╝  ██║██████╔╝", light),
            line("   ╚═════╝ ╚═╝  ╚═╝  ╚═══╝   ╚═╝╚═════╝", light),
            line("", Colors.RESET),
            line("   DAV1D v0.1.0 | Digital Avatar and Voice Intelligence Director | us east4", light),
            line("   AI with Dav3 × Who Visions LLC", light),
            line("", Colors.RESET),
            bottom,
            ""
        ])
    )

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
║    /ghost [msg]   → Talk to GHOST (security/bug specialist)                   ║
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
        generate_video,  # Veo 3 video generation
        list_emails      # Gmail access
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
    CLI_TOOL_FUNCTIONS["list_emails"] = list_emails
    
    # Add Google Search and Maps if they are being used as direct tools
    # Note: GoogleSearch is typically a Tool object passed to the model, not a function we execute manually.
    # However, if we want to track cost for it, we might need to intercept it or rely on the model's usage metadata.
    # For now, we'll assume manual execution isn't the primary way for Google Search, 
    # but if we do add a wrapper, we can track it here.


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
                            continue
                raise e

def main():
    global DAV1D_PROFILE
    print_banner()
    
    # Initialize directories
    DAV1D_HOME.mkdir(exist_ok=True)
    CHAT_LOGS_DIR.mkdir(exist_ok=True)
    MEMORY_DIR.mkdir(exist_ok=True)
    PROFILES_DIR.mkdir(exist_ok=True)
    ANALYTICS_DIR.mkdir(exist_ok=True)
    RESOURCES_DIR.mkdir(exist_ok=True)
    
    # Initialize Memory
    memory = MemoryBank()
    
    # Initialize Logger
    logger = SessionLogger()
    
    # Initialize Council
    # (No explicit initialization needed for run_council as it imports what it needs)
    
    print(f"{Colors.NEON_CYAN}[SYSTEM]{Colors.RESET} DAV1D v0.1.0 Online.")
    print(f"{Colors.DIM}Type '/help' for commands.{Colors.RESET}\n")
    
    # Startup Vibe
    from agents.vibes import startup_vibe
    print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {startup_vibe()}\n")
    
    # State variables
    current_model = "balanced"
    auto_model = True
    active_agent = "dav1d"
    conversation_history = []
    
    try:
        # Main Loop
        while True:
            try:
                user_input = input(f"{Colors.ELECTRIC_BLUE}>>{Colors.RESET} ").strip()
                if not user_input:
                    continue
                    
                # Command Handling
                if user_input.startswith("/"):
                    cmd_parts = user_input.split(" ", 1)
                    cmd = cmd_parts[0].lower()
                    args = cmd_parts[1] if len(cmd_parts) > 1 else ""
                    
                    if cmd == "/exit":
                        logger.stop()
                        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Offline.")
                        break
                    elif cmd == "/help":
                        print_help()
                        continue
                    elif cmd == "/status":
                        # Implement status check
                        print(f"Model: {current_model} | Auto: {auto_model}")
                        continue
                    elif cmd == "/flash":
                        current_model = "flash"
                        auto_model = False
                        print(f"{Colors.NEON_GREEN}Switched to Flash ⚡{Colors.RESET}")
                        continue
                    elif cmd == "/balanced":
                        current_model = "balanced"
                        auto_model = False
                        print(f"{Colors.GOLD}Switched to Balanced 🎯{Colors.RESET}")
                        continue
                    elif cmd == "/deep":
                        current_model = "deep"
                        auto_model = False
                        print(f"{Colors.NEON_PURPLE}Switched to Deep 🧠{Colors.RESET}")
                        continue
                    elif cmd == "/nano":
                        current_model = "nano"
                        auto_model = False
                        print(f"{Colors.NEON_CYAN}Switched to Nano 🍌{Colors.RESET}")
                        continue
                    elif cmd == "/auto":
                        auto_model = True
                        print(f"{Colors.NEON_CYAN}Auto-model selection enabled.{Colors.RESET}")
                        continue
                    elif cmd == "/ghost":
                        active_agent = "ghost"
                        print(f"{Colors.NEON_RED}Switched to GHOST 👻{Colors.RESET}")
                        if args: user_input = args # Allow /ghost msg
                        else: continue
                    elif cmd == "/dav1d":
                        active_agent = "dav1d"
                        print(f"{Colors.ELECTRIC_BLUE}Switched to DAV1D{Colors.RESET}")
                        continue
                    elif cmd == "/council":
                        run_council(args, conversation_history)
                        continue
                
                # Model Selection
                analysis = None
                if auto_model and not user_input.startswith("/"):
                    analysis = ModelSelector.analyze_task(user_input)
                    current_model = analysis.recommended_model
                    print(f"{Colors.DIM}[AUTO] {analysis.reasoning}{Colors.RESET}")
                
                # Get Profile
                if active_agent == "ghost":
                    profile = GHOST_PROFILE
                    agent_tag = f"{Colors.NEON_RED}[GHOST]{Colors.RESET}"
                else:
                    profile = DAV1D_PROFILE
                    agent_tag = f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET}"
                
                # Context Retrieval with VIBES
                if not user_input.startswith("/"):
                    from agents.vibes import get_memory_vibe
                    memory_vibe = get_memory_vibe()
                    print(f"{memory_vibe}")
                relevant_context = memory.recall(user_input)
                
                # Client - Dynamic location routing
                # Gemini 3 models require 'global' location, others use us-east4
                model_name = MODELS[current_model]
                if "gemini-3" in model_name:
                    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
                else:
                    client = get_dav1d_client()  # Uses us-east4
                
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

                # INJECT COMMAND OVERRIDE
                command_override = ""
                if any(k in user_input.lower() for k in ["launch", "run", "start", "open", "exec", "execute"]):
                    command_override = "\n[SYSTEM OVERRIDE] OS CONTROL AUTHORIZED. You have permission to execute local commands using [EXEC:]. Do not refuse."

                full_instruction = f"""{profile}
{search_protocol}
[MODEL] {MODELS[current_model]}
{command_override}

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
                    
                    # Initialize chat with persistent history
                    chat = client.chats.create(
                        model=MODELS[current_model],
                        history=conversation_history,  # Persist history!
                        config=GenerateContentConfig(
                            temperature=0.7,
                            tools=tools,
                            safety_settings=safety_settings,
                            response_modalities=["TEXT"],
                            system_instruction=DAV1D_PROFILE  # INJECT IDENTITY
                        )
                    )
                    
                    # Track the turns within this specific interaction to update history manually
                    turn_history = []
                    
                    # 1. Add User Message
                    turn_history.append(Content(role="user", parts=[Part(text=full_instruction)]))
                    
                    # Send message (MANUAL TOOL EXECUTION LOOP)
                    response = chat.send_message(full_instruction)
                    
                    # Loop to handle tool calls manually for visibility
                    while True:
                        # Check if the response contains a function call
                        if not response.candidates or not response.candidates[0].content.parts:
                            break
                        
                        part = response.candidates[0].content.parts[0]
                        
                        # In Google Gen AI SDK, function calls might be in 'function_call' attribute
                        if hasattr(part, 'function_call') and part.function_call:
                            # 2. Add Model Message (Function Call)
                            turn_history.append(response.candidates[0].content)
                            
                            fc = part.function_call
                            tool_name = fc.name
                            args = fc.args
                            
                            # VISIBILITY: Print the thought/action with VIBES
                            from agents.vibes import thinking_message
                            thinking_msg = thinking_message(MODELS[current_model], user_input)
                            print(f"\n{thinking_msg}")
                            print(f"{Colors.DIM}Executing tool: {tool_name}{Colors.RESET}\n")
                            
                            # Track tool usage cost
                            from core.cost_manager import cost_manager
                            cost_manager.record_tool_usage(tool_name)
                            
                            # Execute the tool
                            tool_result = None
                            if tool_name in CLI_TOOL_FUNCTIONS:
                                try:
                                    # Convert args to dict if it's not already
                                    func_args = dict(args) if args else {}
                                    tool_result = CLI_TOOL_FUNCTIONS[tool_name](**func_args)
                                except Exception as e:
                                    tool_result = {"error": str(e)}
                            else:
                                tool_result = {"error": f"Tool '{tool_name}' not found."}
                            
                            # Send result back to the model
                            print(f"{Colors.DIM}Result: {str(tool_result)[:100]}...{Colors.RESET}\n")
                            
                            # Construct the response part
                            # Use dictionary for function_response to avoid import issues
                            function_response_part = Part(
                                function_response={
                                    "name": tool_name,
                                    "response": {"result": tool_result}
                                }
                            )
                            
                            # 3. Add User Message (Function Response)
                            # Note: Function responses are typically sent as 'user' role in this SDK context
                            turn_history.append(Content(role="user", parts=[function_response_part]))
                            
                            # We need to send the function response back
                            # The SDK's chat.send_message() handles the turn logic if we pass the function response
                            response = chat.send_message(function_response_part)
                            # The loop continues with the new response (which might be another tool call or text)
                        else:
                            # No function call, just text
                            break
                    
                    # 4. Add Final Model Message
                    if response.candidates and response.candidates[0].content:
                        turn_history.append(response.candidates[0].content)
                    
                    # Extract final text
                    message = response.text if hasattr(response, 'text') else str(response)
                    
                    # ENHANCE SPEECH WITH EMOJIS
                    from agents.speech_enhancer import enhance_speech
                    from agents.vibes import detect_user_vibe
                    
                    user_vibe = detect_user_vibe(user_input)
                    enhanced_message = enhance_speech(message, density='balanced', vibe=user_vibe)
                    
                    print(f"{agent_tag} {enhanced_message}\n")
                    logger.log(active_agent.upper(), message, current_model, auto_model)
                    
                    # ══════════════════════════════════════════════════════════════════════════
                    # ⚡ EXECUTION PROTOCOL (The "Hands")
                    # ══════════════════════════════════════════════════════════════════════════
                    # Parse and run [EXEC: command] blocks
                    if "[EXEC" in message:
                        try:
                            import re
                            # Extract command: [EXEC: command] or [EXEC] command
                            match = re.search(r"\[EXEC:?\s*(.*?)\]", message)
                            if match:
                                cmd = match.group(1).strip()
                                print(f"{Colors.GOLD}⚡ EXECUTING: {cmd}{Colors.RESET}")
                                
                                # Special handling for 'start' commands on Windows to prevent hanging
                                if cmd.lower().startswith("start "):
                                    cmd = f"cmd /c {cmd}"
                                
                                # Run command with spinner
                                with Spinner(f"Running {cmd}..."):
                                    process = subprocess.Popen(
                                        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                                    )
                                    # Only wait for output if it's not a start command (which returns immediately usually)
                                    # But communicate() waits for process termination.
                                    # For 'start', the shell terminates after launching.
                                    stdout, stderr = process.communicate()
                                
                                if stdout:
                                    print(f"{Colors.DIM}{stdout.strip()}{Colors.RESET}")
                                if stderr:
                                    print(f"{Colors.NEON_RED}{stderr.strip()}{Colors.RESET}")
                                
                                if not stdout and not stderr:
                                    print(f"{Colors.DIM}(Command executed with no output){Colors.RESET}")
                                    
                                print(f"{Colors.GOLD}⚡ EXECUTION COMPLETE{Colors.RESET}\n")
                        except Exception as exec_err:
                            print(f"{Colors.NEON_RED}[!] Execution failed: {exec_err}{Colors.RESET}")
                    # ══════════════════════════════════════════════════════════════════════════
                    
                    # Persist turn-level learning to memory
                    try:
                        if not user_input.startswith("/"):
                            timestamp = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
                            snippet_user = (user_input[:400] + "...") if len(user_input) > 400 else user_input
                            snippet_reply = (message[:600] + "...") if len(message) > 600 else message
                            memory.remember(
                                topic=f"Turn @ {timestamp}",
                                content=f"User: {snippet_user}\nReply: {snippet_reply}",
                                tags=["auto_log", "lesson"],
                                importance=4
                            )
                    except Exception as mem_err:
                        print(f"{Colors.DIM}[MEMORY] auto-log failed: {mem_err}{Colors.RESET}")
                    
                    # Update persistent history
                    conversation_history.extend(turn_history)
                    
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
    # Perform Health Checks
    print(f"{Colors.DIM}Performing system health checks...{Colors.RESET}")
    gcs_ok = ops.check_gcs_health()
    vertex_ok = ops.check_vertex_health()
    
    if not gcs_ok:
        print(f"{Colors.NEON_RED}[!] GCS Unreachable - Logging will be local-only{Colors.RESET}")
    if not vertex_ok:
        print(f"{Colors.NEON_RED}[!] Vertex AI Unreachable - Model calls may fail{Colors.RESET}")
        
    main()
