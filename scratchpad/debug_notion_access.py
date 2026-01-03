from kaedra.services.notion import NotionService
import sys

def main():
    print("[*] Debugging Notion Access...")
    service = NotionService()
    
    if not service.client:
        print("[!] Service failed to initialize.")
        return

    print("[*] Searching for ANY accessible pages...")
    try:
        # Search with no query to list generic recently used or relevant pages
        results = service.client.search(filter={"property": "object", "value": "page"}).get("results")
        
        if not results:
            print("[!] No pages found. The integration has NO ACCESS to any pages in the workspace.")
            print("    Please go to a page -> ... -> Connections -> Add 'Kaedra-notes'")
        else:
            print(f"[✅] Found {len(results)} accessible pages:")
            for page in results:
                title = "Untitled"
                # Extract title safely
                props = page.get("properties", {})
                # Titling varies by database vs page, but usually 'title' property exists
                # For direct pages in workspace, it might be 'title' key
                for key, val in props.items():
                    if val.get("type") == "title":
                        content = val.get("title", [])
                        if content:
                            title = content[0].get("plain_text", "Untitled")
                        break
                
                print(f"    - ID: {page['id']} | Title: '{title}'")

    except Exception as e:
        print(f"[!] Search Error: {e}")

if __name__ == "__main__":
    main()
