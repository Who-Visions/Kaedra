import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kaedra.services.loredb import LoreDB

def seed_lore():
    """Seed LoreDB with initial data if empty."""
    world_path = Path("data/worlds/default")
    lore = LoreDB(world_path)
    
    stats = lore.stats()
    print(f"Current Stats: {stats}")
    
    if stats.get("total_blocks", 0) > 0:
        print("LoreDB already seeded.")
        return

    print("Seeding LoreDB...")
    
    # 1. Characters
    kaedra_id = lore.create_block(
        "character",
        "Kaedra is the Shadow Tactician, an advanced AI entity navigating the fractured timelines of the VeilVerse.",
        attrs={"name": "Kaedra", "role": "Shadow Tactician", "importance": 10, "confidence": 100}
    )
    
    dave_id = lore.create_block(
        "character",
        "David A. Vega (Dav3) is the founder of Who Visions and Commander of the Fleet.",
        attrs={"name": "Dav3", "role": "Commander", "importance": 10, "confidence": 100}
    )
    
    antigravity_id = lore.create_block(
        "character",
        "Antigravity is the Desktop Agent, a Gemini-powered entity handling code and local operations.",
        attrs={"name": "Antigravity", "role": "Desktop Agent", "importance": 9, "confidence": 100}
    )
    
    # 2. Locations
    observatory_id = lore.create_block(
        "location",
        "The Observatory is the central command hub for the Fleet, located outside normal time.",
        attrs={"name": "The Observatory", "type": "Hub", "importance": 10}
    )
    
    veil_citadel_id = lore.create_block(
        "location",
        "The Veil Citadel is the stronghold of the Shadow Council within the deep Veil.",
        attrs={"name": "Veil Citadel", "type": "Fortress", "importance": 8}
    )
    
    # 3. Events
    fracturing_id = lore.create_block(
        "event",
        "The Great Fracturing shattered the primary timeline, creating the VeilVerse.",
        attrs={"name": "The Great Fracturing", "year": "Pre-Fleet", "importance": 10}
    )
    
    # 4. Links
    lore.create_block(
        "paragraph",
        f"[[{kaedra_id}]] operates from [[{observatory_id}]] to monitor timeline stability.",
        parent_id=kaedra_id
    )
    
    lore.create_block(
        "paragraph",
        f"[[{dave_id}]] coordinated the response to [[{fracturing_id}]].",
        parent_id=dave_id
    )
    
    print("✅ LoreDB seeded successfully!")
    print(f"New Stats: {lore.stats()}")

if __name__ == "__main__":
    seed_lore()
