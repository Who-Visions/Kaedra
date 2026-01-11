import sys
import os
from pathlib import Path

# Ensure kaedra is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.services.notion import NotionService
from rich.console import Console

console = Console()

def verify():
    console.print("[bold cyan]Testing Notion Integration...[/]")
    
    # 1. Initialize
    try:
        notion = NotionService()
        if not notion.client:
            console.print("[red]❌ Failed to init Notion client (check .env)[/]")
            return
            
        users = notion.get_users()
        console.print(f"[green]✅ Auth Successful! Found {len(users)} users.[/]")
        
    except Exception as e:
        console.print(f"[red]❌ Init Exception: {e}[/]")
        return

    # 2. Search for Veil Verse
    console.print("\n[bold cyan]Searching for 'Veil Verse'...[/]")
    page_id = notion.search_page("Veil Verse")
    
    if page_id:
        console.print(f"[green]✅ Found 'Veil Verse' (ID: {page_id})[/]")
        
        # 3. List Subpages
        console.print("\n[bold cyan]Scanning Children...[/]")
        children = notion.list_subpages("Veil Verse")
        if children:
            for c in children[:5]:
                console.print(f"  - {c}")
            if len(children) > 5:
                console.print(f"  ... and {len(children)-5} more.")
            console.print(f"[green]✅ Found {len(children)} sub-items.[/]")
        else:
            console.print("[yellow]⚠️ 'Veil Verse' found but returned no children (or Permissions issue).[/]")
    else:
        console.print("[red]❌ Could not find 'Veil Verse' page.[/]")
        
    # 4. Check specific canon page
    target = "ATLANTIS PRIME"
    console.print(f"\n[bold cyan]Reading Canon Page: '{target}'...[/]")
    content = notion.read_page_content(target)
    
    if "not found" not in content and "Error" not in content:
        console.print(f"[green]✅ Read '{target}' successfully ({len(content)} chars).[/]")
        console.print(f"[dim]{content[:200]}...[/]")
    else:
        console.print(f"[red]❌ Failed to read '{target}': {content}[/]")

if __name__ == "__main__":
    verify()
