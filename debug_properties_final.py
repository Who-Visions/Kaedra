import json
import sys
from notion_client import Client

TOKEN = "ntn_u30316993017RaOd8iWGISlHViGvluX3BtJiGWqgoCQ0JY"
DB_ID = "2d90b4b4-0f65-8001-98fe-cbf8a4a2146a"

client = Client(auth=TOKEN)

try:
    print(f"Attempting client.databases.query on {DB_ID}...")
    # Try standard method
    results = client.databases.query(database_id=DB_ID, page_size=1).get("results", [])
    
    if results:
        print("✅ Success via .query()")
        print(json.dumps(results[0].get("properties", {}), indent=2))
    else:
        print("⚠️ No results found in database.")

except AttributeError:
    print("⚠️ client.databases.query not found. Attempting raw request...")
    try:
        # Fallback to raw request
        response = client.request(
            path=f"databases/{DB_ID}/query",
            method="POST",
            body={"page_size": 1}
        )
        results = response.get("results", [])
        if results:
            print("✅ Success via .request()")
            print(json.dumps(results[0].get("properties", {}), indent=2))
        else:
            print("⚠️ No results found via raw request.")
    except Exception as e:
        print(f"❌ Raw request failed: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
