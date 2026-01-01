import os
from notion_client import Client
from typing import Optional, List, Any
from kaedra.core.config import NOTION_TOKEN

class NotionService:
    def __init__(self):
        if not NOTION_TOKEN:
            print("[!] Notion Token not found. Notion service disabled.")
            self.client = None
            return
            
        try:
            self.client = Client(auth=NOTION_TOKEN)
            # Verify auth with a lightweight call (e.g. list users or just initialization)
            # We don't want to fail hard on init, but we'll print success
            print("[✅] Notion Service Initialized")
        except Exception as e:
            print(f"[!] Failed to initialize Notion Service: {e}")
            self.client = None

    def search_page(self, query: str) -> Optional[str]:
        """Search for a page ID by title."""
        if not self.client: return None
        try:
            results = self.client.search(query=query, filter={"property": "object", "value": "page"}).get("results")
            if results:
                return results[0]["id"]
        except Exception as e:
            print(f"[!] Notion Search Error: {e}")
        return None

    def append_children(self, block_id: str, children: List[Any]):
        """Append blocks to a page or block."""
        if not self.client: return
        try:
            self.client.blocks.children.append(block_id=block_id, children=children)
            print(f"[Notion] Appended {len(children)} blocks to {block_id}")
        except Exception as e:
            print(f"[!] Notion Append Error: {e}")

    def create_page(self, title: str, parent_page_id: str = None) -> Optional[str]:
        """Create a new page. If parent_page_id not provided, checks for 'Cinematic Universe' page as parent."""
        if not self.client: return None
        
        try:
            # Resulting Parent ID
            target_parent_id = parent_page_id
            
            # KNOWN IDs (Autodiscovered)
            KNOWN_UNIVERSE_ID = "e2d725ad-17cd-4423-bddc-53620d3dc7d4"

            # If no parent specified, try to find the Root Universe Page
            if not target_parent_id:
                # 1. Try Known ID (Fastest/Safest)
                try:
                    self.client.pages.retrieve(KNOWN_UNIVERSE_ID)
                    target_parent_id = KNOWN_UNIVERSE_ID
                except:
                    # 2. Search by Title
                    target_parent_id = self.search_page("Ai with Dav3 Cinematic Universe")
                    if not target_parent_id:
                         target_parent_id = self.search_page("Cinematic Universe")
                    if not target_parent_id:
                         target_parent_id = self.search_page("Kaedra")
            
            if not target_parent_id:
                print("[!] Cannot create page: No parent page found.")
                return None

            new_page = self.client.pages.create(
                parent={"page_id": target_parent_id},
                properties={
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {
                            "rich_text": [{"type": "text", "text": {"content": f"Welcome to {title}"}}]
                        }
                    }
                ]
            )
            page_id = new_page["id"]
            print(f"[✅] Created Notion Page: '{title}' (ID: {page_id})")
            return page_id
            
        except Exception as e:
            print(f"[!] Notion Create Page Error: {e}")
            return None

    def log_universe_idea(self, text: str):
        """High-level helper to log an idea to the Universe control page."""
        if not self.client: return
        
        # 1. Find or Create "Ai with Dav3 Cinematic Universe" page
        page_id = self.search_page("Ai with Dav3 Cinematic Universe")
        if not page_id:
             # Try generic search
             page_id = self.search_page("Cinematic Universe")
        
        if not page_id:
            print("[!] Could not find 'Cinematic Universe' page in Notion. Please create it and share with integration.")
            return

        # 2. Append the text
        paragraph_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }
        self.append_children(page_id, [paragraph_block])

    def _extract_id(self, text: str) -> Optional[str]:
        """Extract Notion UUID from URL or text."""
        # Regex for 32-char hex string (Notion ID style)
        import re
        match = re.search(r'([a-f0-9]{32})', text)
        if match:
            return match.group(1)
        return None

    def read_page_content(self, page_identifier: str) -> Optional[str]:
        """Read page content. Accepts Title, URL, or ID."""
        if not self.client: return None
        
        # 1. Try to extract ID from URL/text
        page_id = self._extract_id(page_identifier)
        
        # 2. If no ID found, search by Title
        if not page_id:
            page_id = self.search_page(page_identifier)
        
        if not page_id:
            return f"[Page '{page_identifier}' not found]"
        
        try:
            blocks = self.client.blocks.children.list(block_id=page_id).get("results", [])
            text_parts = []
            for block in blocks:
                block_type = block.get("type")
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    for rt in rich_text:
                        text_parts.append(rt.get("plain_text", ""))
                elif block_type == "image":
                    image_data = block.get("image", {})
                    url = ""
                    if "file" in image_data:
                        url = image_data["file"].get("url", "")
                    elif "external" in image_data:
                        url = image_data["external"].get("url", "")
                    
                    if url:
                        text_parts.append(f"[IMAGE FOUND: {url}]")
            return "\n".join(text_parts) if text_parts else "[Page is empty]"
        except Exception as e:
            return f"[Error reading page: {e}]"

    def list_subpages(self, parent_title: str = "Ai with Dav3 Cinematic Universe") -> List[str]:
        """List all child pages under a parent page."""
        if not self.client: return []
        
        # Try primary title
        page_id = self.search_page(parent_title)
        
        # Fallback 1: Generic "Cinematic Universe"
        if not page_id:
            print(f"[Notion] '{parent_title}' not found. Trying 'Cinematic Universe'...")
            page_id = self.search_page("Cinematic Universe")
            
        # Fallback 2: "Kaedra"
        if not page_id:
            print(f"[Notion] 'Cinematic Universe' not found. Trying 'Kaedra'...")
            page_id = self.search_page("Kaedra")

        if not page_id:
            print(f"[Notion] Index Scan Failed: Could not find parent page '{parent_title}' or fallbacks.")
            return []
        
        print(f"[Notion] Scanning children of {page_id}...")
        
        try:
            blocks = self.client.blocks.children.list(block_id=page_id).get("results", [])
            subpages = []
            for block in blocks:
                if block.get("type") == "child_page":
                    subpages.append(block.get("child_page", {}).get("title", "Untitled"))
            return subpages
        except Exception as e:
            print(f"[!] Error listing subpages: {e}")
            return []

    def get_universe_summary(self) -> str:
        """Get a summary of all universe content for context injection."""
        if not self.client: return "[Notion not connected]"
        
        subpages = self.list_subpages()
        if not subpages:
            return "[No universe pages found]"
        
        summary = f"Universe Pages ({len(subpages)}): " + ", ".join(subpages[:10])
    def append_to_page(self, page_identifier: str, text: str) -> str:
        """Append text to a page by Title, URL, or ID."""
        if not self.client: return "[Notion not connected]"
        
        # 1. Try ID/URL
        page_id = self._extract_id(page_identifier)
        
        # 2. Try Title
        if not page_id:
            page_id = self.search_page(page_identifier)
            
        if not page_id:
            return f"[Page '{page_identifier}' not found]"
            
        paragraph_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
        
        try:
            self.append_children(page_id, [paragraph_block])
            return f"[Updated '{page_identifier}' with new lore]"
        except Exception as e:
            return f"[Error updating page: {e}]"

