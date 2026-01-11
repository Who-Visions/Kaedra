import sys
import os
from rich.console import Console

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import get_entity, get_character, create_entity
from kaedra.services.notion import NotionService

console = Console()

def verify_contract():
    console.print("[bold cyan]Verifying VeilVerse API Contract Compliance...[/]")
    notion = NotionService()

    # 1. Test Null-Safe Reading (Atlantis Prime)
    console.print("\n[bold yellow]1. Safe Read: 'Atlantis Prime'...[/]")
    try:
        # We know Atlantis Prime exists but had null category
        res = get_entity("Atlantis Prime")
        if "Status" in res or "BODY" in res or "Page" in res:
             console.print(f"[green]✅ Success: Read Atlantis Prime safely.[/]")
             console.print(f"Sample: {res[:150]}...")
        else:
             console.print(f"[red]❌ Read might have failed: {res[:100]}[/]")
    except Exception as e:
        console.print(f"[red]CRITICAL FAIL: {e}[/]")

    # 2. Test Full Schema Creation
    name = "Contract Test Unit 01"
    console.print(f"\n[bold yellow]2. Schema Write: '{name}'...[/]")
    try:
        # Should populate Status, Canon Status, and default multi-selects
        res = create_entity(name, "Character", "Compliance test unit.")
        console.print(f"Result: {res}")
        if "Created Character" in res:
             console.print("[green]✅ Write Success[/]")
    except Exception as e:
        console.print(f"[red]CRITICAL WRITE FAIL: {e}[/]")

    # 3. Readback to check defaults
    console.print(f"\n[bold yellow]3. Schema Readback: '{name}'...[/]")
    try:
        readback = get_character(name)
        if "Unknown" in readback and "Neutral" in readback: # Checks our defaults
             console.print("[green]✅ Defaults (Unknown/Neutral) verified in metadata![/]")
        else:
             console.print("[yellow]⚠️ Could not verify defaults in readback (check extraction logic).[/]")
        console.print(f"Readback Snippet: {readback[:300]}")
    except Exception as e:
        console.print(f"[red]Readback Error: {e}[/]")

if __name__ == "__main__":
    verify_contract()
