import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.engine import StoryEngine
from kaedra.story.config import FLASH_MODEL

async def verify_synthesis():
    print("🧪 Verifying Interactive Tool Synthesis...")
    
    # Init Engine
    engine = StoryEngine(world_config={"world_id": "test_world"})
    
    # Mock Client Response Pattern
    # This is tricky without mocking the whole GenAI client.
    # Instead, we will check the 'Configuration' state right before generation.
    
    # Spy on _run_tool_loop
    original_run_tool = engine._run_tool_loop
    
    captured_config = {}

    def mock_run_tool(model, config):
        captured_config['include_thoughts'] = config.thinking_config.include_thoughts
        captured_config['system_prompt'] = config.system_instruction
        return "Mock Synthesis: I found info on Cush. What next?"

    engine._run_tool_loop = mock_run_tool
    
    # Force 'needs_tools' decision to be True
    engine._route_request = MagicMock(return_value={
        "complexity": "medium", 
        "needs_tools": True, 
        "variant_plan": {"tiers": ["low"], "per_tier": 1}
    })

    print("▶️ Executing Turn with Tool Need...")
    # Execute
    await engine._execute_turn("Search Notion for Cush Kingdom")
    
    # Assertions
    print(f"\n🔍 Checking Config...")
    
    if captured_config.get('include_thoughts') is True:
        print("✅ Thinking Config: ENABLED")
    else:
        print("❌ Thinking Config: DISABLED")
        sys.exit(1)
        
    prompt = captured_config.get('system_prompt', "")
    if "STRICT TOOL USE POLICY" in prompt:
        print("✅ System Prompt: Policy Injected")
    else:
        print("❌ System Prompt: Policy MISSING")
        sys.exit(1)
        
    print("\n🎉 Verification Passed!")

if __name__ == "__main__":
    asyncio.run(verify_synthesis())
