
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import request_scribe_expansion, get_entity
from rich.console import Console

console = Console()

def test_scribe_handoff():
    console.print("[bold yellow]1. Flagging 'The Shadow Blade' for Scribe...[/]")
    
    # 1. Request Expansion
    res = request_scribe_expansion(
        "The Shadow Blade", 
        "Expand the history of the blade's first wielder, the Void-Knight Malakar."
    )
    console.print(f"Result: {res}")
    
    # 2. Verify Tags
    console.print("\n[bold yellow]2. Verifying Tags...[/]")
    entity = get_entity("The Shadow Blade")
    
    if "Scribe-Queue" in entity: # Crude check, but get_entity dumps metadata text
        console.print("[green]✅ Success: 'Scribe-Queue' tag found in metadata.[/]")
    else:
        console.print("[red]❌ Failed: 'Scribe-Queue' tag NOT found.[/]")
        console.print(f"[dim]Entity Content Dump:\n{entity}[/dim]")
        
    if "SCRIBE: Expand the history" in entity:
        console.print("[green]✅ Success: Scribe marker found in body.[/]")
    else:
        console.print("[red]❌ Failed: Scribe marker missing.[/]")
        console.print(f"[dim]Entity Content Dump:\n{entity}[/dim]")

if __name__ == "__main__":
    test_scribe_handoff()
