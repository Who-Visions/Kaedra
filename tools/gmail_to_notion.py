"""
Gmail to Notion Ingestion Bridge
Polls Gmail for 'VeilVerse' related emails and pushes them to the Notion Ingestion Queue.
"""
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from kaedra.services.google_workspace import GoogleWorkspaceService
import requests
import toml

class GmailNotionBridge:
    def __init__(self):
        self.google = GoogleWorkspaceService()
        
        # Load Notion config
        config_path = ROOT / "kaedra" / "config" / "notion.toml"
        self.config = toml.load(config_path)
        self.notion_token = self.config["notion"]["token"]
        self.db_id = self.config["databases"]["ingestion_queue"]
        
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }

    def push_to_notion(self, subject: str, sender: str, body: str, msg_id: str) -> bool:
        """Create an ingestion item from an email."""
        print(f"📥 Processing: {subject}")
        
        # Prepare Notion blocks (Split body into 2000-char chunks)
        chunk_size = 1900
        all_blocks = []
        for i in range(0, len(body), chunk_size):
            all_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": body[i:i+chunk_size]}}]
                }
            })

        # Create page with initial blocks
        initial_blocks = [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "📧"},
                    "rich_text": [{"text": {"content": f"From: {sender}"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Email Content"}}]
                }
            }
        ]
        
        first_batch = all_blocks[:80]
        remaining_blocks = all_blocks[80:]

        payload = {
            "parent": {"database_id": self.db_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": f"EMAIL: {subject[:80]}"}}]
                },
                "Status": {
                    "select": {"name": "New"}
                },
                "Source URL": {
                    "url": f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
                }
            },
            "children": initial_blocks + first_batch
        }
        
        resp = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload)
        if resp.status_code != 200:
            return False
            
        result = resp.json()
        page_id = result.get('id')
        
        # Append remaining
        if remaining_blocks and page_id:
            for i in range(0, len(remaining_blocks), 100):
                batch = remaining_blocks[i:i + 100]
                requests.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=self.headers,
                    json={"children": batch}
                )
        
        return True

    def run(self, query: str = "VeilVerse", limit: int = 5):
        """Find emails and push to Notion."""
        print(f"🔍 Searching Gmail for: '{query}'...")
        
        service = self.google._get_service('gmail', 'v1')
        if not service:
            print("❌ Google Service not initialized.")
            return

        # Search for messages
        results = service.users().messages().list(userId='me', q=query, maxResults=limit).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print("   No matching emails found.")
            return

        success = 0
        for msg in messages:
            # Check if already processed (could use a local cache or a 'Processed' label)
            # For now, we'll just pull the metadata
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = m.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            # Simple body extraction (Plain text)
            parts = m.get('payload', {}).get('parts', [])
            body = m.get('snippet', '') # Fallback to snippet if multipart is complex
            
            # If we want full body, we'd need to parse data from parts.
            # Keeping it simple for the bridge.
            
            if self.push_to_notion(subject, sender, body, msg['id']):
                success += 1
                # Mark as read or add label?
                # service.users().messages().modify(userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        
        print(f"✅ Successfully ingested {success}/{len(messages)} emails to Notion.")

if __name__ == "__main__":
    bridge = GmailNotionBridge()
    bridge.run()
