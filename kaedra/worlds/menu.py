from __future__ import annotations

from collections import defaultdict
from rich.console import Console
from rich.prompt import Prompt
from rich.tree import Tree
from rich.panel import Panel

from kaedra.worlds.store import list_worlds

# Force terminal width to avoid "1 word per line" issue in constrained environments
console = Console(force_terminal=True, width=100, soft_wrap=True)

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
        
        # Special handling for Veil Verse 3-level hierarchy
        if universe == "Veil Verse":
            earth_node = u_node.add("[bold green]Earth[/]")
            mars_node = u_node.add("[bold red]Mars[/]")
            others = []
            
            earth_worlds = []
            mars_worlds = []
            
            for w in by_universe[universe]:
                if "Earth" in w.name:
                    earth_worlds.append(w)
                elif "Mars" in w.name:
                    mars_worlds.append(w)
                else:
                    others.append(w)
            
            # Helper to add worlds to nodes
            def add_to_node(node, w_list, current_idx):
                for w in w_list:
                    label = f"[yellow]{current_idx})[/] [cyan]{w.name}[/]"
                    if w.last_played:
                        label += f" [dim]({w.last_played.split('T')[0]})[/]"
                    node.add(label)
                    index_map[str(current_idx)] = w.world_id
                    current_idx += 1
                return current_idx
            
            i = add_to_node(earth_node, earth_worlds, i)
            i = add_to_node(mars_node, mars_worlds, i)
            i = add_to_node(u_node, others, i) # Add remaining directly to universe
            
        else:
            # Standard Flat List for other universes
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
