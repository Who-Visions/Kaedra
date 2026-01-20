import os
import toml
import requests
import json
from pathlib import Path

# Configuration
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"

def load_config():
    if not CONFIG_PATH.exists():
        print(f"❌ Config not found: {CONFIG_PATH}")
        exit(1)
    return toml.load(CONFIG_PATH)

def upgrade_schema():
    config = load_config()
    token = config["notion"]["token"]
    db_id = config["databases"]["universe_db"]

    print(f"🚀 Upgrading Schema for Database: {db_id}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # ---------------------------------------------------------
    # DEFINITIONS
    # ---------------------------------------------------------
    
    # A) Option Expansions (Multi-Select / Select / Status)
    # Note: We don't overwrite existing options, we just ensure these exist.
    # Notion merges options by name.
    
    properties = {}

    # 1. Appears In (multi_select)
    properties["Appears In"] = {
        "multi_select": {
            "options": [
                {"name": "Volume 1"}, {"name": "Volume 2"}, {"name": "Volume 3"},
                {"name": "Volume 4"}, {"name": "Volume 5"}, {"name": "Prologue Arc"},
                {"name": "Interlude Arc"}, {"name": "Canon Registry"}, {"name": "Pilot"},
                {"name": "Season 1"}, {"name": "Season 2"}, {"name": "DLC"},
                {"name": "Mainline"}, {"name": "One Shot"}
            ]
        }
    }

    # 2. Media Type (multi_select)
    properties["Media Type"] = {
        "multi_select": {
            "options": [
                {"name": "Screenplay"}, {"name": "Storyboard"}, {"name": "Animatic"},
                {"name": "Visual Bible"}, {"name": "Lore Bible"}, {"name": "Music"},
                {"name": "Podcast"}, {"name": "ARG"}, {"name": "Tabletop"},
                {"name": "VR/XR"}, {"name": "Interactive Fiction"}
            ]
        }
    }

    # 3. Universe Era (select)
    properties["Universe Era"] = {
        "select": {
            "options": [
                {"name": "Pre Collapse Era"}, {"name": "Collapse Era"},
                {"name": "Reconstruction Era"}, {"name": "Near Future Era"},
                {"name": "Far Future Era"}, {"name": "Deep Time Era"}
            ]
        }
    }

    # 4. Story Arc (select) -> New/Update? Assuming new if not exists, or update.
    properties["Story Arc"] = {
        "select": {
            "options": [
                {"name": "Inciting Incident"}, {"name": "Trials"}, {"name": "Midpoint Shift"},
                {"name": "Dark Night"}, {"name": "Finale"}, {"name": "Aftermath"},
                {"name": "Flashback"}, {"name": "Foreshadow Thread"}
            ]
        }
    }

    # 5. Canon Status (select)
    properties["Canon Status"] = {
        "select": {
            "options": [
                {"name": "Soft Canon"}, {"name": "Pending Review"},
                {"name": "Contradicted"}, {"name": "Replaced"}, {"name": "Canon Locked"}
            ]
        }
    }

    # 6. Power Level (select)
    properties["Power Level"] = {
        "select": {
            "options": [
                {"name": "Human Plus"}, {"name": "City Level"},
                {"name": "Planetary"}, {"name": "Multiversal"}
            ]
        }
    }

    # 7. Category (select)
    properties["Category"] = {
        "select": {
            "options": [
                {"name": "Organization"}, {"name": "Culture"}, {"name": "Creature"},
                {"name": "Vehicle"}, {"name": "Language"}, {"name": "Religion"},
                {"name": "Planet"}, {"name": "Dimension"}, {"name": "System"},
                {"name": "Law"}, {"name": "Scene"}, {"name": "Symbol"}
            ]
        }
    }

    # 8. Themes (multi_select)
    properties["Themes"] = {
        "multi_select": {
            "options": [
                {"name": "Control"}, {"name": "Freedom"}, {"name": "Class Divide"},
                {"name": "Surveillance"}, {"name": "Trauma"}, {"name": "Myth"},
                {"name": "Faith"}, {"name": "Corruption"}, {"name": "Loyalty"},
                {"name": "Memory"}, {"name": "Destiny"}, {"name": "Chaos"}
            ]
        }
    }

    # 9. Species/Race (multi_select)
    properties["Species/Race"] = {
        "multi_select": {
            "options": [
                {"name": "Cyborg"}, {"name": "Bio Engineered"}, {"name": "Undead"},
                {"name": "Demon"}, {"name": "Angelic"}, {"name": "Fae"},
                {"name": "Djinn"}, {"name": "Ancient Machine"},
                {"name": "Parasite Bonded"}, {"name": "Veilborn"}
            ]
        }
    }

    # 10. Tags (multi_select)
    properties["Tags"] = {
        "multi_select": {
            "options": [
                {"name": "Render Ready"}, {"name": "Needs Visual"}, {"name": "Needs Timeline"},
                {"name": "Needs Connections"}, {"name": "Needs Powers"}, {"name": "Continuity Risk"},
                {"name": "Retcon Candidate"}, {"name": "Anchor Node"}, {"name": "Scene Critical"},
                {"name": "Template Seed"}
            ]
        }
    }

    # B) New Properties to ADD

    # Core Indexing
    properties["Slug"] = {"rich_text": {}}
    properties["Display Name"] = {"rich_text": {}}
    properties["Entity Subtype"] = {
        "multi_select": {
            "options": [
                # Character
                {"name": "Protagonist"}, {"name": "Antagonist"}, {"name": "Mentor"},
                {"name": "Courier"}, {"name": "Assassin"}, {"name": "Scientist"},
                {"name": "AI"}, {"name": "Oracle"}, {"name": "Warlord"},
                # Location
                {"name": "City"}, {"name": "District"}, {"name": "Corridor"},
                {"name": "Market"}, {"name": "Shrine"}, {"name": "Vault"},
                {"name": "Museum"}, {"name": "Slum"}, {"name": "Sanctum"}, {"name": "Transit Node"},
                # Faction
                {"name": "Syndicate"}, {"name": "Resistance Cell"}, {"name": "Cult"},
                {"name": "Corporation"}, {"name": "Government"}, {"name": "Mercenary Band"},
                # Artifact
                {"name": "Weapon"}, {"name": "Veil Shard"}, {"name": "Relic"},
                {"name": "Key"}, {"name": "Suit"}, {"name": "Consumable"}, {"name": "Contract Sigil"},
                # Event
                {"name": "Heist"}, {"name": "Uprising"}, {"name": "Assassination"},
                {"name": "Collapse"}, {"name": "Discovery"}, {"name": "Trial"},
                {"name": "Betrayal"}, {"name": "War"},
                # Tech/Magic
                {"name": "Protocol"}, {"name": "Ritual"}, {"name": "Interface"},
                {"name": "Engine"}, {"name": "Binding"}, {"name": "Surveillance Stack"}
            ]
        }
    }
    properties["Canon Weight"] = {
        "select": {
            "options": [
                {"name": "Prime"}, {"name": "Core"}, {"name": "Peripheral"},
                {"name": "Experimental"}, {"name": "Alt Layer"}
            ]
        }
    }
    properties["Canon Confidence"] = {"number": {"format": "number"}}
    properties["Continuity Notes"] = {"rich_text": {}}
    properties["Continuity Flags"] = {
        "multi_select": {
            "options": [
                {"name": "Contradiction"}, {"name": "Missing Source"}, {"name": "Timeline Clash"},
                {"name": "Duplicate"}, {"name": "Needs Retcon"}, {"name": "Unclear Motive"}
            ]
        }
    }

    # Timeline
    properties["Timeline Start Year"] = {"number": {"format": "number"}}
    properties["Timeline End Year"] = {"number": {"format": "number"}}
    properties["Timeline Precision"] = {
        "select": {
            "options": [
                {"name": "Exact"}, {"name": "Estimated"},
                {"name": "Range"}, {"name": "Mythic"}, {"name": "Unknown"}
            ]
        }
    }
    properties["Era Detail"] = {
        "select": {
            "options": [] # Open ended, user can add
        }
    }
    properties["Chronology Notes"] = {"rich_text": {}}

    # Graph Power
    properties["Connection Type"] = {
        "multi_select": {
            "options": [
                {"name": "Ally"}, {"name": "Enemy"}, {"name": "Family"},
                {"name": "Mentor"}, {"name": "Rival"}, {"name": "Owner Of"},
                {"name": "Created By"}, {"name": "Located In"}, {"name": "Part Of"},
                {"name": "Leads"}, {"name": "Serves"}, {"name": "Seeks"},
                {"name": "Hunts"}, {"name": "Protects"}, {"name": "Betrayed By"},
                {"name": "Bound To"}
            ]
        }
    }
    properties["Connection Notes"] = {"rich_text": {}}
    properties["Anchor Node"] = {"checkbox": {}}
    properties["Node Tier"] = {
        "select": {
            "options": [
                {"name": "Tier 1"}, {"name": "Tier 2"},
                {"name": "Tier 3"}, {"name": "Background"}
            ]
        }
    }
    # Fix: Relation requires dual_property wrapper
    properties["Duplicate Of"] = {
        "relation": {
            "database_id": db_id, 
            "dual_property": {"synced_property_name": "Duplicates"}
        }
    }

    # Render & Asset Pipeline
    # Note: Status options cannot be set via API creation/update, valid payload is `{"status": {}}` 
    # User will need to configure the specific options in Notion UI.
    properties["Render Status"] = {"status": {}}
    
    properties["Visual Brief"] = {"rich_text": {}}
    properties["Prompt Pack"] = {"rich_text": {}}
    properties["Negative Prompt"] = {"rich_text": {}}
    properties["Model Target"] = {
        "select": {
            "options": [
                {"name": "Nano Banana Pro"}, {"name": "Gemini Image"}, {"name": "Midjourney"},
                {"name": "Firefly"}, {"name": "Stable Diffusion"}, {"name": "Practical Shoot"}
            ]
        }
    }
    properties["Aspect Ratio"] = {
        "select": {
            "options": [
                {"name": "1:1"}, {"name": "4:5"}, {"name": "16:9"},
                {"name": "9:16"}, {"name": "3:2"}, {"name": "2:3"}
            ]
        }
    }
    properties["Mood Board Links"] = {"url": {}}
    properties["Asset Folder"] = {"url": {}}
    properties["Color Palette"] = {
        "multi_select": {
            "options": [
                {"name": "Neon"}, {"name": "Ash"}, {"name": "Gold"},
                {"name": "Crimson"}, {"name": "Violet"}, {"name": "Cyan"},
                {"name": "Obsidian"}, {"name": "Bone"}, {"name": "Rust"},
                {"name": "Emerald"}
            ]
        }
    }
    properties["Cinematography Tags"] = {
        "multi_select": {
            "options": [
                {"name": "Handheld"}, {"name": "Dolly"}, {"name": "Wide"},
                {"name": "Macro"}, {"name": "Long Lens"}, {"name": "Shallow DOF"},
                {"name": "Noir Contrast"}, {"name": "Volumetric Haze"}
            ]
        }
    }

    # Veil Mechanics
    properties["Veil Presence Level"] = {"number": {"format": "number"}}
    properties["Veil Activation Trigger"] = {"rich_text": {}}
    properties["Veil Primary Tell"] = {"rich_text": {}}
    properties["Veil Secondary Tells"] = {"rich_text": {}}
    properties["Veil Cost"] = {"rich_text": {}}
    properties["Veil Failure Mode"] = {"rich_text": {}}
    properties["Veil Consequences"] = {"rich_text": {}}
    
    # Fix: Relation requires dual_property wrapper
    properties["Veil Rule Link"] = {
        "relation": {
            "database_id": db_id, 
            "dual_property": {"synced_property_name": "Linked By Law"}
        }
    }

    # Execute Update
    url = f"https://api.notion.com/v1/databases/{db_id}"
    payload = {"properties": properties}
    
    print("⏳ Sending Update Request...")
    
    try:
        resp = requests.patch(url, headers=headers, json=payload)
        
        if not resp.ok:
            print(f"❌ Update Failed: Status {resp.status_code}")
            print("Response Body:", resp.text)
            resp.raise_for_status()
            
        print("✅ Schema Upgrade Complete!")
        # print(json.dumps(resp.json(), indent=2))
        
        # ---------------------------------------------------------
        # POST-UPDATE SYNCHRONIZATION
        # ---------------------------------------------------------
        
        # 1. Save V2 Schema to Markdown
        print("   💾 Saving V2 Schema to Markdown...")
        md_lines = ["# Notion Schema V2 (Upgrade)", "## New & Updated Properties"]
        for name, details in properties.items():
            ptype = list(details.keys())[0] # e.g. "select", "multi_select"
            line = f"- **{name}** ({ptype})"
            if "options" in details[ptype]:
                opt_names = [o["name"] for o in details[ptype]["options"]]
                line += f"\n  - Options (Appended): {opt_names}"
            md_lines.append(line)
            
        md_path = ROOT / "NOTION_SCHEMA_V2.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        print(f"   ✅ Saved to {md_path}")

        # 2. Save to LoreDB (SQLite)
        try:
            import sys
            sys.path.insert(0, str(ROOT))
            from kaedra.services.loredb import LoreDB
            
            print("   💾 Saving V2 Schema to LoreDB...")
            lore = LoreDB(ROOT.parent / "lore" / "worlds" / "world_bee9d6ac") # Hardcoded for now based on context
            lore.create_block(
                type="schema_v2", 
                content=f"Notion Schema V2 Upgrade for {db_id}", 
                attrs={"schema_diff": properties, "source": "upgrade_schema_v2_script"}
            )
            print("   ✅ Saved to SQLite")
        except Exception as e:
            print(f"   ⚠️ Failed to save to LoreDB: {e}")

        # 3. Save to Memory
        try:
            from kaedra.services.memory import MemoryService
            print("   🧠 Saving to Memory...")
            mem = MemoryService()
            mem.insert(f"Notion Schema V2 Applied: {json.dumps(properties)}", role="system")
            print("   ✅ Inserted into Memory Bank")
        except Exception as e:
            print(f"   ⚠️ Failed to save to Memory: {e}")

    except Exception as e:
        print(f"❌ Update Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(e.response.text)

if __name__ == "__main__":
    upgrade_schema()
