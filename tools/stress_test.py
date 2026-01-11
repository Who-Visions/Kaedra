import asyncio
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.engine import StoryEngine  # Correct import
from kaedra.story.context import ContextManager

# Mock Input Generator
MOCK_INPUTS = [
    "Look around the area.",
    "Check my inventory.",
    "What do I see in the distance?",
    "Move towards the light.",
    "Analyze the structural integrity.",
    "Recall relevant history.",
    "Scan for energy signatures.",
    "Attempt to communicate.",
    "Wait and observe.",
    "Debug system status."
]

async def stress_test(turns=100):
    from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn, TaskProgressColumn
    from rich.console import Console
    
    console = Console()
    console.print(f"\n[STRESS TEST] Initializing Engine for {turns} turns...")
    
    # Initialize Engine
    engine = StoryEngine(world_config={"world_id": "stress_test_world"})
    
    start_time = time.time()
    errors = 0
    cache_hits = 0
    
    console.print("[STRESS TEST] Starting Loop...")

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running Stress Test...", total=turns)
        
        for i in range(turns):
            turn_id = i + 1
            user_input = MOCK_INPUTS[i % len(MOCK_INPUTS)]
            
            try:
                # Execute Turn
                response = await engine._execute_turn(user_input, tick_physics=True)
                
                # Check Metrics
                budget = engine.context.get_budget_status(prune=False)
                cache_name = engine.context.cached_content_name
                
                usage_str = f"{budget['usage_percent']:.1f}%"
                cache_str = "HIT" if cache_name else "MISS"
                if cache_name: cache_hits += 1
                
                progress.update(task, advance=1, description=f"[cyan]Stress Test[/] | Turn {turn_id} | Tokens: {usage_str} | Cache: {cache_str}")
                
            except Exception as e:
                console.print(f"[red]Failed Turn {turn_id}: {e}[/]")
                errors += 1
            
            await asyncio.sleep(0.1)

    duration = time.time() - start_time
    console.print(f"\n[STRESS TEST] COMPLETE in {duration:.2f}s")
    console.print(f"TOTAL TURNS: {turns}")
    console.print(f"ERRORS: {errors}")
    console.print(f"CACHE HITS: {cache_hits}")
if __name__ == "__main__":
    try:
        asyncio.run(stress_test(100))
    except (KeyboardInterrupt, SystemExit):
        print("\n[STRESS TEST] Aborted.")
