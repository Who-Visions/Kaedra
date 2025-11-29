"""
Tasks & Notion Sync for Dav1d
Bidirectional sync between Google Tasks and Notion databases
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Google Auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Notion
from notion_client import Client as NotionClient

# Gemini for task enrichment
from google import genai
from google.genai import types

load_dotenv()

# Configuration
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_TASKS_DB = os.getenv("NOTION_TASKS_DB_ID")
PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

# Google Tasks API Scopes
SCOPES = ['https://www.googleapis.com/auth/tasks']

if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN not set in .env")

# Initialize clients
notion = NotionClient(auth=NOTION_TOKEN)
gemini_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)


# ──────────────────────────────────────────────────────────────
# GOOGLE TASKS AUTHENTICATION
# ──────────────────────────────────────────────────────────────

def get_tasks_service():
    """Authenticate with Google Tasks API using OAuth 2.0."""
    creds = None
    token_path = 'token_tasks.json'
    creds_path = 'credentials_tasks.json'
    
    # Load existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    f"Missing {creds_path}. Download from Google Cloud Console:\n"
                    "https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('tasks', 'v1', credentials=creds)


# ──────────────────────────────────────────────────────────────
# GOOGLE TASKS OPERATIONS
# ──────────────────────────────────────────────────────────────

def get_task_lists(service) -> List[Dict]:
    """Get all task lists."""
    results = service.tasklists().list().execute()
    return results.get('items', [])


def get_tasks_from_list(service, tasklist_id: str) -> List[Dict]:
    """Get all tasks from a specific list."""
    results = service.tasks().list(tasklist=tasklist_id).execute()
    return results.get('items', [])


def create_google_task(service, tasklist_id: str, title: str, notes: str = "", due: str = None) -> Dict:
    """Create a new Google Task."""
    task = {
        'title': title,
        'notes': notes
    }
    
    if due:
        task['due'] = due
    
    result = service.tasks().insert(
        tasklist=tasklist_id,
        body=task
    ).execute()
    
    return result


def mark_task_complete(service, tasklist_id: str, task_id: str):
    """Mark a Google Task as completed."""
    service.tasks().update(
        tasklist=tasklist_id,
        task=task_id,
        body={'status': 'completed'}
    ).execute()


# ──────────────────────────────────────────────────────────────
# NOTION TASKS OPERATIONS
# ──────────────────────────────────────────────────────────────

def get_notion_tasks(database_id: str = None) -> List[Dict]:
    """Get all tasks from Notion database."""
    if not database_id:
        database_id = NOTION_TASKS_DB
    
    if not database_id:
        print("⚠️  NOTION_TASKS_DB_ID not set")
        return []
    
    try:
        results = notion.databases.query(database_id=database_id)
        return results.get('results', [])
    except Exception as e:
        print(f"❌ Failed to fetch Notion tasks: {e}")
        return []


def create_notion_task(task_data: Dict, database_id: str = None) -> Optional[str]:
    """Create a new task in Notion database."""
    if not database_id:
        database_id = NOTION_TASKS_DB
    
    if not database_id:
        print("⚠️  NOTION_TASKS_DB_ID not set")
        return None
    
    try:
        # Build properties based on task data
        properties = {
            "Name": {
                "title": [
                    {"text": {"content": task_data['title'][:2000]}}
                ]
            },
            "Status": {
                "select": {"name": task_data.get('status', 'To Do')}
            }
        }
        
        # Add optional fields
        if task_data.get('priority'):
            properties["Priority"] = {
                "select": {"name": task_data['priority']}
            }
        
        if task_data.get('due'):
            properties["Due Date"] = {
                "date": {"start": task_data['due']}
            }
        
        if task_data.get('tags'):
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in task_data['tags']]
            }
        
        # Create children blocks if notes exist
        children = []
        if task_data.get('notes'):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": task_data['notes'][:2000]}}]
                }
            })
        
        # Create page
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            children=children if children else None
        )
        
        return page['id']
    
    except Exception as e:
        print(f"❌ Failed to create Notion task: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_notion_task_status(page_id: str, status: str):
    """Update a Notion task's status."""
    try:
        notion.pages.update(
            page_id=page_id,
            properties={
                "Status": {"select": {"name": status}}
            }
        )
    except Exception as e:
        print(f"❌ Failed to update Notion task: {e}")


# ──────────────────────────────────────────────────────────────
# AI TASK ENRICHMENT
# ──────────────────────────────────────────────────────────────

