import os
import toml
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
try:
    from notion_client import Client
except ImportError:
    print("❌ notion-client not installed. Run: pip install notion-client")
    exit(1)

# Paths
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "kaedra" / "config" / "notion.toml"
WORLDS_ROOT = ROOT / "lore" / "worlds"


def _retry_request(func, max_retries=3, base_delay=1.0):
    """Retry with exponential backoff for rate limits (429)."""
    import requests
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"   ⏳ Rate limited. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
    return None


class NotionBridge:
    def __init__(self, world_id: str):
        self.world_id = world_id
        self.world_path = WORLDS_ROOT / world_id
        
        # Load Config
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
            
        self.config = toml.load(CONFIG_PATH)
        self.token = self.config["notion"]["token"]
        
        if self.token == "YOUR_NOTION_TOKEN":
            print("⚠️ Notion Token not set in kaedra/config/notion.toml")
            self.client = None
        else:
            self.client = Client(auth=self.token)
            
    def check_connection(self) -> bool:
        if not self.client: return False
        try:
            me = self.client.users.me()
            print(f"✅ Connected to Notion as: {me['name']}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def pull_ingestion_queue(self):
        """
        Pull 'Approved' items from Notion Ingestion Queue -> local ingestion.json
        """
        if not self.client: return
        
        # Use Data Source ID (from ds/ part of URL, not db= part)
        ds_id = self.config["mappings"]["ingestion_json"]
        print(f"📥 Pulling Ingestion Queue (Data Source ID: {ds_id})...")
        
        try:
            # Query using direct requests with 2025-09-03 API
            import requests
            import uuid
            
            # Format UUID with dashes if needed
            if len(ds_id) == 32:
                ds_id = str(uuid.UUID(ds_id))
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": "2025-09-03",
                "Content-Type": "application/json"
            }
            url = f"https://api.notion.com/v1/data_sources/{ds_id}/query"
            payload = {
                "filter": {
                    "property": "Status",
                    "select": {
                        "equals": "Approved"
                    }
                }
            }
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            response = resp.json()
            
            new_items = []
            for page in response["results"]:
                props = page["properties"]
                title = props["Title"]["title"][0]["plain_text"] if props["Title"]["title"] else "Untitled"
                
                item = {
                    "id": page["id"],
                    "title": title,
                    "status": "Approved",
                    "category": "Imported",
                    "notion_url": page["url"]
                }
                new_items.append(item)
                
            print(f"   Found {len(new_items)} approved items.")
            
            # Merge with existing: deduplicate by ID
            ingest_path = self.world_path / "ingestion.json"
            existing_items = []
            existing_ids = set()
            if ingest_path.exists():
                existing_data = json.loads(ingest_path.read_text(encoding="utf-8"))
                existing_items = existing_data.get("items", [])
                existing_ids = {item["id"] for item in existing_items}
            
            # Add only new items
            added = 0
            for item in new_items:
                if item["id"] not in existing_ids:
                    existing_items.append(item)
                    added += 1
            
            data = {"items": existing_items}
            ingest_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"✅ Saved to {ingest_path} (+{added} new)")
            
            # Writeback: Update status to "Imported" in Notion
            if new_items:
                self._mark_as_imported([item["id"] for item in new_items], ds_id, headers)
            
        except Exception as e:
            print(f"❌ Pull failed: {e}")

    def _mark_as_imported(self, page_ids: List[str], ds_id: str, headers: dict):
        """Update Notion items' status to 'Imported' after pulling."""
        import requests
        
        for page_id in page_ids:
            try:
                url = f"https://api.notion.com/v1/pages/{page_id}"
                payload = {
                    "properties": {
                        "Status": {
                            "select": {"name": "Imported"}
                        }
                    }
                }
                resp = requests.patch(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
                resp.raise_for_status()
            except Exception as e:
                print(f"   ⚠️ Could not mark {page_id[:8]}... as Imported: {e}")

    def push_to_bible(self):
        """
        Push local world_bible.json entries (marked 'Pending Sync') to Notion World Bible.
        """
        if not self.client: return
        
        import requests
        import uuid
        
        bible_path = self.world_path / "world_bible.json"
        if not bible_path.exists():
            print("⚠️ No world_bible.json found.")
            return
            
        bible = json.loads(bible_path.read_text(encoding="utf-8"))
        
        # Get World Bible page ID (we'll create pages under it)
        parent_page_id = self.config["pages"]["world_bible"]
        if len(parent_page_id) == 32:
            parent_page_id = str(uuid.UUID(parent_page_id))
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        
        pushed = 0
        sections = bible.get("sections", {})
        for section_name, entries in sections.items():
            for entry in entries:
                # Only push entries marked for sync
                if entry.get("sync_status") != "pending":
                    continue
                    
                title = entry.get("name", "Untitled Entry")
                entry_type = entry.get("type", section_name)  # Use section name as default type
                description = entry.get("description", "")
                
                # Create page in Notion under World Bible
                url = "https://api.notion.com/v1/pages"
                payload = {
                    "parent": {"page_id": parent_page_id},
                    "properties": {
                        "title": {
                            "title": [{"type": "text", "text": {"content": title}}]
                        }
                    },
                    "children": [
                        {
                            "object": "block",
                            "type": "callout",
                            "callout": {
                                "icon": {"emoji": "📚"},
                                "rich_text": [{"type": "text", "text": {"content": f"Type: {entry_type}"}}]
                            }
                        },
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": description}}]
                            }
                        }
                    ]
                }
                
                try:
                    resp = requests.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    new_page = resp.json()
                    print(f"   📤 Pushed: '{title}' -> {new_page['url']}")
                    
                    # Mark as synced
                    entry["sync_status"] = "synced"
                    entry["notion_id"] = new_page["id"]
                    entry["notion_url"] = new_page["url"]
                    pushed += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to push '{title}': {e}")
        
        if pushed > 0:
            bible_path.write_text(json.dumps(bible, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"✅ Pushed {pushed} entries to Notion World Bible.")
        else:
            print("📭 No entries pending sync.")

    def upload_file(self, file_path: Path, page_id: str = None) -> Optional[str]:
        """
        Upload a file to Notion and optionally attach to a page.
        Returns the file upload ID on success.
        
        Supports: images, PDFs, audio, video
        - Single-part: up to 20MB
        - Multi-part: 20MB - 5GB (paid workspaces)
        """
        import requests
        import uuid
        import mimetypes
        import math
        
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return None
            
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
            
        file_size = file_path.stat().st_size
        CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2025-09-03"
        }
        
        try:
            if file_size <= 20 * 1024 * 1024:
                # Single-part upload
                return self._upload_single_part(file_path, mime_type, page_id, headers)
            else:
                # Multi-part upload for large files
                return self._upload_multi_part(file_path, mime_type, page_id, headers, file_size, CHUNK_SIZE)
                
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None

    def _upload_single_part(self, file_path: Path, mime_type: str, page_id: str, headers: dict) -> Optional[str]:
        """Handle single-part upload for files <= 20MB."""
        import requests
        import uuid
        
        create_url = "https://api.notion.com/v1/file_uploads"
        create_payload = {
            "filename": file_path.name,
            "content_type": mime_type
        }
        resp = requests.post(create_url, headers={**headers, "Content-Type": "application/json"}, json=create_payload)
        resp.raise_for_status()
        upload_info = resp.json()
        
        file_upload_id = upload_info["id"]
        upload_url = upload_info["upload_url"]
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, mime_type)}
            resp = requests.post(upload_url, files=files)
            resp.raise_for_status()
        
        print(f"   📎 Uploaded: {file_path.name} (ID: {file_upload_id})")
        
        self._attach_to_page(file_upload_id, mime_type, page_id, headers)
        return file_upload_id

    def _upload_multi_part(self, file_path: Path, mime_type: str, page_id: str, headers: dict, file_size: int, chunk_size: int) -> Optional[str]:
        """Handle multi-part upload for files > 20MB."""
        import requests
        import uuid
        import math
        
        num_parts = math.ceil(file_size / chunk_size)
        print(f"   📦 Large file ({file_size / 1024 / 1024:.1f}MB) - using {num_parts}-part upload...")
        
        # Step 1: Create multi-part file upload
        create_url = "https://api.notion.com/v1/file_uploads"
        create_payload = {
            "mode": "multi_part",
            "number_of_parts": num_parts,
            "filename": file_path.name,
            "content_type": mime_type
        }
        resp = requests.post(create_url, headers={**headers, "Content-Type": "application/json"}, json=create_payload)
        resp.raise_for_status()
        upload_info = resp.json()
        
        file_upload_id = upload_info["id"]
        
        # Step 2: Send each part
        with open(file_path, "rb") as f:
            for part_num in range(1, num_parts + 1):
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                    
                send_url = f"https://api.notion.com/v1/file_uploads/{file_upload_id}/send"
                files = {"file": (file_path.name, chunk, mime_type)}
                data = {"part_number": str(part_num)}
                
                resp = requests.post(send_url, headers=headers, files=files, data=data)
                resp.raise_for_status()
                print(f"      Part {part_num}/{num_parts} sent")
        
        # Step 3: Complete the upload
        complete_url = f"https://api.notion.com/v1/file_uploads/{file_upload_id}/complete"
        resp = requests.post(complete_url, headers={**headers, "Content-Type": "application/json"})
        resp.raise_for_status()
        
        print(f"   📎 Uploaded: {file_path.name} (ID: {file_upload_id})")
        
        self._attach_to_page(file_upload_id, mime_type, page_id, headers)
        return file_upload_id

    def _attach_to_page(self, file_upload_id: str, mime_type: str, page_id: str, headers: dict):
        """Attach uploaded file to a page as a block."""
        import requests
        import uuid
        
        if not page_id:
            return
            
        if len(page_id) == 32:
            page_id = str(uuid.UUID(page_id))
            
        append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        block_type = "image" if mime_type.startswith("image/") else "file"
        block_payload = {
            "children": [{
                "object": "block",
                "type": block_type,
                block_type: {
                    "type": "file_upload",
                    "file_upload": {"id": file_upload_id}
                }
            }]
        }
        resp = requests.patch(append_url, headers={**headers, "Content-Type": "application/json"}, json=block_payload)
        resp.raise_for_status()
        print(f"   ✅ Attached to page: {page_id}")

    def download_files(self, page_id: str, output_dir: Path = None) -> List[Path]:
        """
        Download all files/images from a Notion page to local storage.
        Returns list of downloaded file paths.
        
        Note: URLs are temporary (1hr expiry), so download immediately.
        """
        import requests
        import uuid
        from urllib.parse import urlparse
        
        if output_dir is None:
            output_dir = self.world_path / "assets"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if len(page_id) == 32:
            page_id = str(uuid.UUID(page_id))
            
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2025-09-03"
        }
        
        downloaded = []
        
        try:
            # Retrieve block children
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            blocks = resp.json().get("results", [])
            
            for block in blocks:
                block_type = block.get("type")
                
                # Check for file-containing block types
                if block_type in ["image", "file", "video", "audio", "pdf"]:
                    file_obj = block.get(block_type, {})
                    file_type = file_obj.get("type")
                    
                    if file_type == "file":
                        # Uploaded via UI - has temporary URL
                        file_url = file_obj.get("file", {}).get("url")
                    elif file_type == "external":
                        # External URL
                        file_url = file_obj.get("external", {}).get("url")
                    elif file_type == "file_upload":
                        # Uploaded via API
                        file_url = file_obj.get("file_upload", {}).get("url")
                    else:
                        continue
                    
                    if not file_url:
                        continue
                    
                    # Download file
                    try:
                        parsed = urlparse(file_url)
                        filename = Path(parsed.path).name or f"{block['id']}.bin"
                        # Clean filename
                        filename = filename.split("?")[0]
                        
                        file_resp = requests.get(file_url, stream=True)
                        file_resp.raise_for_status()
                        
                        out_path = output_dir / filename
                        with open(out_path, "wb") as f:
                            for chunk in file_resp.iter_content(8192):
                                f.write(chunk)
                        
                        print(f"   📥 Downloaded: {filename}")
                        downloaded.append(out_path)
                        
                    except Exception as e:
                        print(f"   ⚠️ Failed to download {file_url}: {e}")
            
            if downloaded:
                print(f"✅ Downloaded {len(downloaded)} files to {output_dir}")
            else:
                print("📭 No files found on page.")
                
        except Exception as e:
            print(f"❌ Failed to retrieve page blocks: {e}")
        
        return downloaded

    def sync_all(self):
        print(f"🔄 Syncing World: {self.world_id}")
        if self.check_connection():
            self.pull_ingestion_queue()
            self.push_to_bible()

if __name__ == "__main__":
    # Test run
    import sys
    wid = "world_bee9d6ac" # Validation World ID default
    if len(sys.argv) > 1:
        wid = sys.argv[1]
        
    bridge = NotionBridge(wid)
    bridge.sync_all()
