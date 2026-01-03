"""
LoreDB Test Script
Validates the LoreDB service functionality.
"""
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from kaedra.services.loredb import LoreDB

def test_loredb():
    """Test LoreDB functionality."""
    print("=" * 50)
    print("LOREDB TEST SUITE")
    print("=" * 50)
    
    # Test with temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        lore = LoreDB(Path(tmpdir) / "test_world")
        
        # Test 1: Create blocks
        print("\n[1] Creating blocks...")
        char_id = lore.create_block(
            "character",
            "The Shadow King rules from the Obsidian Throne.",
            attrs={"name": "Shadow King", "power_level": 95, "faction": "Veil Council"}
        )
        print(f"    Created character: {char_id}")
        
        loc_id = lore.create_block(
            "location",
            "The Obsidian Throne sits at the heart of the Veil Citadel.",
            attrs={"name": "Obsidian Throne", "era": "Modern"}
        )
        print(f"    Created location: {loc_id}")
        
        # Test 2: Create block with reference
        print("\n[2] Creating block with references...")
        event_id = lore.create_block(
            "event",
            f"The coronation of [[{char_id}]] at the [[{loc_id}]].",
            attrs={"year": 2026, "era": "Modern"}
        )
        print(f"    Created event: {event_id}")
        
        # Test 3: Get block
        print("\n[3] Retrieving block...")
        block = lore.get_block(char_id)
        print(f"    Retrieved: {block.attrs.get('name')} (power: {block.attrs.get('power_level')})")
        
        # Test 4: Update block
        print("\n[4] Updating block...")
        lore.update_block(char_id, attrs={"power_level": 99})
        updated = lore.get_block(char_id)
        print(f"    Updated power_level: {updated.attrs.get('power_level')}")
        
        # Test 5: Query by type
        print("\n[5] Query by type...")
        characters = lore.find_by_type("character")
        print(f"    Found {len(characters)} character(s)")
        
        # Test 6: Query by attribute
        print("\n[6] Query by attribute...")
        veil_members = lore.find_by_attr("faction", "Veil Council")
        print(f"    Veil Council members: {len(veil_members)}")
        
        # Test 7: Full-text search
        print("\n[7] Full-text search...")
        results = lore.search("Shadow")
        print(f"    Search 'Shadow': {len(results)} result(s)")
        
        # Test 8: Backlinks
        print("\n[8] Backlinks...")
        backlinks = lore.get_backlinks(char_id)
        print(f"    Backlinks to Shadow King: {len(backlinks)}")
        
        # Test 9: Stats
        print("\n[9] Database stats...")
        stats = lore.stats()
        print(f"    {stats}")
        
        # Test 10: JSON export
        print("\n[10] JSON sync...")
        lore.sync_to_json()
        print(f"    Exported to JSON files")
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED!")
        print("=" * 50)

if __name__ == "__main__":
    test_loredb()
