
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the refactored editor
from kaedra.story.components.lore_editor import LoreEditor
from rich.console import Console

console = Console()
console.print("[bold magenta]>> Starting Smart Lore Editor Demo...[/]")
console.print("[dim]Select an entity (e.g. 'The Shadow Blade') and try the 'expand' action to see Tier selection.[/]")

editor = LoreEditor(console)
editor.run()
