"""
Dav1d Integration Helpers
Add these functions to dav1d.py to enable external memory queries and workflow triggers
"""

import os
import requests
from typing import List, Dict, Optional
from notion_client import Client as NotionClient
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_GMAIL_DB = os.getenv("NOTION_GMAIL_DB_ID")
NOTION_TASKS_DB = os.getenv("NOTION_TASKS_DB_ID")
NOTION_WORKFLOWS_DB = os.getenv("NOTION_WORKFLOWS_DB_ID")

# Initialize Notion client if available
notion = NotionClient(auth=NOTION_TOKEN) if NOTION_TOKEN else None


# ──────────────────────────────────────────────────────────────
# EXTERNAL MEMORY SEARCH
# ──────────────────────────────────────────────────────────────

def search_gmail_memory(query: str, max_results: int = 10) -> List[Dict]:
    """Search Gmail database in Notion."""
    if not notion or not NOTION_GMAIL_DB:
        return []
    
    try:
        # Search in database (Notion's search is limited, using query for filtering)
        results = notion.databases.query(
            database_id=NOTION_GMAIL_DB,
            page_size=max_results
        )
        
        pages = results.get('results', [])
        
        # Extract relevant info
        emails = []
        for page in pages:
            props = page['properties']
            
            # Get subject
            subject_prop = props.get('Subject', {}).get('title', [])
            subject = subject_prop[0]['plain_text'] if subject_prop else 'No subject'
            
            # Get from
            from_prop = props.get('From', {}).get('rich_text', [])
            from_addr = from_prop[0]['plain_text'] if from_prop else 'Unknown'
            
            # Get category
            category_prop = props.get('Category', {}).get('select', {})
            category = category_prop.get('name', 'N/A')
            
            # Get priority
            priority_prop = props.get('Priority', {}).get('select', {})
            priority = priority_prop.get('name', 'N/A')
            
            emails.append({
                'id': page['id'],
                'subject': subject,
                'from': from_addr,
                'category': category,
                'priority': priority,
                'url': page['url']
            })
        
        return emails
    
    except Exception as e:
        print(f"❌ Failed to search Gmail memory: {e}")
        return []


def search_tasks_memory(status: str = None, priority: str = None) -> List[Dict]:
    """Search Tasks database in Notion."""
    if not notion or not NOTION_TASKS_DB:
        return []
    
    try:
        # Build filter
        filters = []
        if status:
            filters.append({
                "property": "Status",
                "select": {"equals": status}
            })
        if priority:
            filters.append({
                "property": "Priority",
                "select": {"equals": priority}
            })
        
        # Query database
        query_params = {"database_id": NOTION_TASKS_DB}
        if filters:
            if len(filters) == 1:
                query_params["filter"] = filters[0]
            else:
                query_params["filter"] = {"and": filters}
        
        results = notion.databases.query(**query_params)
        pages = results.get('results', [])
        
        # Extract tasks
        tasks = []
        for page in pages:
            props = page['properties']
            
            # Get name
            name_prop = props.get('Name', {}).get('title', [])
            name = name_prop[0]['plain_text'] if name_prop else 'Untitled'
            
            # Get status
            status_prop = props.get('Status', {}).get('select', {})
            task_status = status_prop.get('name', 'To Do')
            
            # Get priority
            priority_prop = props.get('Priority', {}).get('select', {})
            task_priority = priority_prop.get('name', 'Medium')
            
            tasks.append({
                'id': page['id'],
                'name': name,
                'status': task_status,
                'priority': task_priority,
                'url': page['url']
            })
        
        return tasks
    
    except Exception as e:
        print(f"❌ Failed to search tasks memory: {e}")
        return []


def search_all_memory(query: str) -> Dict:
    """Search across all external memory databases."""
    return {
        'emails': search_gmail_memory(query),
        'tasks': search_tasks_memory()
    }


# ──────────────────────────────────────────────────────────────
# WORKFLOW TRIGGERS
# ──────────────────────────────────────────────────────────────

