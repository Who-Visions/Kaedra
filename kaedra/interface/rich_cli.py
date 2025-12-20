"""
KAEDRA v0.0.6 - Rich CLI Interface
Modern terminal UI with Rich library for streaming responses.
"""

import sys
import random
import platform
import warnings
from datetime import datetime
from typing import Optional

import vertexai
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.style import Style

# Suppress known Vertex AI deprecation warning from SDK
warnings.filterwarnings(
    "ignore",
    message="This feature is deprecated as of June 24, 2025",
    category=UserWarning,
    module=r"vertexai\..*",
)

from ..core.version import __version__, __codename__
from ..core.config import (
    MODELS, MODEL_COSTS, DEFAULT_MODEL,
    VEO_MODELS, DEFAULT_VEO_MODEL,
    LOCATION, THINKING_MESSAGES, LYRICS_DB, STARTUP_VIBES, RANDOM_FACTS
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

# Initialize Rich Console
console = Console()

# Custom styles for agents
KAEDRA_STYLE = Style(color="magenta", bold=True)
BLADE_STYLE = Style(color="red", bold=True)
NYX_STYLE = Style(color="cyan", bold=True)
SYSTEM_STYLE = Style(color="yellow", bold=True)


def print_banner():
    """Print the KAEDRA startup banner with Rich."""
    banner = """
[bold purple]╔═══════════════════════════════════════════════════════════════════════════════╗[/]
[bold purple]║[/]                                                                               [bold purple]║[/]
[bold purple]║[/]   [bold purple]██╗  ██╗[/] [bold magenta]█████╗[/] [bold magenta]███████╗[/][bold cyan]██████╗[/] [bold cyan]██████╗[/]  [bold yellow]█████╗[/]                             [bold purple]║[/]
[bold purple]║[/]   [bold purple]██║ ██╔╝[/][bold magenta]██╔══██╗[/][bold magenta]██╔════╝[/][bold cyan]██╔══██╗[/][bold cyan]██╔══██╗[/][bold yellow]██╔══██╗[/]                            [bold purple]║[/]
[bold purple]║[/]   [bold purple]█████╔╝[/] [bold magenta]███████║[/][bold magenta]█████╗[/]  [bold cyan]██║  ██║[/][bold cyan]██████╔╝[/][bold yellow]███████║[/]                            [bold purple]║[/]
[bold purple]║[/]   [bold purple]██╔═██╗[/] [bold magenta]██╔══██║[/][bold magenta]██╔══╝[/]  [bold cyan]██║  ██║[/][bold cyan]██╔══██╗[/][bold yellow]██╔══██║[/]                            [bold purple]║[/]
[bold purple]║[/]   [bold purple]██║  ██╗[/][bold magenta]██║  ██║[/][bold magenta]███████╗[/][bold cyan]██████╔╝[/][bold cyan]██║  ██║[/][bold yellow]██║  ██║[/]                            [bold purple]║[/]
[bold purple]║[/]   [bold purple]╚═╝  ╚═╝[/][bold magenta]╚═╝  ╚═╝[/][bold magenta]╚══════╝[/][bold cyan]╚═════╝[/] [bold cyan]╚═╝  ╚═╝[/][bold yellow]╚═╝  ╚═╝[/]                            [bold purple]║[/]
[bold purple]║[/]                                                                               [bold purple]║[/]
[bold purple]║[/]   [bold cyan]v{version} | {codename} | {location}[/]                                        [bold purple]║[/]
[bold purple]║[/]   [bold yellow]Who Visions LLC[/]                                                             [bold purple]║[/]
[bold purple]║[/]                                                                               [bold purple]║[/]
[bold purple]╚═══════════════════════════════════════════════════════════════════════════════╝[/]
    """.format(version=__version__, codename=__codename__, location=LOCATION)
    console.print(banner)


def print_help():
    """Print command reference using Rich table."""
    table = Table(title="KAEDRA v{} - Command Reference".format(__version__), 
                  title_style="bold yellow", box=None, show_header=True)
    table.add_column("Category", style="cyan")
    table.add_column("Command", style="green")
    table.add_column("Description", style="white")
    
    # Model switching
    table.add_row("Models", "/flash", "Gemini 2.5 Flash ⚡ (~$0.008)")
    table.add_row("", "/pro", "Gemini 2.5 Pro 🎯 (~$0.031)")
    table.add_row("", "/ultra", "Gemini 3 Pro 🔥 (~$0.038)")
    table.add_row("", "", "")
    
    # Agents
    table.add_row("Agents", "/blade [msg]", "Talk to BLADE (offensive analyst)")
    table.add_row("", "/nyx [msg]", "Talk to NYX (strategic observer)")
    table.add_row("", "/council [task]", "Multi-agent discussion")
    table.add_row("", "", "")
    
    # Memory
    table.add_row("Memory", "/remember", "Store a memory")
    table.add_row("", "/recall [query]", "Search memories (hybrid)")
    table.add_row("", "/context", "List recent memories")
    table.add_row("", "", "")
    
    # Advanced
    table.add_row("Advanced", "/tot [task]", "Tree of Thought reasoning")
    table.add_row("", "/battle [task]", "Adversarial validation")
    table.add_row("", "/optimize [p]", "Optimize a prompt")
    table.add_row("", "", "")
    
    # System
    table.add_row("System", "/status", "System health check")
    table.add_row("", "/help", "Show this reference")
    table.add_row("", "/exit", "Disconnect")
    
    console.print(table)


def agent_panel(agent: str, content: str) -> Panel:
    """Create a styled panel for agent responses."""
    if agent.lower() == "kaedra":
        return Panel(
            Markdown(content),
            title="[bold magenta]🌑 KAEDRA[/]",
            border_style="magenta",
            padding=(0, 1)
        )
    elif agent.lower() == "blade":
        return Panel(
            Markdown(content),
            title="[bold red]⚔️ BLADE[/]",
            border_style="red",
            padding=(0, 1)
        )
    elif agent.lower() == "nyx":
        return Panel(
            Markdown(content),
            title="[bold cyan]🌙 NYX[/]",
            border_style="cyan",
            padding=(0, 1)
        )
    else:
        return Panel(
            Markdown(content),
            title=f"[bold yellow]📡 {agent.upper()}[/]",
            border_style="yellow",
            padding=(0, 1)
        )


def status_table(current_model: str, active_agent: str, is_logging: bool) -> Table:
    """Create a status display table."""
    table = Table(title="System Status", box=None)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Version", f"v{__version__}")
    table.add_row("Location", LOCATION)
    table.add_row("Active Model", f"{MODELS[current_model]} ({current_model})")
    table.add_row("Active Agent", active_agent.upper())
    table.add_row("Logging", "ON ✓" if is_logging else "OFF")
    table.add_row("Semantic Search", "Enabled 🧠")
    
    return table


def memory_table(results: list) -> Table:
    """Create a table for memory search results."""
    table = Table(title=f"Memory Results ({len(results)} found)", box=None)
    table.add_column("#", style="dim")
    table.add_column("Topic", style="cyan")
    table.add_column("Content", style="white", max_width=60)
    table.add_column("Tags", style="green")
    
    for i, res in enumerate(results, 1):
        date = res.get('timestamp', '').split('T')[0]
        content = res.get('content', '')[:60] + "..."
        tags = ", ".join(res.get('tags', []))
        similarity = res.get('similarity')
        topic = res.get('topic', 'general')
        if similarity:
            topic = f"{topic} ({similarity:.2f})"
        table.add_row(str(i), topic, content, tags)
    
    return table


def startup_vibe() -> str:
    """Generate a random startup message."""
    roll = random.random()
    if roll < 0.3:
        return f"🎵 {random.choice(LYRICS_DB)} 🎵"
    elif roll < 0.5:
        return random.choice(RANDOM_FACTS)
    else:
        return random.choice(STARTUP_VIBES)


def thinking_message(model: str) -> str:
    """Generate a random thinking message."""
    if random.random() < 0.2:
        return f"🎵 {random.choice(LYRICS_DB)} 🎵"
    return random.choice(THINKING_MESSAGES).format(model=model)


def run_with_spinner(agent, query: str, agent_name: str, model: str) -> str:
    """Run agent query with a spinner animation."""
    with console.status(f"[bold cyan]{thinking_message(model)}[/]", spinner="dots"):
        response = agent.run_sync(query)
    return response


def main():
    """Main Rich CLI entry point."""
    # Force UTF-8 for Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    
    print_banner()
    
    # Initialize Vertex AI
    console.print("[dim]Connecting to {}...[/]".format(LOCATION))
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
            console.print("[green]✓[/] Video generation: READY")
        except Exception as e:
            console.print(f"[dim]Video unavailable: {e}[/]")
    
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
    active_agent = "kaedra"
    
    console.print("[green]✓[/] LINK ESTABLISHED")
    console.print(f"[green]✓[/] KAEDRA v{__version__} ONLINE")
    console.print(f"[green]✓[/] Location: {LOCATION}")
    console.print(f"[green]✓[/] Model: {MODELS[current_model]}")
    console.print("    Type [bold cyan]/help[/] for commands\n")
    
    # Startup vibe
    console.print(agent_panel("kaedra", startup_vibe()))
    
    try:
        while True:
            try:
                # Rich prompt
                user_input = console.input(
                    f"\n[bold cyan]YOU[/] [dim]|[/] [bold green]{current_model}[/] [bold cyan]>>[/] "
                ).strip()
                
                if not user_input:
                    continue
                
                # Log user input
                logger.log_message("YOU", user_input, MODELS[current_model])
                
                cmd = user_input.lower()
                
                # ═══════════════════════════════════════════════════════════
                # SYSTEM COMMANDS
                # ═══════════════════════════════════════════════════════════
                
                if cmd == "/exit":
                    if logger.is_session_active:
                        logger.stop_session()
                    console.print(agent_panel("kaedra", "Severing link. Until next time, Commander."))
                    break
                
                if cmd == "/help":
                    print_help()
                    continue
                
                # Model switching
                if cmd == "/flash":
                    current_model = "flash"
                    prompt.set_model(current_model)
                    console.print(f"[yellow]⚡ Model:[/] {MODELS[current_model]} (~${MODEL_COSTS[current_model]}/query)")
                    continue
                
                if cmd == "/pro":
                    current_model = "pro"
                    prompt.set_model(current_model)
                    console.print(f"[yellow]🎯 Model:[/] {MODELS[current_model]} (~${MODEL_COSTS[current_model]}/query)")
                    continue
                
                if cmd == "/ultra":
                    current_model = "ultra"
                    prompt.set_model(current_model)
                    console.print(f"[yellow]🔥 Model:[/] {MODELS[current_model]} (~${MODEL_COSTS[current_model]}/query)")
                    continue
                
                if cmd in ["/models", "/status"]:
                    console.print(status_table(current_model, active_agent, logger.is_session_active))
                    continue
                
                # ═══════════════════════════════════════════════════════════
                # MEMORY COMMANDS
                # ═══════════════════════════════════════════════════════════
                
                if cmd == "/remember":
                    console.print("\n[bold magenta]📝 Store Memory[/]")
                    topic = console.input("  [cyan]Topic:[/] ").strip()
                    content = console.input("  [cyan]Content:[/] ").strip()
                    tags_input = console.input("  [cyan]Tags (comma-separated):[/] ").strip()
                    
                    if topic and content:
                        tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                        mem_id = memory.insert(content, topic, tags)
                        console.print(f"  [green]✓ Stored:[/] {mem_id}")
                    else:
                        console.print("  [red]✗ Aborted:[/] Topic and Content required")
                    continue
                
                if cmd.startswith("/recall"):
                    query = cmd[7:].strip() or console.input("  [cyan]Search:[/] ").strip()
                    if query:
                        # Use hybrid search if available
                        if memory.semantic_enabled:
                            results = memory.hybrid_recall(query)
                            console.print("[dim]Using hybrid (keyword + semantic) search[/]")
                        else:
                            results = memory.recall(query)
                        console.print(memory_table(results))
                    continue
                
                if cmd == "/context":
                    recent = memory.list_recent()
                    table = Table(title="Recent Memories", box=None)
                    table.add_column("Topic", style="cyan")
                    table.add_column("Date", style="dim")
                    for res in recent:
                        date = res.get('timestamp', '').split('T')[0]
                        table.add_row(res.get('topic', 'unknown'), date)
                    console.print(table)
                    continue
                
                # ═══════════════════════════════════════════════════════════
                # AGENT COMMANDS
                # ═══════════════════════════════════════════════════════════
                
                if cmd == "/blade" or cmd.startswith("/blade "):
                    if cmd == "/blade":
                        active_agent = "blade"
                        console.print(agent_panel("blade", "BLADE active. Awaiting orders."))
                        continue
                    
                    query = user_input[7:].strip()
                    if query:
                        response = run_with_spinner(blade, query, "blade", MODELS[current_model])
                        console.print(agent_panel("blade", response.content))
                        logger.log_message("BLADE", response.content, response.model)
                    continue
                
                if cmd == "/nyx" or cmd.startswith("/nyx "):
                    if cmd == "/nyx":
                        active_agent = "nyx"
                        console.print(agent_panel("nyx", "NYX active. Observing."))
                        continue
                    
                    query = user_input[5:].strip()
                    if query:
                        response = run_with_spinner(nyx, query, "nyx", MODELS[current_model])
                        console.print(agent_panel("nyx", response.content))
                        logger.log_message("NYX", response.content, response.model)
                    continue
                
                if cmd == "/kaedra":
                    active_agent = "kaedra"
                    console.print(agent_panel("kaedra", "KAEDRA active. Ready."))
                    continue
                
                if cmd.startswith("/council "):
                    query = user_input[9:].strip()
                    if query:
                        console.print("\n[bold yellow]╔═══ COUNCIL INITIATED ═══╗[/]")
                        
                        # BLADE
                        response_b = run_with_spinner(blade, query, "blade", MODELS[current_model])
                        console.print(agent_panel("blade", response_b.content))
                        
                        # NYX
                        nyx_context = f"BLADE's Analysis: {response_b.content}"
                        response_n = run_with_spinner(nyx, query, "nyx", MODELS[current_model])
                        console.print(agent_panel("nyx", response_n.content))
                        
                        # KAEDRA synthesis
                        synthesis = f"""BLADE: {response_b.content}
NYX: {response_n.content}

Synthesize and make the final call."""
                        response_k = run_with_spinner(kaedra, query, "kaedra", MODELS[current_model])
                        console.print(agent_panel("kaedra", response_k.content))
                        
                        console.print("[bold yellow]╚═══ COUNCIL CONCLUDED ═══╝[/]\n")
                        logger.log_message("COUNCIL", response_k.content, MODELS[current_model])
                    continue
                
                # ═══════════════════════════════════════════════════════════
                # ADVANCED PROMPTING
                # ═══════════════════════════════════════════════════════════
                
                if cmd.startswith("/tot "):
                    task = user_input[5:].strip()
                    if task:
                        with console.status("[bold cyan]Running Tree of Thought analysis...[/]", spinner="dots"):
                            result = tot.execute(task, current_model)
                        console.print(Panel(Markdown(result), title="[bold yellow]🌳 Tree of Thought[/]"))
                        logger.log_message("TOT", result, MODELS[current_model])
                    continue
                
                if cmd.startswith("/battle "):
                    task = user_input[8:].strip()
                    if task:
                        with console.status("[bold cyan]Running Battle of Bots...[/]", spinner="dots"):
                            result = battle.execute(task, current_model)
                        console.print(Panel(Markdown(result), title="[bold yellow]⚔️ Battle of Bots[/]"))
                        logger.log_message("BATTLE", result, MODELS[current_model])
                    continue
                
                if cmd.startswith("/optimize "):
                    raw_prompt = user_input[10:].strip()
                    if raw_prompt:
                        with console.status("[bold cyan]Optimizing prompt...[/]", spinner="dots"):
                            result = optimizer.optimize(raw_prompt, current_model)
                        console.print(Panel(Markdown(result), title="[bold yellow]✨ Optimized Prompt[/]"))
                        logger.log_message("OPTIMIZE", result, MODELS[current_model])
                    continue
                
                # ═══════════════════════════════════════════════════════════
                # SEND TO ACTIVE AGENT
                # ═══════════════════════════════════════════════════════════
                
                # Route to active agent with spinner
                if active_agent == "blade":
                    response = run_with_spinner(blade, user_input, "blade", MODELS[current_model])
                    console.print(agent_panel("blade", response.content))
                elif active_agent == "nyx":
                    response = run_with_spinner(nyx, user_input, "nyx", MODELS[current_model])
                    console.print(agent_panel("nyx", response.content))
                else:
                    response = run_with_spinner(kaedra, user_input, "kaedra", MODELS[current_model])
                    console.print(agent_panel("kaedra", response.content))
                
                logger.log_message(active_agent.upper(), response.content, response.model)
                
                # Auto-memory (silent)
                if not user_input.startswith("/"):
                    try:
                        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        memory.insert(
                            content=f"User: {user_input[:500]}\nReply: {response.content[:1000]}",
                            topic=f"Turn @ {timestamp_str}",
                            tags=["auto_log", f"agent_{active_agent}"],
                            importance="low"
                        )
                    except Exception:
                        pass
                
            except KeyboardInterrupt:
                console.print("\n[dim]Interrupt detected.[/]")
                if logger.is_session_active:
                    logger.stop_session()
                break
                
    except Exception as e:
        console.print(f"[red]Fatal error:[/] {e}")
        if logger.is_session_active:
            logger.stop_session()


if __name__ == "__main__":
    main()
