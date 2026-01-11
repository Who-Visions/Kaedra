import sys
import os
from rich.console import Console

# Ensure kaedra is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.tools.notion import get_character, get_location, get_event, create_entity
from kaedra.services.notion import NotionService

console = Console()

def verify_entities():
    notion = NotionService()
    console.print("[bold cyan]Testing Entity Tools...[/]")

    # 1. Test existing character (Ruvo)
    # Note: We need to know Ruvo's category. Assuming 'Character' based on name.
    console.print("\n[bold yellow]1. Testing get_character('Ruvo')...[/]")
    char_profile = get_character("Ruvo")
    console.print(f"Result (First 200 chars): {char_profile[:200]}...")

    # 2. Test existing location (Atlantis Prime)
    # Note: Atlantis Prime might be distinct or a character?
    console.print("\n[bold yellow]2. Testing get_location('Atlantis Prime')...[/]")
    # We suspect it might be Any category, but let's try location tool
    loc_profile = get_location("Atlantis Prime")
    console.print(f"Result (First 200 chars): {loc_profile[:200]}...")

    # 3. Test Creation (Draft)
    console.print("\n[bold yellow]3. Testing create_entity('Test Drone X', 'Character')...[/]")
    # This creates real data, so we mark it DRAFT in code
    create_res = create_entity(
        name="Test Drone X", 
        category="Character", 
        content="Experimental drone unit for verifying StoryEngine writes."
    )
    console.print(f"Creation Result: {create_res}")

    # 4. Verify Readback
    if "Created" in create_res:
         console.print("\n[bold yellow]4. Verifying Readback of Test Drone X...[/]")
         # Wait a moment for consistency?
         readback = get_character("Test Drone X")
         if "Experimental drone" in readback:
             console.print("[green]✅ Readback confirmed![/]")
         else:
             console.print(f"[red]❌ Readback failed or delayed: {readback}[/]")

if __name__ == "__main__":
    verify_entities()
