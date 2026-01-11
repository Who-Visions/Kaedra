import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from kaedra.services.notion import NotionService

def verify_enrichment():
    print("--- Verifying Notion Enhancements ---")
    notion = NotionService()
    
    # 1. Test Categorized Summary
    print("\n[1] Testing get_universe_summary()...")
    summary = notion.get_universe_summary()
    print(summary)
    
    # 2. Test List by Category
    print("\n[2] Testing list_entities_by_category('Character')...")
    chars = notion.list_entities_by_category("Character", limit=5)
    for c in chars:
        print(f" - {c['title']} ({c['id']})")
        
    print("\n[3] Testing list_entities_by_category('Location')...")
    locs = notion.list_entities_by_category("Location", limit=5)
    for l in locs:
        print(f" - {l['title']} ({l['id']})")

if __name__ == "__main__":
    verify_enrichment()
