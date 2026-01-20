
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Add root to path for imports
sys.path.append(os.getcwd())

load_dotenv()
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")

def search(query):
    client = Client(auth=NOTION_TOKEN)
    print(f"[-] Searching for '{query}'...")
    res = client.search(query=query).get("results", [])
    
    if not res:
        print("No results found.")
        return

    print(f"Found {len(res)} matches:")
    for p in res:
        pid = p.get("id")
        obj = p.get("object")
        title = "Untitled"
        
        # Try to find title in standard props
        props = p.get("properties", {})
        for k, v in props.items():
            if v.get("type") == "title":
                title_list = v.get("title", [])
                if title_list:
                    title = title_list[0].get("plain_text", "Untitled")
                break
                
        print(f"[{obj}] {pid} : {title}")
        url = p.get("url")
        print(f"       {url}")
        print("-" * 40)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search(sys.argv[1])
    else:
        search("Xoah")
