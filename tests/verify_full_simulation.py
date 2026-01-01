import asyncio
import sys
import os
import time
from rich.console import Console

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from universe_text import StoryEngine, Mode

console = Console()

STORY_INPUTS = [
    # Act 1: Equilibrium (Static)
    "Describe the room. It feels static, but something is off about the shadows.",
    "I examine the shadows closely. Do they move when I look away?",
    "Check the datapad on the desk. What does the screen say?",
    
    # Act 1 -> 2: Inciting Incident (The Glitch)
    "The air feels heavy. I sense fear.", # Trigger Fear Pulse
    "I force open the locked folder. What's inside?",
    "Wait, this code looks like... DNA? Or simulation data?",
    
    # Act 2: Veil Thinning (Hope/Rage)
    "I scream at the sky. HELLO?", # Trigger Fear/Rage
    "Hope. I feel a surge of hope that I'm not alone.", # Trigger Hope Pulse
    
    # Midpoint / Veil Unveiling
    "I punch the wall. Break the simulation!",
    "The world shatters. What do I see behind the veil?", 
]

async def run_simulation():
    console.print("[bold red]⚠️ STARTING 30-TURN FULL SIMULATION (NO MOCKS)[/]")
    console.print("[bold yellow]ℹ️ Watch your lights and terminal output.[/]")
    
    # Initialize Real Engine
    engine = StoryEngine()
    
    # Force Veil Active
    engine.veil.is_active = True
    console.print(f"Engine Mode: {engine.mode}")
    console.print(f"Veil Active: {engine.veil.is_active}")
    console.print(f"Story Structure: Act {engine.structure.act} | Progress {engine.structure.progress}")
    
    for i, user_input in enumerate(STORY_INPUTS, 1):
        console.rule(f"[bold cyan]Turn {i}/{len(STORY_INPUTS)}[/]")
        
        # Simulate User Input
        console.print(f"[bold green]USER >[/] {user_input}")
        
        # Real Generation (Streaming)
        await engine.generate_response(user_input)
        
        # Debug State
        console.print(f"[dim]State: Scene {engine.scene} | Tension {engine.tension.current:.2f} | Act {engine.structure.act}[/]")
        console.print(f"[dim]Veil Metric: {engine.veil.revelation_metric:.2f}[/]")
        
        # Pause for effect/pacings
        time.sleep(1.0)
        
    console.print("[bold green]✔ SIMULATION COMPLETE[/]")

if __name__ == "__main__":
    try:
        asyncio.run(run_simulation())
    except KeyboardInterrupt:
        console.print("[red]Sim Stopped[/]")
