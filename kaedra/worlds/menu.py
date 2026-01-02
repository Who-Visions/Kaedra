from __future__ import annotations

from collections import defaultdict
from rich.console import Console
from rich.prompt import Prompt
from rich.tree import Tree
from rich.panel import Panel

from kaedra.worlds.store import list_worlds

console = Console()

def select_world_interactive() -> str | None:
    worlds = list_worlds()
    
    # If no worlds exist, default to creation flow (or just return special action)
    if not worlds:
        console.print("[dim]No worlds found in registry.[/]")
        
    by_universe = defaultdict(list)
    for w in worlds:
        by_universe[w.universe].append(w)

    console.clear()
    console.print(Panel("[bold cyan]KAEDRA StoryEngine[/] [dim]v7.15[/]\n[bold]World Select[/]", border_style="dim"))
    
    root = Tree("Universes")
    index_map: dict[str, str] = {}
    i = 1

    for universe in sorted(by_universe.keys()):
        u_node = root.add(f"[bold white]{universe}[/]")
        for w in by_universe[universe]:
            label = f"[yellow]{i})[/] [cyan]{w.name}[/]"
            if w.last_played:
                label += f" [dim]({w.last_played.split('T')[0]})[/]"
            u_node.add(label)
            index_map[str(i)] = w.world_id
            i += 1
    
    if not worlds:
       root.add("[dim i]Empty[/]")

    console.print(root)
    console.print("\n[bold]Actions:[/]")
    console.print("[green]N)[/] Create new world")
    console.print("[red]D)[/] Delete a world")
    console.print("[dim]Q) Quit[/]\n")

    choice = Prompt.ask(">> Select", default="N" if not worlds else "1").strip().upper()
    
    # Check numeric selection
    if choice in index_map:
        return index_map[choice]
        
    # Actions
    if choice == "N":
        return "__ACTION__:N"
    if choice == "Q":
        return None
    if choice == "D":
        # Delete flow could be here or handled by caller, for now return action
        return "__ACTION__:D"
        
    if choice.isdigit():
        # Handle case where user typed untracked number
        return None

    return "__ACTION__:N" # Default to new if unsure? Or loop? Let's return None for invalid
