
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from kaedra.story.engine import StoryEngine
from kaedra.story.config import FLASH_MODEL, PRO_MODEL

console = Console(force_terminal=True)

async def narrate_pulse():
    console.print("[bold purple]🎬 Initializing StoryEngine for '47-Minute Pulse' Beat...[/]")
    engine = StoryEngine()
    
    # Setup Scene Context
    # We inject this as if it's the current state of the world
    initial_context = """
    [SCENE START]
    LOCATION: Mars Bio-Dome Delta (The Glass Lung).
    CHARACTERS: Sireva (Protagonist, exhausted, metabolic anomaly).
    ATMOSPHERE: Oppressive, rhythmic, bioluminescent.
    
    SITUATION:
    Sireva is lying on the grate floor of the Bio-Dome. 
    There is a "pulse" in the atmosphere—a vibration that hits every 47 minutes. 
    Her heart rate has synced to it (47 BPM). 
    This is biologically impossible. The O2 scrubbers humming in the background match the pitch.
    She feels the vibration in her teeth.
    """
    
    engine.context.add_text("user", initial_context)
    console.print(Panel(initial_context, title="Context Injection", border_style="blue"))

    # Generate the Narrative Beat
    console.print("\n[bold cyan]⚡ Generating Narrative Beat (Dual-Brain)...[/]")
    prompt = "Describe the sensation of the Pulse hitting. Sireva tries to stand but the rhythm forces her down. She realizes the scrubbers are 'singing' to her."
    
    response = await engine.generate_response(prompt)
    
    console.print("\n[bold white]📝 NARRATIVE OUTPUT:[/]")
    console.print(Panel(response, border_style="white"))
    
    # Invoke The Board for Audit
    console.print("\n[bold yellow]📡 Summoning The Board for Audit...[/]")
    await engine._fleet_review(focus="Narrative Consistency & Sensory Audit")

if __name__ == "__main__":
    try:
        asyncio.run(narrate_pulse())
    except Exception as e:
        console.print(f"[red]Execution Failed: {e}[/]")
