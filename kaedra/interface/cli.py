"""
KAEDRA v0.0.6 - Command Line Interface
Main CLI entry point with command parsing and dispatch.
"""

import sys
import random
import platform
import warnings
import subprocess
from datetime import datetime
from typing import Optional

import vertexai

# Suppress known Vertex AI deprecation warning from SDK
warnings.filterwarnings(
    "ignore",
    message="This feature is deprecated as of June 24, 2025",
    category=UserWarning,
    module=r"vertexai\..*",
)

from ..core.version import __version__, __codename__
from ..core.config import (
    Colors, MODELS, MODEL_COSTS, DEFAULT_MODEL,
    VEO_MODELS, DEFAULT_VEO_MODEL,
    LOCATION, AGENT_RESOURCE_NAME,
    THINKING_MESSAGES, LYRICS_DB, STARTUP_VIBES, RANDOM_FACTS
)
from ..services.memory import MemoryService
from ..services.logging import LoggingService
from ..services.prompt import PromptService
from ..services.web import WebService
from ..services import VIDEO_AVAILABLE, VideoService
from ..agents.kaedra import KaedraAgent
from ..agents.blade import BladeAgent
from ..agents.nyx import NyxAgent
from ..strategies.tree_of_thought import TreeOfThoughtsStrategy
from ..strategies.battle_of_bots import BattleOfBotsStrategy
from ..strategies.presets import PromptOptimizer


def print_banner():
    """Print the KAEDRA startup banner."""
    print(f"""
{Colors.GRAD_PURPLE}╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   {Colors.GRAD_PURPLE}██╗  ██╗ {Colors.GRAD_PINK}█████╗ {Colors.GRAD_PINK}███████╗{Colors.GRAD_BLUE}██████╗ {Colors.GRAD_BLUE}██████╗  {Colors.GRAD_GOLD}█████╗{Colors.GRAD_PURPLE}                             ║
║   {Colors.GRAD_PURPLE}██║ ██╔╝{Colors.GRAD_PINK}██╔══██╗{Colors.GRAD_PINK}██╔════╝{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_GOLD}██╔══██╗{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}█████╔╝ {Colors.GRAD_PINK}███████║{Colors.GRAD_PINK}█████╗  {Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_BLUE}██████╔╝{Colors.GRAD_GOLD}███████║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}██╔═██╗ {Colors.GRAD_PINK}██╔══██║{Colors.GRAD_PINK}██╔══╝  {Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_GOLD}██╔══██║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}██║  ██╗{Colors.GRAD_PINK}██║  ██║{Colors.GRAD_PINK}███████╗{Colors.GRAD_BLUE}██████╔╝{Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_GOLD}██║  ██║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}╚═╝  ╚═╝{Colors.GRAD_PINK}╚═╝  ╚═╝{Colors.GRAD_PINK}╚══════╝{Colors.GRAD_BLUE}╚═════╝ {Colors.GRAD_BLUE}╚═╝  ╚═╝{Colors.GRAD_GOLD}╚═╝  ╚═╝{Colors.GRAD_PURPLE}                            ║
║                                                                               ║
║   {Colors.GRAD_BLUE}v{__version__} | {__codename__} | {LOCATION}{Colors.GRAD_PURPLE}                                        ║
║   {Colors.GRAD_GOLD}Who Visions LLC{Colors.GRAD_PURPLE}                                                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)


def print_banner():
    """Print the KAEDRA startup banner."""
    print(f"""
{Colors.GRAD_PURPLE}╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   {Colors.GRAD_PURPLE}██╗  ██╗ {Colors.GRAD_PINK}█████╗ {Colors.GRAD_PINK}███████╗{Colors.GRAD_BLUE}██████╗ {Colors.GRAD_BLUE}██████╗  {Colors.GRAD_GOLD}█████╗{Colors.GRAD_PURPLE}                             ║
║   {Colors.GRAD_PURPLE}██║ ██╔╝{Colors.GRAD_PINK}██╔══██╗{Colors.GRAD_PINK}██╔════╝{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_GOLD}██╔══██╗{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}█████╔╝ {Colors.GRAD_PINK}███████║{Colors.GRAD_PINK}█████╗  {Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_BLUE}██████╔╝{Colors.GRAD_GOLD}███████║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}██╔═██╗ {Colors.GRAD_PINK}██╔══██║{Colors.GRAD_PINK}██╔══╝  {Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_BLUE}██╔══██╗{Colors.GRAD_GOLD}██╔══██║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}██║  ██╗{Colors.GRAD_PINK}██║  ██║{Colors.GRAD_PINK}███████╗{Colors.GRAD_BLUE}██████╔╝{Colors.GRAD_BLUE}██║  ██║{Colors.GRAD_GOLD}██║  ██║{Colors.GRAD_PURPLE}                            ║
║   {Colors.GRAD_PURPLE}╚═╝  ╚═╝{Colors.GRAD_PINK}╚═╝  ╚═╝{Colors.GRAD_PINK}╚══════╝{Colors.GRAD_BLUE}╚═════╝ {Colors.GRAD_BLUE}╚═╝  ╚═╝{Colors.GRAD_GOLD}╚═╝  ╚═╝{Colors.GRAD_PURPLE}                            ║
║                                                                               ║
║   {Colors.GRAD_BLUE}v{__version__} | {__codename__} | {LOCATION}{Colors.GRAD_PURPLE}                                        ║
║   {Colors.GRAD_GOLD}Who Visions LLC{Colors.GRAD_PURPLE}                                                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)


