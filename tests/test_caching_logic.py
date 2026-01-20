"""Test LoreCacheManager logic."""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kaedra.services.cache_manager import get_cache_manager

def test_caching():
    cm = get_cache_manager()
    content = "This is a large world bible content that we want to cache. " * 100
    system_instruction = "You are a helpful lore assistant."
    
    print("Testing get_or_create_cache...")
    cache_name = cm.get_or_create_cache(content, system_instruction, ttl_seconds=600)
    
    if cache_name:
        print(f"✅ Cache created/retrieved: {cache_name}")
        
        print("Testing retrieval of existing cache...")
        cache_name_2 = cm.get_or_create_cache(content, system_instruction)
        if cache_name == cache_name_2:
            print("✅ Deduplication works!")
        else:
            print(f"❌ Deduplication failed: {cache_name} != {cache_name_2}")
            
        print("Cleaning up (Optional, but let's test delete)...")
        # cm.delete_cache(cache_name)
    else:
        print("❌ Cache creation failed (Check if content is > 32k tokens if required by API)")

if __name__ == "__main__":
    test_caching()
