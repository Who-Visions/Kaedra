import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService

def auto_categorize():
    service = NotionService()
    print("🤖 Auto-Categorization Protocol Initiated...", flush=True)
    
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Fetched {len(pages)} entities.", flush=True)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    # Rules Engine
    rules = {
        "Artifact": ["Shard", "Glyph", "Pendant", "Blade", "Spear", "Device", "Token", "Relic", "Coin", "Key", "Mask"],
        "Lore": ["Timeline", "Cosmology", "System", "Protocol", "Theory", "History", "Myth", "Legend", "Physics", "Mechanics", "Flow", "Magic", "Veil", "Concept"],
        "Location": ["Sector", "District", "City", "Zone", "Vault", "Hub", "Lab", "Facility", "Station", "Region", "Empire", "Kingdom", "Planet", "Moon", "System", "Bar", "Club", "Tower", " Citadel"],
        "Organization": ["Syndicate", "Council", "Corp", "Faction", "Group", "Team", "Unit", "Guild", "Order", "Cult", "Society", "Company", "Department", "Agency", "Foundation", "Institute"],
        "Technology": ["Network", "Algorithm", "Code", "Program", "Software", "Hardware", "Interface", "Cyber", "Mech", "Robot", "Drone", "AI", "Platform", "Engine", "Reactor"],
        "Character": ["Sheet", "Profile", "Dossier", "Bio", "King", "Queen", "Prince", "Princess", "Agent", "Pilot", "Captain", "Doctor", "Professor", "Master", "Lord", "Lady", "God", "Goddess", "Entity", "Being", "Creature", "Person", "Human", "Cyborg", "Android"]
    }
    
    updated_count = 0
    skipped_count = 0
    manual_review = []
    
    for page in pages:
        props = page.get("properties", {})
        title = service._get_title(page)
        p_id = page["id"]
        
        # Skip if already categorized
        current_cat = service.safe_get_property(props, "Category", "select")
        if current_cat:
            skipped_count += 1
            continue
            
        if not title:
            continue
            
        # Determine Category
        assigned_cat = None
        title_lower = title.lower()
        
        for cat, keywords in rules.items():
            for kw in keywords:
                # Check for word boundary/strict containment
                # Simple containment for now
                if kw.lower() in title_lower:
                    assigned_cat = cat
                    break
            if assigned_cat:
                break
        
        # Fallback Logic
        if not assigned_cat:
            # Special logic for Xoah/Names?
            if "xoah" in title_lower or "kage" in title_lower:
                assigned_cat = "Character"
        
        if assigned_cat:
            try:
                service.client.patch(
                    f"https://api.notion.com/v1/pages/{p_id}",
                    json={"properties": {"Category": {"select": {"name": assigned_cat}}}}
                )
                print(f"   ✅ Categorized '{title}' -> {assigned_cat}", flush=True)
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Failed to update '{title}': {e}", flush=True)
        else:
            print(f"   ⚠️ Could not categorize: '{title}'", flush=True)
            manual_review.append(title)

    print(f"\n🏁 Categorization Complete.", flush=True)
    print(f"   - Updated: {updated_count}", flush=True)
    print(f"   - Skipped (Already set): {skipped_count}", flush=True)
    print(f"   - Needs Manual Review: {len(manual_review)}", flush=True)

if __name__ == "__main__":
    auto_categorize()
