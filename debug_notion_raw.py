import requests
import uuid

token = "ntn_u30316993017RaOd8iWGISlHViGvluX3BtJiGWqgoCQ0JY"

# The DATA SOURCE ID from the URL (ds/44fb... part)
ds_id = "44fb8dcf5fc64ea1b6187488a3007a58"

def format_uuid(id_str):
    if len(id_str) == 32:
        return str(uuid.UUID(id_str))
    return id_str

formatted_id = format_uuid(ds_id)

headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2025-09-03",  # Updated version!
    "Content-Type": "application/json"
}

# Query DATA SOURCE endpoint (not databases)
url = f"https://api.notion.com/v1/data_sources/{formatted_id}/query"
print(f"Querying: {url}")

resp = requests.post(url, headers=headers, json={})
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"Results count: {len(data.get('results', []))}")
    if data.get('results'):
        page = data['results'][0]
        print("First page properties:")
        for prop_name, prop_val in page.get('properties', {}).items():
            print(f"  - {prop_name}: {prop_val.get('type')}")
else:
    print(f"Error: {resp.text}")
