"""Test StoryChainer logic."""
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kaedra.story.chain import StoryChainer
from rich.console import Console

async def test_chaining():
    console = Console()
    chainer = StoryChainer(console=console)
    
    user_input = "Write a story about a sentient Martian dust storm that falls in love with a Mars rover."
    system_prompt = "You are an award-winning science fiction author."
    
    print("Testing Story Chaining pipeline (this may take a minute)...")
    story = await chainer.chain_generation(user_input, system_prompt)
    
    print("\n" + "=" * 50)
    print("FINAL STORY PREVIEW")
    print("=" * 50)
    print(story[:500] + "...")
    print("=" * 50)
    print(f"Total length: {len(story)} chars")

if __name__ == "__main__":
    asyncio.run(test_chaining())
