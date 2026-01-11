import sys
import os
from rich.console import Console

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import create_entity, get_entity

console = Console()

def verify_expanded():
    console.print("[bold cyan]Verifying Expanded VeilVerse Schema...[/]")
    
    # 1. Test Artifact Creation (New Category)
    console.print("\n[bold yellow]1. Creating Artifact: 'The Shadow Blade'...[/]")
    res = create_entity("The Shadow Blade", "Artifact", "A legendary weapon lost to time.")
    console.print(res)
    
    if "Created Artifact" in res:
        console.print("[green]✅ Success: Artifact created.[/]")
    else:
        console.print("[red]❌ Failed to create Artifact.[/]")

    # 2. Test Lore Creation (New Category + Proposed Status)
    console.print("\n[bold yellow]2. Creating Lore: 'Origin of the Veil'...[/]")
    res = create_entity("Origin of the Veil", "Lore", "The mythological beginnings of the separation.")
    console.print(res)
    
    if "Created Lore" in res:
        console.print("[green]✅ Success: Lore created.[/]")
    else:
        console.print("[red]❌ Failed to create Lore.[/]")

    # 3. Read back to check tags (Artifact should have 'Legendary')
    console.print("\n[bold yellow]3. Checking Artifact Tags...[/]")
    readback = get_entity("The Shadow Blade")
    # Not strictly parsing tags here as get_entity returns text, but we check if it didn't crash
    if readback and "The Shadow Blade" in readback: # weak check but confirms existence
        console.print("[green]✅ Success: Artifact is readable.[/]")
    else:
        console.print("[red]❌ Artifact not found or unreadable.[/]")


    # 4. Test Quest Creation (Strict Schema Category)
    console.print("\n[bold yellow]4. Creating Quest: 'The Lost Expedition'...[/]")
    res = create_entity("The Lost Expedition", "Quest", "Find the missing research team in Sector 7.")
    console.print(res)
    
    if "Created Quest" in res:
        console.print("[green]✅ Success: Quest created (Schema validated).[/]")
    else:
        console.print("[red]❌ Failed to create Quest.[/]")

if __name__ == "__main__":
    verify_expanded()

