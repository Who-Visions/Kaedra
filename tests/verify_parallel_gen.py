"""Verify Parallel Tier Generation in Canon Factory."""
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kaedra.story.engine import StoryEngine
from kaedra.story.config import Mode

async def test_parallel_generation():
    engine = StoryEngine()
    # Mock some world config
    engine.world_config = {"name": "Test World"}
    
    user_input = "The hero enters the forbidden temple."
    system_prompt = "You are a dungeon master."
    plan = {
        "intent": "scene",
        "should_write_scene": True,
        "needs_tools": False,
        "variant_plan": {
            "tiers": ["low", "medium", "high"], # 3 tiers in parallel
            "per_tier": 1
        }
    }

    print(f"Starting parallel generation of {plan['variant_plan']['tiers']}...")
    start_time = time.perf_counter()
    
    # Simulate turn logic: add input to context
    engine.context.add_text("user", user_input)
    
    # We call generate_canon_pack directly
    result = await engine.generate_canon_pack(user_input, system_prompt, plan)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"GENERATION COMPLETE in {duration:.2f}s")
    print("=" * 50)
    print(f"Result (first 200 chars):\n{result[:200]}...")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_parallel_generation())
