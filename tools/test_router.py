import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.engine import StoryEngine  # Correct import
from rich.console import Console

console = Console()

def test_router_logic():
    console.print("[bold cyan]🧪 Testing Strict Intent Router...[/]")
    
    # Initialize Engine (Partial)
    engine = StoryEngine(world_config={"world_id": "test_router"})
    
    # CASE 1: Plan Intent (Vague Input)
    input_1 = "kush kingdom"
    plan_1 = engine._route_request(input_1)
    
    console.print(f"\n[yellow]Input:[/ '{input_1}'")
    console.print(f"[dim]Output:[/ {plan_1}")
    
    assert plan_1["intent"] == "plan", f"Expected intent='plan', got '{plan_1.get('intent')}'"
    assert plan_1["should_write_scene"] is False, "Expected should_write_scene=False"
    console.print("[green]✅ CASE 1 PASSED: Correctly routed to PLAN.[/]")

    # CASE 2: Scene Intent (Explicit)
    input_2 = "write scene: kush kingdom initiation"
    plan_2 = engine._route_request(input_2)
    
    console.print(f"\n[yellow]Input:[/ '{input_2}'")
    console.print(f"[dim]Output:[/ {plan_2}")
    
    assert plan_2["intent"] == "scene", f"Expected intent='scene', got '{plan_2.get('intent')}'"
    assert plan_2["should_write_scene"] is True, "Expected should_write_scene=True"
    console.print("[green]✅ CASE 2 PASSED: Correctly routed to SCENE.[/]")
    
    # CASE 3: Research Intent
    input_3 = "search notion for kush kingdom"
    plan_3 = engine._route_request(input_3)
    
    console.print(f"\n[yellow]Input:[/ '{input_3}'")
    console.print(f"[dim]Output:[/ {plan_3}")
    
    # Research might be tool use, intent=research
    # Verify needs_tools is true
    assert plan_3["needs_tools"] is True, "Expected needs_tools=True"
    console.print("[green]✅ CASE 3 PASSED: Correctly detected TOOL NEED.[/]")
    
    console.print("\n[bold green]🎉 A L L   T E S T S   P A S S E D[/]")

if __name__ == "__main__":
    try:
        test_router_logic()
    except AssertionError as e:
        console.print(f"\n[bold red]❌ TEST FAILED: {e}[/]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ ERROR: {e}[/]")
        sys.exit(1)