def print_help():
    """Print command reference."""
    print(f"""
{Colors.GOLD}╔═══════════════════════════════════════════════════════════════════════════════╗
║  KAEDRA v{__version__} - COMMAND REFERENCE                                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  MODEL SWITCHING                                                              ║
║    /flash      → Gemini 2.5 Flash (~$0.008) ⚡ FAST                            ║
║    /pro        → Gemini 2.5 Pro (~$0.031) 🎯 BALANCED                         ║
║    /ultra      → Gemini 3 Pro Preview (~$0.038) 🔥 POWERFUL                   ║
║    /models     → Show available models                                        ║
║                                                                               ║
║  AGENT COMMUNICATION                                                          ║
║    /blade [msg]    → Talk to BLADE (aggressive analyst)                       ║
║    /nyx [msg]      → Talk to NYX (strategic observer)                         ║
║    /kaedra         → Switch back to KAEDRA                                    ║
║    /council [task] → Multi-agent council discussion                           ║
║                                                                               ║
║  ADVANCED PROMPTING                                                           ║
║    /tot [task]     → Tree of Thought (multi-path analysis)                    ║
║    /battle [task]  → Battle of Bots (adversarial validation)                  ║
║    /optimize [p]   → Optimize your prompts                                    ║
║    /presets        → List available prompt presets                            ║
║                                                                               ║
║  MEMORY SYSTEM                                                                ║
║    /remember       → Store long-term context                                  ║
║    /recall [query] → Search memory bank                                       ║
║    /context        → List recent memories                                     ║
║                                                                               ║
  ║  WEB TOOLS                                                                    ║
  ║    /fetch [url]    → Fetch and read any webpage                              ║
  ║    /search [query] → Web search (uses Vertex AI grounding)                    ║
  ║                                                                               ║
  ║  VIDEO GENERATION                                                             ║
  ║    /video [prompt] → Generate video from text (Veo 3.1)                      ║
  ║    /videoimg [p]   → Generate image first, then video                         ║
  ║    /extend [file]  → Extend existing video                                    ║
  ║    /veomodel       → Show/switch Veo models                                   ║
  ║                                                                               ║
  ║  LOGGING                                                                      ║
║    /startlog       → Begin session logging                                    ║
║    /stoplog        → Stop logging and save                                    ║
║                                                                               ║
║  SYSTEM                                                                       ║
║    /status         → Check system health                                      ║
║    /caps           → Show capabilities                                        ║
║    /help           → Show this reference                                      ║
║    /exit           → Disconnect                                               ║
║                                                                               ║
║  COST GUIDE (per ~2000 token query)                                           ║
║    Flash: ~$0.008  │  Pro: ~$0.031  │  Ultra: ~$0.038                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝{Colors.RESET}
    """)


def startup_vibe() -> str:
    """Generate a random startup message."""
    roll = random.random()
    hour = datetime.now().hour
    
    if hour < 12:
        time_vibe = "Morning grind."
    elif hour < 18:
        time_vibe = "Afternoon flow."
    else:
        time_vibe = "Late night lab."
    
    if roll < 0.3:
        return f"🎵 {random.choice(LYRICS_DB)} 🎵"
    elif roll < 0.5:
        return f"{time_vibe} {random.choice(RANDOM_FACTS)} So, what's the move?"
    else:
        return random.choice(STARTUP_VIBES)


