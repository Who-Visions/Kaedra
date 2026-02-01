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

    print(f"Starting parallel generation turn 1 of {plan['variant_plan']['tiers']}...")
    start_time = time.perf_counter()
    
    # Turn 1
    engine.context.add_text("user", user_input)
    result1 = await engine.generate_canon_pack(user_input, system_prompt, plan)
    
    # Turn 2: Verify persistence
    print("\nStarting parallel generation turn 2...")
    user_input2 = "The hero explores the altar."
    engine.context.add_text("model", result1)
    engine.context.add_text("user", user_input2)
    result2 = await engine.generate_canon_pack(user_input2, system_prompt, plan)

    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"MULTI-TURN GENERATION COMPLETE in {duration:.2f}s")
    print("=" * 50)
    print(f"Result 1 (first 100 chars): {result1[:100]}...")
    print(f"Result 2 (first 100 chars): {result2[:100]}...")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_parallel_generation())
