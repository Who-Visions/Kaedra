import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.services.prompt import PromptService
from kaedra.core.config import PROJECT_ID, LOCATION

async def test_smart_routing():
    print("🚀 Testing Gemini Smart Router...")
    
    prompt_service = PromptService()
    print(f"DEBUG: PromptService using Project={prompt_service.project}, Location={prompt_service.location}")
    
    # 1. Test Simple Query (Should stay on Flash)
    print("\n[Test 1] Simple Query...")
    simple_query = "What time is it in Miami?"
    result1 = await prompt_service.generate_async(simple_query)
    print(f"Query: {simple_query}")
    print(f"Model Used: {result1.model}")
    if result1.thoughts:
        print(f"Thoughts: {result1.thoughts[:100]}...")
    
    # 2. Test Complex Query (Should escalate to Pro)
    print("\n[Test 2] Complex Query (Research/Analyze)...")
    complex_query = "Research the latest trends in agentic AI and analyze their impact on software development."
    result2 = await prompt_service.generate_async(complex_query)
    print(f"Query: {complex_query}")
    print(f"Model Used: {result2.model}")
    if result2.thoughts:
        print(f"Thoughts: {result2.thoughts[:200]}...")
    
    # 3. Test Debug Query
    print("\n[Test 3] Debug Query...")
    debug_query = "Debug this python error: 'NameError: name 'genai' is not defined'"
    result3 = await prompt_service.generate_async(debug_query)
    print(f"Query: {debug_query}")
    print(f"Model Used: {result3.model}")
    if result3.thoughts:
        print(f"Thoughts: {result3.thoughts[:200]}...")

    print("\n✅ Smart Routing Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_smart_routing())
