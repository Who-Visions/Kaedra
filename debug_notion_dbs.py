import sys
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from kaedra.services.notion import NotionService

notion = NotionService()
if notion.client:
    print("Searching for Ingestion Queue database...")
    try:
        results = notion.client.search(
            query="Ingestion Queue",
            filter={"property": "object", "value": "database"}
        ).get("results", [])
        
        if results:
            for res in results:
                title = res.get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"[FOUND] {title} - ID: {res['id']}")
        else:
            print("No database found with that title.")
            
        print("\nAll accessible databases:")
        all_res = notion.client.search(filter={"property": "object", "value": "database"}).get("results", [])
        for res in all_res:
             title = res.get("title", [{}])[0].get("plain_text", "Untitled")
             print(f"- {title} ({res['id']})")
             
    except Exception as e:
        print(f"Error: {e}")
