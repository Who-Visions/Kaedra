
import asyncio
import os
import sys
from pathlib import Path
import traceback

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from kaedra.story.engine import StoryEngine
from rich.console import Console

console = Console(force_terminal=True)

async def validate():
    console.print("[bold cyan]🚀 Initializing StoryEngine for Council Validation...[/]")
    
    try:
        engine = StoryEngine()
        console.print("[green]✅ StoryEngine Initialized.[/]")
    except Exception as e:
        console.print(f"[red]❌ StoryEngine Init Failed: {e}[/]")
        console.print(traceback.format_exc())
        return

    # Mock some context (Dec 2025 Movie Releases)
    context = """
    [CULTURAL SCAN: DECEMBER 2025 THEATRICAL RELEASES]

    1. Avatar: Fire and Ash
       - Release: Dec 19
       - Type: Sci-Fi Spectacle/Sequel
       - Note: Major Cameron blockbuster.

    2. Anaconda
       - Release: Dec 25
       - Type: Creature-Feature Reboot
       - Note: Classic horror IP return.

    3. Five Nights at Freddy’s 2
       - Release: Dec 5
       - Type: Horror Sequel
       - Note: Viral gaming IP adaptation.

    4. The SpongeBob Movie: Search for SquarePants
       - Release: Dec 19
       - Type: Animated Family
       - Note: Legacy franchise anchor.

    5. Marty Supreme
       - Release: Dec 25
       - Type: Josh Safdie Biopic (Ping-Pong)
       - Note: A24/Indie prestige play?

    6. Song Sung Blue
       - Release: Dec 25
       - Type: Romance/Music Drama
       - Stars: Hugh Jackman, Kate Hudson
       - Note: Counter-programming to blockbusters.
    """
    
    # Push to history using the proper method
    try:
        engine.context.add_text("user", context)
        console.print("[green]✅ Context pushed to history.[/]")
    except Exception as e:
        console.print(f"[red]❌ Context Push Failed: {e}[/]")
        console.print(traceback.format_exc())
        return
    
    for i in range(1, 4):
        console.print(f"\n[bold yellow]{'='*20} PASS {i} {'='*20}[/]")
        try:
            # fleet_review takes an optional 'focus' string
            await engine._fleet_review(focus="Narratological Validation")
        except Exception as e:
            console.print(f"[red]❌ Error in Pass {i}: {e}[/]")
            console.print(traceback.format_exc())

    console.print(f"\n[bold cyan]{'='*20} VALIDATION SUMMARY {'='*20}[/]")
    console.print(f"Total Council Sessions: {engine.council_sessions}")
    console.print(f"Final Scoreboard: {engine.fleet_scores}")
    
    # Check if scores were recorded
    if engine.fleet_scores:
        console.print("[bold green]✅ CONSISTENCY CHECK: Scores recorded successfully.[/]")
    else:
        console.print("[bold red]⚠️ WARNING: No scores recorded. Check democratic voting parsing.[/]")

if __name__ == "__main__":
    try:
        asyncio.run(validate())
    except Exception as e:
        print(f"CRITICAL MAIN ERROR: {e}")
        traceback.print_exc()
