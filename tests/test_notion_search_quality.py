import os
import sys
from kaedra.services.notion import NotionService

def test_search():
    notion = NotionService()
    
    test_queries = [
        ("Xoah lin oda", "Xoah-Lin Oda"),
        ("Shadow king", "The Shadow King (Oda Nobunaga)"),
        ("shadow courier", "Xoah-Lin Oda"), # Alias test
    ]
    
    print("\n--- Notion Search Quality Test ---")
    for query, expected in test_queries:
        print(f"\nSearching for: '{query}'")
        page_id = notion.search_page(query)
        if page_id:
            # We need to get the title to verify
            page = notion.client.pages.retrieve(page_id=page_id)
            title = notion._get_title(page)
            print(f"Result: '{title}' (ID: {page_id})")
            if expected.lower() in title.lower():
                print("✅ Match!")
            else:
                print(f"❌ Mismatch. Expected containing '{expected}'")
        else:
            print("❌ No results found.")

if __name__ == "__main__":
    test_search()
