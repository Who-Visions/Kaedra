import sys
import os
from rich.console import Console

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import get_entity, list_universe_pages

console = Console()

def verify_final():
    console.print("[bold cyan]Final Verification of Veil Verse Tools[/]")
    
    # 1. Test get_entity for uncategorized 'Atlantis Prime'
    console.print("\n[bold yellow]1. Testing get_entity('Atlantis Prime')...[/]")
    res = get_entity("Atlantis Prime")
    if "Status" in res and "BODY" in res:
        console.print("[green]✅ Success: Retrieved 'Atlantis Prime' (Uncategorized)[/]")
    else:
        console.print(f"[red]❌ Failed or unexpected format: {res[:100]}...[/]")
        
    # 2. Test list_universe_pages (Root Index)
    console.print("\n[bold yellow]2. Testing list_universe_pages (Root Index)...[/]")
    idx = list_universe_pages()
    if "VeilVerse Root Index" in idx:
        console.print("[green]✅ Success: Retrieved Root Index[/]")
        console.print(idx[:300] + "...")
    else:
        console.print(f"[red]❌ Failed to get Root Index: {idx[:100]}...[/]")

if __name__ == "__main__":
    verify_final()
