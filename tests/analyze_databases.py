import sys
import os
import json
from rich.console import Console

# Ensure kaedra is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.services.notion import NotionService

console = Console()

def analyze_dbs():
    console.print("[bold cyan]Analyzing Notion Databases...[/]")
    notion = NotionService()

    try:
        # Strategy B: Backtrace from known page
        page_id = notion.search_page("ATLANTIS PRIME")
        dbs = []
        if page_id:
            page = notion.client.pages.retrieve(page_id)
            parent = page.get("parent", {})
            # Found it via backtrace log: 2d90b4b4-0f65-8001-98fe-cbf8a4a2146a
            db_id = parent.get("database_id")
            if not db_id and parent.get("type") == "database_id":
                 db_id = parent.get("database_id")
            
            if db_id:
                console.print(f"[green]Found Parent Database ID: {db_id}[/]")
                try:
                    db = notion.client.databases.retrieve(db_id)
                    dbs.append(db)
                except Exception as e:
                    console.print(f"[red]Failed to retrieve DB: {e}[/]")
            else:
                console.print(f"[yellow]Page parent has no database_id: {parent}[/]")
        else:
             console.print("[red]Could not find anchor page 'ATLANTIS PRIME'[/]")
             
        # Search ALL objects (no filter) then filter client-side
        
        console.print(f"Found {len(dbs)} reachable databases.\n")
        
        for db in dbs:
            db_id = db["id"]
            title_list = db.get("title", [])
            title = "".join([t["plain_text"] for t in title_list]) if title_list else "Untitled"
            
            console.print(f"[bold yellow]{title}[/] (ID: {db_id})")
            
            # Print Properties Schema
            props = db.get("properties", {})
            console.print(f"  Schema ({len(props)} fields):")
            
            # Sort for readability
            for key, val in sorted(props.items()):
                dtype = val.get("type", "unknown")
                extra = ""
                if dtype == "select":
                    opts = [o["name"] for o in val.get("select", {}).get("options", [])]
                    extra = f" Options: {opts[:5]}..." if len(opts) > 5 else f" Options: {opts}"
                elif dtype == "multi_select":
                    opts = [o["name"] for o in val.get("multi_select", {}).get("options", [])]
                    extra = f" Options: {opts[:5]}..." if len(opts) > 5 else f" Options: {opts}"
                elif dtype == "relation":
                    extra = f" (Linked)"
                    
                console.print(f"   - [cyan]{key}[/] ({dtype}){extra}")
            console.print("")

    except Exception as e:
        console.print(f"[red]Error analyzing databases: {e}[/]")

if __name__ == "__main__":
    analyze_dbs()