def trigger_workflow(action: str, event_data: Dict, workflow_url: str = "http://localhost:3001") -> Dict:
    """Trigger a workflow action manually."""
    
    try:
        response = requests.post(
            f"{workflow_url}/trigger-manual",
            json={
                "action": action,
                "event_data": event_data
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}


def list_available_workflows(workflow_url: str = "http://localhost:3001") -> Dict:
    """List all available workflows."""
    
    try:
        response = requests.get(f"{workflow_url}/workflows", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ──────────────────────────────────────────────────────────────
# DAV1D COMMAND HANDLERS (Add these to dav1d.py)
# ──────────────────────────────────────────────────────────────

def handle_search_memory_command(user_input: str):
    """
    Handle /search-memory command
    Usage: /search-memory <query>
    """
    query = user_input.replace("/search-memory", "").strip()
    
    if not query:
        print("Usage: /search-memory <query>")
        return
    
    print(f"\n🔍 Searching external memory for: '{query}'")
    print("=" * 60)
    
    # Search emails
    emails = search_gmail_memory(query)
    if emails:
        print(f"\n📧 Found {len(emails)} emails:")
        for i, email in enumerate(emails[:5], 1):
            print(f"\n{i}. {email['subject']}")
            print(f"   From: {email['from']}")
            print(f"   Category: {email['category']} | Priority: {email['priority']}")
            print(f"   URL: {email['url']}")
    else:
        print("\n📧 No emails found")
    
    # Search tasks
    tasks = search_tasks_memory()
    if tasks:
        print(f"\n✅ Open tasks: {len(tasks)}")
        for i, task in enumerate(tasks[:5], 1):
            print(f"\n{i}. {task['name']}")
            print(f"   Status: {task['status']} | Priority: {task['priority']}")
            print(f"   URL: {task['url']}")
    else:
        print("\n✅ No tasks found")
    
    print("\n" + "=" * 60)


def handle_trigger_workflow_command(user_input: str):
    """
    Handle /trigger-workflow command
    Usage: /trigger-workflow <action_name>
    """
    parts = user_input.replace("/trigger-workflow", "").strip().split(maxsplit=1)
    
    if not parts:
        # List available workflows
        workflows = list_available_workflows()
        if "error" not in workflows:
            print("\n⚡ Available workflows:")
            for i, wf in enumerate(workflows.get('workflows', []), 1):
                print(f"\n{i}. {wf['name']}")
                print(f"   Trigger: {wf['trigger']['source']} → {wf['trigger']['event_type']}")
                print(f"   Actions: {', '.join(wf['actions'])}")
            
            print("\n⚡ Available actions:")
            for action in workflows.get('available_actions', []):
                print(f"   - {action}")
            
            print("\nUsage: /trigger-workflow <action_name>")
        else:
            print(f"❌ Workflow server not available: {workflows['error']}")
        return
    
    action = parts[0]
    
    print(f"\n⚡ Triggering workflow action: {action}")
    
    # Trigger with sample data
    result = trigger_workflow(action, {"source": "manual_trigger"})
    
    if "error" not in result:
        print(f"✅ Workflow triggered successfully")
        print(f"   Status: {result.get('status')}")
        print(f"   Result: {result.get('result')}")
    else:
        print(f"❌ Failed to trigger workflow: {result['error']}")


def handle_sync_tasks_command():
    """
    Handle /sync-tasks command
    Triggers bidirectional task sync
    """
    import subprocess
    
    print("\n🔄 Triggering task sync (Google Tasks ↔ Notion)...")
    
    try:
        result = subprocess.run(
            ["python", "tasks_notion_sync.py", "--direction", "both"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(result.stdout)
        if result.returncode == 0:
            print("✅ Task sync complete!")
        else:
            print(f"❌ Sync failed: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("❌ Sync timeout (>60s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")


def handle_sync_gmail_command():
    """
    Handle /sync-gmail command
    Triggers Gmail to Notion sync
    """
    import subprocess
    
    print("\n📧 Triggering Gmail sync (Gmail → Notion)...")
    
    try:
        result = subprocess.run(
            ["python", "gmail_to_notion.py", "--max", "10"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.returncode == 0:
            print("✅ Gmail sync complete!")
        else:
            print(f"❌ Sync failed: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        print("❌ Sync timeout (>120s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")


# ──────────────────────────────────────────────────────────────
# INTEGRATION SNIPPET FOR DAV1D.PY
# ──────────────────────────────────────────────────────────────

"""
# Add to dav1d.py main loop:

# Import at top
from dav1d_integrations import (
    handle_search_memory_command,
    handle_trigger_workflow_command,
    handle_sync_tasks_command,
    handle_sync_gmail_command
)

# Add in command processing section:

elif user_input.startswith("/search-memory"):
    handle_search_memory_command(user_input)
    continue

elif user_input.startswith("/trigger-workflow"):
    handle_trigger_workflow_command(user_input)
    continue

elif user_input == "/sync-tasks":
    handle_sync_tasks_command()
    continue

elif user_input == "/sync-gmail":
    handle_sync_gmail_command()
    continue

# Update help text:

/search-memory <query>    - Search external memory (emails, tasks)
/trigger-workflow <name>  - Trigger workflow automation
/sync-tasks              - Sync Google Tasks ↔ Notion
/sync-gmail              - Sync Gmail → Notion
"""