def thinking_message(model: str) -> str:
    """Generate a random thinking message."""
    if random.random() < 0.2:
        return f"🎵 {random.choice(LYRICS_DB)} 🎵 ({model})"
    return random.choice(THINKING_MESSAGES).format(model=model)


def run_council(query: str, kaedra: KaedraAgent, blade: BladeAgent, nyx: NyxAgent) -> str:
    """Run a multi-agent council discussion."""
    print(f"\n{Colors.GOLD}[COUNCIL INITIATED]{Colors.RESET}")
    print(f"{Colors.DIM}Convening: KAEDRA, BLADE, NYX{Colors.RESET}\n")
    
    # BLADE first
    print(f"{Colors.blade_tag()} Analyzing for action...")
    blade_response = blade.run_sync(query)
    print(f"{Colors.blade_tag()} {blade_response.content}\n")
    
    # NYX second
    print(f"{Colors.nyx_tag()} Analyzing for risk...")
    nyx_context = f"BLADE's Analysis: {blade_response.content}"
    nyx_response = nyx.run_sync(query, context=nyx_context)
    print(f"{Colors.nyx_tag()} {nyx_response.content}\n")
    
    # KAEDRA synthesizes
    print(f"{Colors.kaedra_tag()} Synthesizing...")
    synthesis_context = f"""BLADE's Position: {blade_response.content}

NYX's Position: {nyx_response.content}

You're the ORCHESTRATOR. You've heard from your advisors. Make the call.
Think through:
1. Where do they agree?
2. Where do they disagree, and why?
3. What's the balanced path?
4. What's your final call?

Respond in 3-5 sentences. Acknowledge both perspectives, state your decision, give the final directive."""
    
    kaedra_response = kaedra.run_sync(query, context=synthesis_context)
    print(f"{Colors.kaedra_tag()} {kaedra_response.content}\n")
    print(f"{Colors.GOLD}[COUNCIL CONCLUDED]{Colors.RESET}\n")
    
    return kaedra_response.content


def format_sysinfo() -> str:
    """Return a formatted system information string."""
    info = platform.uname()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    python_version = platform.python_version()
    lines = [
        f"Timestamp:   {timestamp}",
        f"OS:          {info.system} {info.release} ({info.version})",
        f"Hostname:    {info.node}",
        f"Architecture:{info.machine}",
        f"Processor:   {info.processor or 'Unknown'}",
        f"Python:      {python_version}",
        f"Location:    {LOCATION}",
    ]
    return "\n".join(lines)


def handle_internal_exec(command: str) -> bool:
    """Handle internal EXEC commands without spawning subprocesses."""
    normalized = command.strip().lower()
    if normalized in {"sysinfo", "sys-info", "systeminfo", "system-info"}:
        print(f"{Colors.system_tag()} System Information")
        print(format_sysinfo())
        return True
    return False


