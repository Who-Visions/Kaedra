import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from universe_text import NarrativeStructure, VeilManager
from rich.console import Console
from rich.table import Table

console = Console()

def test_audit():
    console.print("[bold cyan]Running Technical Audit Logic Test (20 Scene Run)[/]")
    
    # 1. Setup
    struct = NarrativeStructure()
    veil = VeilManager(is_active=True, hidden_truth="USER IS AN AI")
    target_len = 20
    
    table = Table(title="Narrative Timeline Simulation")
    table.add_column("Scene")
    table.add_column("Prog")
    table.add_column("Act")
    table.add_column("Directives")
    table.add_column("Veil (Metric=0.4)")
    
    # 2. Loop
    for scene in range(1, target_len + 2):
        directives = struct.tick(scene, target_length=target_len)
        
        # Test Veil Logic (simulating static metric)
        veil.revelation_metric = 0.4
        v_dir = veil.get_directive()
        
        # Highlight significant events
        dir_str = "\n".join(directives)
        style = "dim"
        if directives:
            style = "bold yellow"
            if "MIDPOINT" in dir_str:
                style = "bold red reverse"
        
        table.add_row(
            str(scene),
            f"{struct.progress:.2f}",
            str(struct.act),
            f"[{style}]{dir_str}[/]",
            v_dir[:30]+"...",
        )
        
    console.print(table)
    
    # 3. Assertions
    console.print("\n[bold]Checking Thresholds...[/]")
    
    # Reset and check specific points
    s = NarrativeStructure()
    
    # Scene 3 (15%) -> Inciting Incident
    d3 = s.tick(3, 20)
    assert any("INCITING INCIDENT" in d for d in d3), "Failed to trigger Inciting Incident at Scene 3"
    console.print("[green]✔ Scene 3 triggers Inciting Incident[/]")
    
    # Scene 10 (50%) -> Midpoint
    # Note: tick uses current vs old, so we need to step up to it
    s.tick(9, 20)
    d10 = s.tick(10, 20)
    assert any("MIDPOINT" in d for d in d10), "Failed to trigger Midpoint at Scene 10"
    console.print("[green]✔ Scene 10 triggers Midpoint Twist[/]")

if __name__ == "__main__":
    try:
        test_audit()
        print("\nALL TESTS PASSED")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except Exception as e:
        print(f"\nRUNTIME ERROR: {e}")
