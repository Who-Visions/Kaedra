from kaedra.services.notion import NotionService
import sys

def main():
    print("[*] Initializing Notion Service...")
    service = NotionService()
    
    if not service.client:
        print("[!] Service failed to initialize. Check configuration.")
        return

    print("[*] Creating 'VeilVerse_AutoTest' Project Folder...")
    page_id = service.create_page("VeilVerse_AutoTest")
    
    if page_id:
        print(f"[✅] SUCCESS: VeilVerse page created with ID: {page_id}")
    else:
        print("[!] FAILURE: Could not create VeilVerse page. Ensure 'Cinematic Universe' page exists and integration has access.")

if __name__ == "__main__":
    main()
