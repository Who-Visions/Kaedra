
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.components.lore_editor import LoreEditor
from rich.console import Console

console = Console()
console.print("[bold green]>> Starting Lore Editor Demo...[/]")

editor = LoreEditor(console)
editor.run() # Will default to asking for 'The Shadow Blade'
