import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from kaedra.services.lifx import LIFXService
from kaedra.story.lights import LightsController

async def reset():
    print(">> [EMERGENCY] Resetting Lights to Night Mode (Red 35%)...")
    
    # Initialize Service
    try:
        service = LIFXService(token=os.getenv("LIFX_TOKEN"))
        lights = LightsController(service)
        
        # Force Restore
        # Directly call restore logic: Red 35%
        # is_night_mode property check implies 11PM-6AM, but user requested explicit night mode now.
        # So we manually set it.
        
        # Target Living Room for safety (Eve)
        response = service.set_color(
            selector="group:Living Room",
            color="hue:0 saturation:1.0 kelvin:2500",
            brightness=0.35,
            duration=1.0
        )
        print(f"LIFX Response: {response}")
        print(">> [SUCCESS] Lights Reset.")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(reset())
