
import os
import sys
from notion_client import Client, APIResponseError

# Add project root to path
sys.path.append(os.getcwd())

from kaedra.core.config import NOTION_TOKEN

def diagnose_notion():
    print("[-] diagnosising Notion Connectivity...")
    
    if not NOTION_TOKEN:
        print("[!] FATAL: NOTION_TOKEN not found in environment.")
        return

    client = Client(auth=NOTION_TOKEN)

    # 1. READ CHECK (Get Users)
    print("[-] Step 1: Read Check (List Users)...")
    try:
        users = client.users.list().get("results", [])
        print(f"[+] Read Success. Found {len(users)} users.")
    except APIResponseError as e:
        print(f"[!] READ FAILED: {e.code} - {e.message}")
        return
    except Exception as e:
        print(f"[!] READ FAILED (Unknown): {e}")
        return

    # 2. WRITE CHECK (Append to a dedicated test page or just check limits)
    # We won't spam. We'll try to search for the "System Logs" page or similar
    # and append one tiny block, OR just stop here if user is worried about blocks.
    
    # Actually, let's just create a temporary top-level page? No, that might spam.
    # Let's search for "Kaedra Diagnostics"
    print("[-] Step 2: Write Target Search...")
    try:
        search_res = client.search(query="Kaedra Diagnostics").get("results", [])
        page_id = None
        if search_res:
            page_id = search_res[0]["id"]
            print(f"[+] Found Diagnostic Page: {page_id}")
            
            # ATTEMPT WRITE
            print("[-] Step 3: Attempting Write (Append Block)...")
            try:
                client.blocks.children.append(
                    block_id=page_id,
                    children=[
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": "Diagnostics Write Test: SUCCESS"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                )
                print("[+] WRITE SUCCESS: Block appended.")
            except APIResponseError as e:
                print(f"[!] WRITE FAILED: {e.code} - {e.message}")
        else:
            print("[-] Diagnostic Page not found. Skipping write safely.")

    except APIResponseError as e:
        print(f"[!] SEARCH/WRITE FAILED: {e.code} - {e.message}")

if __name__ == "__main__":
    diagnose_notion()
