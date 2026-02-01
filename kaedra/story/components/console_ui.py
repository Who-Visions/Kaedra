import asyncio
import sys
import time
# import msvcrt removed (Windows-only), handled dynamically in smart_input
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from datetime import datetime

class EngineUI:
    """Handles console interactions, input loops, and rich output."""

    def __init__(self, console: Console):
        self.console = console
        self._session_file = None

    def init_log(self, session_dir: Path):
        """Initialize session logging."""
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            self._session_file = session_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
            if not self._session_file.exists():
                self._session_file.write_text("", encoding="utf-8")
        except Exception as e:
            self.console.print(f"[red]❌ Session directory failure ({session_dir}): {e}[/]")
            self._session_file = Path(f"session_fallback_{int(time.time())}.jsonl")

    def show_help(self):
        """Display command help."""
        table = Table(title="StoryEngine Commands", box=None)
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        cmds = [
            (":plan [prompt]", "Force PLANNER mode (Build steps)"),
            (":scene [prompt]", "Force SCENE mode (Write narrative)"),
            (":research [topic]", "Force RESEARCH mode (Trigger tools)"),
            (":go [prompt]", "Alias for :scene"),
            ("freeze", "Bullet-time mode"),
            ("zoom", "Micro-detail focus"),
            ("escalate", "Spike tension"),
            ("god", "Worldbuilding/Lore"),
            ("director", "Meta-narration"),
            ("normal", "Reset to default"),
            ("pov [name]", "Change perspective"),
            ("next", "Advance scene"),
            ("rewind [n]", "Rewind n snapshots"),
            ("emotion [emo] [delta]", "Pulse emotion"),
            ("queue [pri] [msg]", "Queue message"),
            ("coherence", "Analyze lore consistency"),
            ("bridge", "Generate narrative bridge"),
            ("debug", "Show state"),
            ("email", "Show recent emails"),
            ("calendar", "Show today's events"),
            ("tasks", "Show pending tasks"),
            ("review / board", "Trigger Fleet Review Board"),
            ("automate", "Run Agent-Layer Automations"),
            ("sync", "Sync World to Notion"),
            ("lights [restore|fire]", "Manual Atmosphere Control"),
        ]
        for c, d in cmds:
            table.add_row(c, d)
        self.console.print(table)

    def show_debug(self, engine_state: dict, context_budget: dict):
        """Display internal state."""
        self.console.print(Panel(
            Pretty(engine_state),
            title="[bold yellow]Debug: Current State[/]",
            border_style="yellow"
        ))

        self.console.print(
            f"\n[cyan]Context Budget:[/] {context_budget['current']:,} / {context_budget['capacity']:,} tokens ({context_budget['usage_percent']:.1f}%)"
        )

    def smart_input(self, prompt_markup: str = ">> ") -> str:
        """
        Smart Input with Heuristic Paste Detection.
        If newline is followed immediately (<50ms) by more input, it's a paste.
        """
        # Platform-specific interactive input (Windows only)
        if sys.platform != "win32":
            self.console.print(prompt_markup, end="")
            return input()

        try:
            import msvcrt
        except ImportError:
            self.console.print(prompt_markup, end="")
            return input()

        if ">>" in prompt_markup:
            sys.stdout.write("\n>> ")
        else:
            sys.stdout.write("\n> ")
        sys.stdout.flush()

        buffer = []
        while True:
            # Batch read loop
            batch = []
            while msvcrt.kbhit():
                char = msvcrt.getwch()
                batch.append(char)
                if len(batch) > 5000:
                    break

            if not batch:
                time.sleep(0.001)
                continue

            echo_chunk = []

            for i, char in enumerate(batch):
                if char == '\x03': # Ctrl+C
                    raise KeyboardInterrupt

                if char == '\x08': # Backspace
                    if buffer:
                        buffer.pop()
                        if echo_chunk:
                            sys.stdout.write("".join(echo_chunk))
                            echo_chunk = []
                        sys.stdout.flush()

                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                    continue

                if char == '\r': # Enter
                    remaining_in_batch = (i < len(batch) - 1)
                    is_paste = remaining_in_batch

                    if not is_paste:
                        start = time.perf_counter()
                        while (time.perf_counter() - start) < 0.15:
                            if msvcrt.kbhit():
                                is_paste = True
                                break

                    if is_paste:
                        buffer.append('\n')
                        echo_chunk.append('\n')
                        continue
                    else:
                        if echo_chunk:
                            sys.stdout.write("".join(echo_chunk))
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        return "".join(buffer)

                buffer.append(char)
                echo_chunk.append(char)

            if echo_chunk:
                sys.stdout.write("".join(echo_chunk))
                sys.stdout.flush()