def main():
    """Main CLI entry point."""
    # Force UTF-8 for Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    print_banner()
    
    # Initialize Vertex AI
    print(f"{Colors.DIM}[*] Connecting to {LOCATION}...{Colors.RESET}")
    vertexai.init(location=LOCATION)
    
    # Initialize services
    memory = MemoryService()
    logger = LoggingService()
    prompt = PromptService(model_key=DEFAULT_MODEL)
    web = WebService()
    
    # Initialize video service (optional)
    video = None
    if VIDEO_AVAILABLE and VideoService:
        try:
            video = VideoService(model_key=DEFAULT_VEO_MODEL)
            print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Video generation: READY")
        except Exception as e:
            print(f"{Colors.DIM}[!] Video generation unavailable: {e}{Colors.RESET}")
    
    # Initialize agents
    kaedra = KaedraAgent(prompt, memory)
    blade = BladeAgent(prompt, memory)
    nyx = NyxAgent(prompt, memory)
    
    # Initialize strategies
    tot = TreeOfThoughtsStrategy(prompt)
    battle = BattleOfBotsStrategy(prompt)
    optimizer = PromptOptimizer(prompt)
    
    # Session state
    current_model = DEFAULT_MODEL
    current_veo_model = DEFAULT_VEO_MODEL if VIDEO_AVAILABLE else None
    active_agent = "kaedra"
    
    print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} LINK ESTABLISHED")
    print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} KAEDRA v{__version__} ONLINE")
    print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Location: {LOCATION}")
    print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Model: {MODELS[current_model]}")
    print(f"    Type /help for commands\n")
    
    # Startup vibe
    print(f"{Colors.kaedra_tag()} {startup_vibe()}\n")
    
    try:
        while True:
            try:
                user_input = input(
                    f"{Colors.NEON_CYAN}[YOU|{Colors.NEON_GREEN}{current_model}{Colors.NEON_CYAN}] >> {Colors.RESET}"
                ).strip()
                
                if not user_input:
                    continue
                
                # Log user input
                logger.log_message("YOU", user_input, MODELS[current_model])
                
                cmd = user_input.lower()
                
                # ══════════════════════════════════════════════════════════
                # SYSTEM COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd == "/exit":
                    if logger.is_session_active:
                        logger.stop_session()
                    print(f"{Colors.kaedra_tag()} Severing link. Until next time, Commander.")
                    break
                
                if cmd == "/help":
                    print_help()
                    continue
                
                # Model switching
                if cmd == "/flash":
                    current_model = "flash"
                    prompt.set_model(current_model)
                    print(f"{Colors.system_tag()} ⚡ Model: {MODELS[current_model]}")
                    print(f"         Cost: ~${MODEL_COSTS[current_model]}/query | Speed: FAST")
                    continue
                
                if cmd == "/pro":
                    current_model = "pro"
                    prompt.set_model(current_model)
                    print(f"{Colors.system_tag()} 🎯 Model: {MODELS[current_model]}")
                    print(f"         Cost: ~${MODEL_COSTS[current_model]}/query | Balance: OPTIMAL")
                    continue
                
                if cmd == "/ultra":
                    current_model = "ultra"
                    prompt.set_model(current_model)
                    print(f"{Colors.system_tag()} 🔥 Model: {MODELS[current_model]}")
                    print(f"         Cost: ~${MODEL_COSTS[current_model]}/query | Power: MAXIMUM")
                    continue
                
                if cmd in ["/models", "/status"]:
                    print(f"\n{Colors.GOLD}[SYSTEM STATUS]{Colors.RESET}")
                    print(f"  Version: v{__version__}")
                    print(f"  Location: {LOCATION}")
                    print(f"  Active Model: {MODELS[current_model]} ({current_model})")
                    print(f"  Active Agent: {active_agent.upper()}")
                    print(f"  Logging: {'ON' if logger.is_session_active else 'OFF'}")
                    print(f"\n  Available Models:")
                    for k, v in MODELS.items():
                        marker = " ← ACTIVE" if k == current_model else ""
                        print(f"    • {k}: {v}{marker}")
                    print()
                    continue
                
                if cmd == "/caps":
                    print(f"\n{Colors.GOLD}[KAEDRA v{__version__} CAPABILITIES]{Colors.RESET}")
                    print(f"\n  🧠 AI/ML: Vertex AI, Gemini (Flash/Pro/Ultra), Vision, Speech, TTS")
                    print(f"  🔥 Firebase: Hosting, RTDB, Storage, Auth, FCM")
                    print(f"  🗺️  Maps: Geocoding, Directions, Places, Routes")
                    print(f"  🌤️  Weather: Weather API, Air Quality, Solar")
                    print(f"  📧 Workspace: Gmail, Drive, Sheets, Calendar, Docs")
                    print(f"  📸 Media: YouTube, Photos, Vision AI")
                    print(f"  ☁️  Infrastructure: Compute, Storage, Pub/Sub, Cloud Run")
                    print(f"\n  115+ APIs enabled. Ready for integration.\n")
                    continue
                
                # Logging
                if cmd == "/startlog":
                    if not logger.is_session_active:
                        filepath = logger.start_session(__version__, LOCATION)
                        print(f"{Colors.system_tag()} 📝 Logging started: {filepath}")
                    else:
                        print(f"{Colors.system_tag()} Logging already active.")
                    continue
                
                if cmd == "/stoplog":
                    if logger.is_session_active:
                        filepath = logger.stop_session()
                        print(f"{Colors.system_tag()} 💾 Log saved: {filepath}")
                    else:
                        print(f"{Colors.system_tag()} No active log session.")
                    continue
                
                # ══════════════════════════════════════════════════════════
                # MEMORY COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd == "/remember":
                    print(f"\n{Colors.NEON_PURPLE}[MEMORY]{Colors.RESET} Storing context...")
                    topic = input("  Topic: ").strip()
                    content = input("  Content: ").strip()
                    tags_input = input("  Tags (comma-separated): ").strip()
                    
                    if topic and content:
                        tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                        mem_id = memory.insert(content, topic, tags)
                        print(f"  ✓ Stored: {mem_id}")
                    else:
                        print("  ✗ Aborted: Topic and Content required")
                    continue
                
                if cmd.startswith("/recall"):
                    query = cmd[7:].strip() or input("  Search: ").strip()
                    if query:
                        results = memory.recall(query)
                        print(f"\n{Colors.NEON_PURPLE}[MEMORY]{Colors.RESET} Found {len(results)} matches:\n")
                        for i, res in enumerate(results, 1):
                            date = res['timestamp'].split('T')[0]
                            print(f"  {i}. {res['topic']} ({date})")
                            print(f"     {res['content'][:100]}...")
                            if res['tags']:
                                print(f"     Tags: {', '.join(res['tags'])}")
                            print()
                    continue
                
                if cmd == "/context":
                    recent = memory.list_recent()
                    print(f"\n{Colors.NEON_PURPLE}[RECENT MEMORIES]{Colors.RESET}\n")
                    for res in recent:
                        date = res['timestamp'].split('T')[0]
                        print(f"  • {res['topic']} ({date})")
                    print()
                    continue
                
                # ══════════════════════════════════════════════════════════
                # WEB COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd.startswith("/fetch "):
                    url = user_input[7:].strip()
                    if not url:
                        print(f"{Colors.system_tag()} Usage: /fetch <url>")
                        continue
                    
                    print(f"\n{Colors.NEON_CYAN}[WEB FETCH]{Colors.RESET} Fetching {url}...")
                    page = web.fetch(url)
                    
                    if page.status_code > 0:
                        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} {page.title}")
                        print(f"{Colors.DIM}Content preview (first 500 chars):{Colors.RESET}\n")
                        print(page.content[:500])
                        print(f"\n{Colors.DIM}...{len(page.content)} total characters{Colors.RESET}")
                        
                        # Feed to KAEDRA for analysis
                        web_context = f"[WEB PAGE: {url}]\nTitle: {page.title}\n\n{page.content[:2000]}"
                        print(f"\n{Colors.kaedra_tag()} Analyzing the page...")
                        response = kaedra.run_sync(
                            f"I fetched this webpage: {url}. Summarize the key points.",
                            context=web_context
                        )
                        print(f"{Colors.kaedra_tag()} {response.content}\n")
                        logger.log_message("WEB FETCH", page.content[:1000], MODELS[current_model])
                    else:
                        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {page.content}")
                    continue
                
                if cmd.startswith("/search "):
                    query = user_input[8:].strip()
                    if not query:
                        print(f"{Colors.system_tag()} Usage: /search <query>")
                        continue
                    
                    print(f"\n{Colors.NEON_CYAN}[WEB SEARCH]{Colors.RESET} Searching for: {query}")
                    print(f"{Colors.DIM}Using Vertex AI Google Search grounding...{Colors.RESET}\n")
                    
                    # Use KAEDRA with grounding for search
                    print(f"{Colors.kaedra_tag()} Searching...")
                    response = kaedra.run_sync(f"Search the web and tell me about: {query}")
                    print(f"{Colors.kaedra_tag()} {response.content}\n")
                    logger.log_message("WEB SEARCH", response.content, response.model)
                    continue
                
                # ══════════════════════════════════════════════════════════
                # VIDEO GENERATION COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd.startswith("/video ") and video:
                    prompt = user_input[7:].strip()
                    if not prompt:
                        print(f"{Colors.system_tag()} Usage: /video <prompt>")
                        continue
                    
                    print(f"\n{Colors.NEON_PURPLE}[VIDEO GENERATION]{Colors.RESET}")
                    print(f"  Model: {video.model}")
                    print(f"  Prompt: {prompt[:80]}...")
                    print(f"\n{Colors.DIM}Starting generation (this may take several minutes)...{Colors.RESET}\n")
                    
                    try:
                        result = video.generate_video(prompt)
                        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Video generated!")
                        print(f"  File: {result.file_path}")
                        print(f"  Duration: {result.duration_seconds:.1f}s")
                        print(f"  Model: {result.model}\n")
                        logger.log_message("VIDEO", f"Generated: {result.file_path}", result.model)
                    except Exception as e:
                        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {e}\n")
                    continue
                
                if cmd.startswith("/videoimg ") and video:
                    prompt = user_input[10:].strip()
                    if not prompt:
                        print(f"{Colors.system_tag()} Usage: /videoimg <prompt>")
                        continue
                    
                    print(f"\n{Colors.NEON_PURPLE}[VIDEO GENERATION - WITH IMAGE]{Colors.RESET}")
                    print(f"  Step 1: Generating image with Nano Banana...")
                    print(f"  Step 2: Generating video with {video.model}...")
                    print(f"\n{Colors.DIM}This may take several minutes...{Colors.RESET}\n")
                    
                    try:
                        result = video.generate_video_with_image(prompt)
                        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Video generated!")
                        print(f"  File: {result.file_path}")
                        print(f"  Duration: {result.duration_seconds:.1f}s")
                        print(f"  Model: {result.model}\n")
                        logger.log_message("VIDEO", f"Generated with image: {result.file_path}", result.model)
                    except Exception as e:
                        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {e}\n")
                    continue
                
                if cmd.startswith("/extend ") and video:
                    parts = user_input[8:].strip().split(" ", 1)
                    if len(parts) < 2:
                        print(f"{Colors.system_tag()} Usage: /extend <video_file> <extension_prompt>")
                        continue
                    
                    video_file = parts[0].strip()
                    extension_prompt = parts[1].strip()
                    
                    print(f"\n{Colors.NEON_PURPLE}[VIDEO EXTENSION]{Colors.RESET}")
                    print(f"  Extending: {video_file}")
                    print(f"  Prompt: {extension_prompt[:80]}...")
                    print(f"\n{Colors.DIM}This may take several minutes...{Colors.RESET}\n")
                    
                    try:
                        result = video.extend_video(video_file, extension_prompt)
                        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Video extended!")
                        print(f"  File: {result.file_path}")
                        print(f"  Duration: {result.duration_seconds:.1f}s\n")
                        logger.log_message("VIDEO", f"Extended: {result.file_path}", result.model)
                    except Exception as e:
                        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {e}\n")
                    continue
                
                if cmd == "/veomodel" or cmd.startswith("/veomodel "):
                    if not video:
                        print(f"{Colors.system_tag()} Video generation not available.")
                        continue
                    
                    if cmd.startswith("/veomodel "):
                        model_key = user_input[10:].strip().lower()
                        if model_key in VEO_MODELS:
                            video.set_model(model_key)
                            print(f"{Colors.system_tag()} Veo model: {VEO_MODELS[model_key]}")
                        else:
                            print(f"{Colors.system_tag()} Unknown model. Available: {', '.join(VEO_MODELS.keys())}")
                    else:
                        print(f"\n{Colors.GOLD}[VEO MODELS]{Colors.RESET}\n")
                        for key, model_name in VEO_MODELS.items():
                            marker = " ← ACTIVE" if key == video.model_key else ""
                            print(f"  • {key}: {model_name}{marker}")
                        print()
                    continue
                
                # ══════════════════════════════════════════════════════════
                # AGENT COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd == "/blade" or cmd.startswith("/blade "):
                    if cmd == "/blade":
                        active_agent = "blade"
                        print(f"{Colors.blade_tag()} BLADE active. Awaiting orders.")
                        continue
                    
                    query = user_input[7:].strip()
                    if not query:
                        print(f"{Colors.system_tag()} Usage: /blade <message>")
                        continue
                    
                    print(f"{Colors.blade_tag()} {thinking_message(MODELS[current_model])}")
                    response = blade.run_sync(query)
                    print(f"{Colors.blade_tag()} {response.content}\n")
                    logger.log_message("BLADE", response.content, response.model)
                    continue
                
                if cmd == "/nyx" or cmd.startswith("/nyx "):
                    if cmd == "/nyx":
                        active_agent = "nyx"
                        print(f"{Colors.nyx_tag()} NYX active. Observing.")
                        continue
                    
                    query = user_input[5:].strip()
                    if not query:
                        print(f"{Colors.system_tag()} Usage: /nyx <message>")
                        continue
                    
                    print(f"{Colors.nyx_tag()} {thinking_message(MODELS[current_model])}")
                    response = nyx.run_sync(query)
                    print(f"{Colors.nyx_tag()} {response.content}\n")
                    logger.log_message("NYX", response.content, response.model)
                    continue
                
                if cmd == "/kaedra":
                    active_agent = "kaedra"
                    print(f"{Colors.kaedra_tag()} KAEDRA active. Ready.")
                    continue
                
                if cmd.startswith("/council "):
                    query = user_input[9:].strip()
                    if not query:
                        print(f"{Colors.system_tag()} Usage: /council <task>")
                        continue
                    result = run_council(query, kaedra, blade, nyx)
                    logger.log_message("COUNCIL", result, MODELS[current_model])
                    continue
                
                # ══════════════════════════════════════════════════════════
                # ADVANCED PROMPTING COMMANDS
                # ══════════════════════════════════════════════════════════
                
                if cmd.startswith("/tot "):
                    task = user_input[5:].strip()
                    if task:
                        result = tot.execute(task, current_model)
                        logger.log_message("TOT", result, MODELS[current_model])
                    else:
                        print(f"{Colors.system_tag()} Usage: /tot <task>")
                    continue
                
                if cmd.startswith("/battle "):
                    task = user_input[8:].strip()
                    if task:
                        result = battle.execute(task, current_model)
                        logger.log_message("BATTLE", result, MODELS[current_model])
                    else:
                        print(f"{Colors.system_tag()} Usage: /battle <task>")
                    continue
                
                if cmd.startswith("/optimize "):
                    raw_prompt = user_input[10:].strip()
                    if raw_prompt:
                        result = optimizer.optimize(raw_prompt, current_model)
                        logger.log_message("OPTIMIZE", result, MODELS[current_model])
                    else:
                        print(f"{Colors.system_tag()} Usage: /optimize <prompt>")
                    continue
                
                if cmd == "/presets":
                    presets = optimizer.list_presets()
                    print(f"\n{Colors.GOLD}[AVAILABLE PRESETS]{Colors.RESET}\n")
                    for name, desc in presets.items():
                        print(f"  • {name}: {desc}")
                    print()
                    continue
                
                # ══════════════════════════════════════════════════════════
                # NATURAL COUNCIL DETECTION
                # ══════════════════════════════════════════════════════════
                
                council_triggers = [
                    "what do blade and nyx think", "ask blade and nyx",
                    "consult the team", "get the team's input",
                    "what does blade think", "what does nyx think",
                    "blade's take", "nyx's take", "bring in the team"
                ]
                
                if any(trigger in cmd for trigger in council_triggers):
                    result = run_council(user_input, kaedra, blade, nyx)
                    logger.log_message("COUNCIL", result, MODELS[current_model])
                    continue
                
                # ══════════════════════════════════════════════════════════
                # SEND TO ACTIVE AGENT
                # ══════════════════════════════════════════════════════════
                
                print(f"{Colors.kaedra_tag()} {thinking_message(MODELS[current_model])}")
                
                # ══════════════════════════════════════════════════════════
                # AUTO-EXECUTE TOOLS BEFORE LLM RESPONSE
                # ══════════════════════════════════════════════════════════
                
                tool_executed = False
                tool_result = None
                
                # BLADE tool triggers
                if active_agent == "blade":
                    blade_triggers = {
                        "sysinfo": lambda: blade.system_diagnostic(),
                        "system": lambda: blade.system_diagnostic(),
                        "status": lambda: blade.system_diagnostic(),
                        "disk": lambda: blade.get_tool_data("disk_info"),
                        "storage": lambda: blade.get_tool_data("disk_info"),
                        "processes": lambda: blade.get_tool_data("processes", limit=10),
                        "network": lambda: blade.get_tool_data("network_info"),
                    }
                    
                    for trigger, func in blade_triggers.items():
                        if trigger in cmd:
                            print(f"{Colors.blade_tag()} [AUTO-EXEC] Running {trigger}...")
                            tool_result = func()
                            tool_executed = True
                            break
                
                # NYX tool triggers
                if active_agent == "nyx":
                    nyx_triggers = {
                        "market": lambda: nyx.get_tool_data("hacker_news", limit=5),
                        "news": lambda: nyx.get_tool_data("google_news", topic="technology", num_results=5) if "google_news" in FREE_TOOLS else nyx.get_tool_data("hacker_news", limit=5),
                        "trends": lambda: nyx.get_tool_data("google_trends") if "google_trends" in FREE_TOOLS else nyx.get_tool_data("hacker_news", limit=5),
                        "crypto": lambda: nyx.get_tool_data("crypto_price", coin_id="bitcoin"),
                        "bitcoin": lambda: nyx.get_tool_data("crypto_price", coin_id="bitcoin"),
                        "price": lambda: nyx.get_tool_data("crypto_price", coin_id="bitcoin"),
                        "scan": lambda: nyx.scan_signals(),
                        "signals": lambda: nyx.scan_signals(),
                        "weather": lambda: nyx.get_tool_data("weather", location="London"),
                        "search": lambda: nyx.get_tool_data("google_search", query=user_input.replace("search", "").strip(), num_results=5) if "google_search" in FREE_TOOLS else nyx.get_tool_data("hacker_news", limit=5),
                        "youtube": lambda: nyx.get_tool_data("youtube_search", query=user_input.replace("youtube", "").strip(), max_results=5) if "youtube_search" in FREE_TOOLS else None,
                    }
                    
                    for trigger, func in nyx_triggers.items():
                        if trigger in cmd:
                            print(f"{Colors.nyx_tag()} [AUTO-EXEC] Scanning {trigger}...")
                            tool_result = func()
                            tool_executed = True
                            break
                
                # If tool executed, show results and add to context
                if tool_executed and tool_result:
                    if tool_result.get("status") == "success":
                        print(f"{Colors.NEON_GREEN}[✓]{Colors.RESET} Tool executed successfully\n")
                        
                        # Format tool result for display
                        import json
                        formatted = json.dumps(tool_result, indent=2)
                        print(f"{Colors.DIM}{formatted}{Colors.RESET}\n")
                        
                        # Add tool result to context for agent interpretation
                        tool_context = f"Tool execution result:\n{formatted}\n\nInterpret this data from your perspective."
                        user_input_with_context = f"{user_input}\n\n{tool_context}"
                    else:
                        print(f"{Colors.NEON_RED}[ERROR]{Colors.RESET} {tool_result.get('message', 'Unknown error')}\n")
                        user_input_with_context = user_input
                else:
                    user_input_with_context = user_input
                
                # Route to active agent (with tool context if available)
                # Vibe Detection (Simple)
                vibe_context = ""
                if any(w in user_input.lower() for w in ["please", "thanks", "appreciate", "love"]):
                    vibe_context = "[USER VIBE: POLITE/FRIENDLY]"
                elif any(w in user_input.lower() for w in ["urgent", "asap", "fast", "quick", "!"]):
                    vibe_context = "[USER VIBE: URGENT/DIRECT]"
                elif any(w in user_input.lower() for w in ["analy", "check", "verify", "test"]):
                    vibe_context = "[USER VIBE: ANALYTICAL]"

                final_input = user_input
                if vibe_context:
                    final_input = f"{vibe_context}\n{final_input}"
                if tool_executed:
                    final_input = f"{final_input}\n\n{tool_context}"

                if active_agent == "blade":
                    response = blade.run_sync(final_input)
                    print(f"{Colors.blade_tag()} {response.content}\n")
                elif active_agent == "nyx":
                    response = nyx.run_sync(final_input)
                    print(f"{Colors.nyx_tag()} {response.content}\n")
                else:
                    response = kaedra.run_sync(final_input)
                    print(f"{Colors.kaedra_tag()} {response.content}\n")
                
                logger.log_message(active_agent.upper(), response.content, response.model)

                # Auto-Memory: Persist turn (Brain Enhancement)
                if not user_input.startswith("/"):
                    try:
                        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        snippet_user = user_input[:500]
                        snippet_reply = response.content[:1000]
                        memory.insert(
                            content=f"User: {snippet_user}\nReply: {snippet_reply}",
                            topic=f"Turn @ {timestamp_str}",
                            tags=["auto_log", "interaction", f"agent_{active_agent}"],
                            importance="low"
                        )
                    except Exception:
                        pass # Silent fail for background memory ops
                
                # Check for execution triggers
                if "[EXEC:" in response.content:
                    try:
                        cmd_start = response.content.find("[EXEC:") + 6
                        cmd_end = response.content.find("]", cmd_start)
                        if cmd_end != -1:
                            command = response.content[cmd_start:cmd_end].strip()
                            print(f"\n{Colors.system_tag()} ⚡ Auto-executing: {command}")
                            if handle_internal_exec(command):
                                continue
                            result = subprocess.run(command, shell=True, capture_output=True, text=True)
                            if result.stdout:
                                print(f"{Colors.DIM}{result.stdout}{Colors.RESET}")
                            if result.stderr:
                                print(f"{Colors.NEON_RED}{result.stderr}{Colors.RESET}")
                    except Exception as e:
                        print(f"{Colors.system_tag()} Execution failed: {e}")
                
            except KeyboardInterrupt:
                print(f"\n{Colors.kaedra_tag()} Interrupt detected.")
                if logger.is_session_active:
                    logger.stop_session()
                break
    
    except Exception as e:
        print(f"\n{Colors.NEON_RED}[!] FATAL ERROR:{Colors.RESET} {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
