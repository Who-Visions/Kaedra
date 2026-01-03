import sys
import traceback
import asyncio
from pathlib import Path

# Add project root
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from kaedra.story.engine import StoryEngine
from kaedra.worlds.store import load_world

async def test_init():
    try:
        world_id = "world_bee9d6ac"
        print(f"[*] Attempting to boot engine with world: {world_id}")
        world_data = load_world(world_id)
        
        engine = StoryEngine(world_config=world_data)
        print("[✅] Engine initialized successfully.")
        
        # We won't run the full loop, just a quick check
        print("[*] Transitioning to run loop...")
        # engine.run() is async, we can just check if it survives start of run
        
    except Exception:
        print("\n" + "="*60)
        print("CRASH DETECTED DURING INITIALIZATION:")
        traceback.print_exc()
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test_init())