async def enrich_task_with_gemini(task_title: str, task_notes: str = "") -> Dict:
    """Use Gemini to enrich task with suggested priority, tags, and breakdown."""
    
    prompt = f"""Analyze this task and provide structured suggestions.

Task: {task_title}
Notes: {task_notes}

Provide:
1. Priority (low/medium/high/urgent)
2. Estimated time (in minutes)
3. Suggested tags (3-5 relevant tags)
4. Breakdown (if complex, break into subtasks)
5. Category (work/personal/learning/admin)

Format as JSON:
{{
    "priority": "medium",
    "estimated_time": 30,
    "tags": ["tag1", "tag2"],
    "subtasks": ["subtask 1", "subtask 2"],
    "category": "work"
}}
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        import json
        return json.loads(response.text)
    
    except Exception as e:
        print(f"❌ Gemini enrichment failed: {e}")
        return {
            "priority": "medium",
            "estimated_time": 30,
            "tags": [],
            "subtasks": [],
            "category": "uncategorized"
        }


# ──────────────────────────────────────────────────────────────
# SYNC FUNCTIONS
# ──────────────────────────────────────────────────────────────

async def sync_google_tasks_to_notion():
    """Sync Google Tasks → Notion with AI enrichment."""
    
    print("🔄 Syncing Google Tasks → Notion...")
    
    try:
        service = get_tasks_service()
        
        # Get all task lists
        task_lists = get_task_lists(service)
        print(f"📋 Found {len(task_lists)} task lists")
        
        total_synced = 0
        
        for tasklist in task_lists:
            list_name = tasklist['title']
            list_id = tasklist['id']
            
            print(f"\n📝 Processing list: {list_name}")
            
            # Get tasks from this list
            tasks = get_tasks_from_list(service, list_id)
            print(f"   Found {len(tasks)} tasks")
            
            for task in tasks:
                # Skip completed tasks
                if task.get('status') == 'completed':
                    continue
                
                title = task.get('title', 'Untitled')
                notes = task.get('notes', '')
                due = task.get('due')
                
                print(f"\n   → {title[:50]}")
                
                # Enrich with Gemini
                enrichment = await enrich_task_with_gemini(title, notes)
                print(f"      Priority: {enrichment['priority']} | Tags: {enrichment['tags']}")
                
                # Create in Notion
                task_data = {
                    'title': f"[{list_name}] {title}",
                    'notes': notes,
                    'status': 'To Do',
                    'priority': enrichment['priority'].capitalize(),
                    'tags': enrichment['tags'] + [list_name],
                    'due': due
                }
                
                page_id = create_notion_task(task_data)
                if page_id:
                    print(f"      ✅ Created in Notion: {page_id[:8]}")
                    total_synced += 1
        
        print(f"\n✅ Sync complete! Synced {total_synced} tasks to Notion")
    
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()


async def sync_notion_to_google_tasks():
    """Sync Notion tasks → Google Tasks."""
    
    print("🔄 Syncing Notion → Google Tasks...")
    
    if not NOTION_TASKS_DB:
        print("⚠️  NOTION_TASKS_DB_ID not set. Skipping.")
        return
    
    try:
        service = get_tasks_service()
        
        # Get default task list
        task_lists = get_task_lists(service)
        if not task_lists:
            print("❌ No Google Task lists found")
            return
        
        default_list = task_lists[0]  # Use first list
        list_id = default_list['id']
        
        print(f"📋 Using Google Tasks list: {default_list['title']}")
        
        # Get Notion tasks
        notion_tasks = get_notion_tasks()
        print(f"📝 Found {len(notion_tasks)} Notion tasks")
        
        synced = 0
        
        for notion_task in notion_tasks:
            # Extract properties
            props = notion_task['properties']
            
            # Get title
            title_prop = props.get('Name', {}).get('title', [])
            if not title_prop:
                continue
            title = title_prop[0]['plain_text']
            
            # Get status
            status_prop = props.get('Status', {}).get('select', {})
            status = status_prop.get('name', 'To Do')
            
            # Skip completed
            if status.lower() in ['done', 'completed']:
                continue
            
            print(f"\n   → {title[:50]}")
            
            # Create in Google Tasks
            create_google_task(service, list_id, title=title)
            print(f"      ✅ Created in Google Tasks")
            synced += 1
        
        print(f"\n✅ Sync complete! Synced {synced} tasks to Google Tasks")
    
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Tasks between Google and Notion")
    parser.add_argument(
        "--direction",
        choices=["google-to-notion", "notion-to-google", "both"],
        default="google-to-notion",
        help="Sync direction"
    )
    
    args = parser.parse_args()
    
    print("🚀 Tasks & Notion Sync - Dav1d")
    print("=" * 50)
    
    if args.direction in ["google-to-notion", "both"]:
        asyncio.run(sync_google_tasks_to_notion())
    
    if args.direction in ["notion-to-google", "both"]:
        asyncio.run(sync_notion_to_google_tasks())
