from notion_client import Client
import os

token = "ntn_u30316993017RaOd8iWGISlHViGvluX3BtJiGWqgoCQ0JY"
client = Client(auth=token)

print("Client:", client)
print("Databases endpoint:", client.databases)
print("Dir of databases:", dir(client.databases))

try:
    print("Trying query...")
    # Just list databases to see if it works without filter first
    # querying a database requires an ID.
    ingest_id = "44fb8dcf5fc64ea1b6187488a3007a58"
    resp = client.databases.query(database_id=ingest_id)
    print("Success, results:", len(resp['results']))
except Exception as e:
    print("Error:", e)
