"""
Handoff Notes Sync to Notion
Syncs agent handoff markdown files to a Notion database.
Uses "The Observatory" integration for Dav3's Space.
"""
import os
import re
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

# Force UTF-8 output for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import httpx
except ImportError:
    print("Missing dependencies. Run: pip install httpx")
    exit(1)

# The Observatory Integration Token (Dav3's Space)
# Token from Notion integration settings - "The Observatory"
OBSERVATORY_TOKEN = os.getenv("OBSERVATORY_TOKEN")

# Handoff Database ID (from URL)
HANDOFF_DB_ID = "2e7ca671311e80e6ae14eded33870f70"

# Handoff files location
HANDOFF_DIR = Path(__file__).parent.parent / ".agent" / "handoff"


def parse_handoff_md(filepath: Path) -> dict:
    """Parse a handoff markdown file into structured data."""
    content = filepath.read_text(encoding="utf-8")
    
    # Extract title (first H1)
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else filepath.stem
    
    # Extract agent name from title
    # Agent Hierarchy: Dave (human) → Antigravity (Gemini CLI) → Kaedra (Vertex AI) → Blade/Nyx (sub-agents)
    agent = "Unknown"
    if "BLADE" in title.upper():
        agent = "Blade"
    elif "NYX" in title.upper():
        agent = "Nyx"
    elif "KAEDRA" in title.upper():
        agent = "Kaedra"
    elif "ANTIGRAVITY" in title.upper():
        agent = "Antigravity"
    elif "DAVE" in title.upper() or "DAV3" in title.upper():
        agent = "Dave"
    elif "GCP" in title.upper() or "SYSTEM" in title.upper():
        agent = "System"
    
    # Extract last update timestamp
    last_update_match = re.search(r'\*\*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\*\*', content)
    last_update = last_update_match.group(1) if last_update_match else datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Count completed items
    completed = len(re.findall(r'\[x\]', content))
    pending = len(re.findall(r'\[ \]', content))
    
    return {
        "title": title,
        "agent": agent,
        "last_update": last_update,
        "completed": completed,
        "pending": pending,
        "content": content[:1900]  # Truncate for Notion code block limit
    }


def sync_to_notion():
    """Sync all handoff files to Notion database using The Observatory token."""
    # Use Observatory token (separate from VeilVerse token)
    headers = {
        "Authorization": f"Bearer {OBSERVATORY_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    if not HANDOFF_DIR.exists():
        print(f"❌ Handoff directory not found: {HANDOFF_DIR}")
        return
    
    handoff_files = list(HANDOFF_DIR.glob("*.md"))
    print(f"Found {len(handoff_files)} handoff files")
    print(f"Using 'The Observatory' integration")
    
    for filepath in handoff_files:
        data = parse_handoff_md(filepath)
        
        # Safe print for Windows console
        safe_title = data['title'].encode('ascii', 'ignore').decode('ascii').strip()
        print(f"\nSyncing: {safe_title}")
        print(f"   Agent: {data['agent']}")
        print(f"   Last Update: {data['last_update']}")
        print(f"   Completed: {data['completed']} | Pending: {data['pending']}")
        
        # Create page in Notion using actual database properties
        try:
            page_data = {
                "parent": {"database_id": HANDOFF_DB_ID},
                "properties": {
                    "Project Name": {
                        "title": [{"text": {"content": data["title"]}}]
                    },
                    "Current Agent": {
                        "select": {"name": data["agent"]}
                    },
                    "Status": {
                        "status": {"name": "In Progress"}
                    },
                    "Priority": {
                        "select": {"name": "Medium"}
                    },
                    "Last Updated": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "Context Notes": {
                        "rich_text": [{"text": {"content": f"Completed: {data['completed']} | Pending: {data['pending']}"}}]
                    },
                    "Next Actions": {
                        "rich_text": [{"text": {"content": "Review handoff and pick up pending tasks"}}]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": "markdown",
                            "rich_text": [{"text": {"content": data["content"]}}]
                        }
                    }
                ]
            }
            
            # Use httpx with Observatory token
            response = httpx.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=page_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                print(f"   Synced to Notion")
            else:
                # Safe print error
                safe_err = response.text[:200].encode('ascii', 'ignore').decode('ascii')
                print(f"   Error: {response.status_code} - {safe_err}")
                
        except Exception as e:
            # Safe print exception
            safe_e = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"   Failed: {safe_e}")
    
    print(f"\nSync complete!")


if __name__ == "__main__":
    sync_to_notion()
