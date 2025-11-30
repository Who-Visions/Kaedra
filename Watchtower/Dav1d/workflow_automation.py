"""
Workflow Automation Integration for Dav1d
Trigger Dav1d agents via Google Workspace events (Gmail, Drive, Calendar)
Inspired by Cloud Flow Director + AppiWorks patterns
"""

import os
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Gemini for intelligent routing
from google import genai
from google.genai import types

# Notion for logging
from notion_client import Client as NotionClient

load_dotenv()

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_WORKFLOWS_DB = os.getenv("NOTION_WORKFLOWS_DB_ID")

# Initialize clients
gemini_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
notion = NotionClient(auth=NOTION_TOKEN) if NOTION_TOKEN else None

app = FastAPI(title="Dav1d Workflow Automation")


# ──────────────────────────────────────────────────────────────
# WORKFLOW DEFINITIONS
# ──────────────────────────────────────────────────────────────

class WorkflowTrigger(BaseModel):
    """Defines a workflow trigger."""
    trigger_type: str  # gmail, drive, calendar, manual
    condition: Dict  # Conditions to match
    action: str  # What to execute


class WorkflowEvent(BaseModel):
    """Incoming event from Google Workspace."""
    source: str  # gmail, drive, calendar
    event_type: str  # new_email, file_uploaded, event_created
    data: Dict  # Event payload


# ──────────────────────────────────────────────────────────────
# WORKFLOW ACTIONS (What Dav1d Can Do)
# ──────────────────────────────────────────────────────────────

async def action_analyze_email(event_data: Dict) -> Dict:
    """Analyze email with Gemini and respond."""
    print(f"📧 Analyzing email: {event_data.get('subject', 'No subject')}")
    
    # Extract email content
    subject = event_data.get('subject', '')
    body = event_data.get('body', '')
    from_addr = event_data.get('from', '')
    
    # Analyze with Gemini
    prompt = f"""Analyze this email and suggest a response.

From: {from_addr}
Subject: {subject}
Body:
{body[:1000]}

Provide:
1. Intent (question/request/notification/spam)
2. Urgency (low/medium/high)
3. Suggested response (if action needed)
4. Should auto-respond? (yes/no)

Format as JSON.
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        import json
        analysis = json.loads(response.text)
        
        print(f"   ✅ Intent: {analysis.get('intent')} | Urgency: {analysis.get('urgency')}")
        return analysis
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return {"intent": "unknown", "urgency": "low"}


async def action_summarize_document(event_data: Dict) -> Dict:
    """Summarize uploaded document."""
    print(f"📄 Summarizing document: {event_data.get('filename', 'Unknown')}")
    
    # In production, fetch file from Drive API
    filename = event_data.get('filename', '')
    file_type = event_data.get('mime_type', '')
    
    # For now, return mock summary
    return {
        "filename": filename,
        "summary": f"Summary of {filename} will be generated here",
        "file_type": file_type
    }


async def action_create_calendar_briefing(event_data: Dict) -> Dict:
    """Create briefing for upcoming calendar event."""
    print(f"📅 Creating briefing for: {event_data.get('event_name', 'Event')}")
    
    event_name = event_data.get('event_name', '')
    event_time = event_data.get('start_time', '')
    attendees = event_data.get('attendees', [])
    
    # Generate briefing with Gemini
    prompt = f"""Create a briefing for this upcoming meeting.

Event: {event_name}
Time: {event_time}
Attendees: {', '.join(attendees)}

Provide:
1. Suggested agenda
2. Key topics to cover
3. Preparation checklist

Format as JSON.
"""
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json"
            )
        )
        
        import json
        return json.loads(response.text)
    
    except Exception as e:
        print(f"❌ Briefing generation failed: {e}")
        return {"agenda": [], "topics": [], "checklist": []}


async def action_trigger_dav1d_analysis(event_data: Dict) -> Dict:
    """Trigger full Dav1d multi-agent analysis."""
    print(f"🧠 Triggering Dav1d analysis...")
    
    # In production, call dav1d.py's multi-agent system
    # For now, return acknowledgment
    
    return {
        "status": "queued",
        "agents": ["DAV1D", "CIPHER", "ECHO"],
        "message": "Multi-agent analysis queued"
    }


# ──────────────────────────────────────────────────────────────
# WORKFLOW ENGINE
# ──────────────────────────────────────────────────────────────

# Map action names to functions
ACTION_HANDLERS: Dict[str, Callable] = {
    "analyze_email": action_analyze_email,
    "summarize_document": action_summarize_document,
    "create_calendar_briefing": action_create_calendar_briefing,
    "trigger_dav1d_analysis": action_trigger_dav1d_analysis,
}


# Pre-defined workflow rules
WORKFLOW_RULES = [
    {
        "name": "Auto-analyze urgent emails",
        "trigger": {
            "source": "gmail",
            "event_type": "new_email",
            "conditions": {
                "has_keyword": ["urgent", "asap", "important"]
            }
        },
        "actions": ["analyze_email", "trigger_dav1d_analysis"]
    },
    {
        "name": "Summarize shared documents",
        "trigger": {
            "source": "drive",
            "event_type": "file_shared",
            "conditions": {
                "file_type": ["pdf", "docx"]
            }
        },
        "actions": ["summarize_document"]
    },
    {
        "name": "Prepare for meetings",
        "trigger": {
            "source": "calendar",
            "event_type": "event_starting_soon",
            "conditions": {
                "minutes_before": 30
            }
        },
        "actions": ["create_calendar_briefing"]
    }
]


async def match_workflow_rules(event: WorkflowEvent) -> List[Dict]:
    """Match incoming event to workflow rules."""
    matched_rules = []
    
    for rule in WORKFLOW_RULES:
        trigger = rule['trigger']
        
        # Check source and event type
        if trigger['source'] != event.source:
            continue
        if trigger['event_type'] != event.event_type:
            continue
        
        # Check conditions (simplified)
        conditions = trigger.get('conditions', {})
        
        # For emails, check keywords
        if 'has_keyword' in conditions and event.source == 'gmail':
            keywords = conditions['has_keyword']
            subject = event.data.get('subject', '').lower()
            body = event.data.get('body', '').lower()
            
            if any(kw.lower() in subject or kw.lower() in body for kw in keywords):
                matched_rules.append(rule)
        else:
            # No specific conditions, just match
            matched_rules.append(rule)
    
    return matched_rules


async def execute_workflow(rule: Dict, event_data: Dict, background_tasks: BackgroundTasks):
    """Execute workflow actions."""
    print(f"\n🚀 Executing workflow: {rule['name']}")
    
    results = {}
    
    for action_name in rule['actions']:
        if action_name in ACTION_HANDLERS:
            print(f"   → Running action: {action_name}")
            
            handler = ACTION_HANDLERS[action_name]
            result = await handler(event_data)
            results[action_name] = result
    
    # Log to Notion if configured
    if notion and NOTION_WORKFLOWS_DB:
        await log_workflow_execution(rule['name'], event_data, results)
    
    print(f"✅ Workflow complete: {rule['name']}")
    return results


async def log_workflow_execution(workflow_name: str, event_data: Dict, results: Dict):
    """Log workflow execution to Notion."""
    try:
        properties = {
            "Workflow": {
                "title": [{"text": {"content": workflow_name}}]
            },
            "Timestamp": {
                "date": {"start": datetime.now().isoformat()}
            },
            "Status": {
                "select": {"name": "Completed"}
            }
        }
        
        # Add event details as page content
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Event Data"}}]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": str(event_data)[:2000]}}],
                    "language": "json"
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Results"}}]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": str(results)[:2000]}}],
                    "language": "json"
                }
            }
        ]
        
        notion.pages.create(
            parent={"database_id": NOTION_WORKFLOWS_DB},
            properties=properties,
            children=children
        )
        
        print(f"   📝 Logged to Notion")
    
    except Exception as e:
        print(f"⚠️  Failed to log to Notion: {e}")


# ──────────────────────────────────────────────────────────────
# API ENDPOINTS
# ──────────────────────────────────────────────────────────────

@app.post("/webhook/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Gmail webhook events."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Create workflow event
    event = WorkflowEvent(
        source="gmail",
        event_type="new_email",
        data=payload
    )
    
    # Match rules
    matched_rules = await match_workflow_rules(event)
    
    if matched_rules:
        print(f"📬 Gmail event matched {len(matched_rules)} rules")
        
        # Execute workflows in background
        for rule in matched_rules:
            background_tasks.add_task(execute_workflow, rule, event.data, background_tasks)
    
    return {"status": "accepted", "matched_rules": len(matched_rules)}


@app.post("/webhook/drive")
async def drive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Google Drive webhook events."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event = WorkflowEvent(
        source="drive",
        event_type="file_shared",
        data=payload
    )
    
    matched_rules = await match_workflow_rules(event)
    
    if matched_rules:
        print(f"📁 Drive event matched {len(matched_rules)} rules")
        for rule in matched_rules:
            background_tasks.add_task(execute_workflow, rule, event.data, background_tasks)
    
    return {"status": "accepted", "matched_rules": len(matched_rules)}


@app.post("/webhook/calendar")
async def calendar_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Google Calendar webhook events."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    event = WorkflowEvent(
        source="calendar",
        event_type="event_starting_soon",
        data=payload
    )
    
    matched_rules = await match_workflow_rules(event)
    
    if matched_rules:
        print(f"📅 Calendar event matched {len(matched_rules)} rules")
        for rule in matched_rules:
            background_tasks.add_task(execute_workflow, rule, event.data, background_tasks)
    
    return {"status": "accepted", "matched_rules": len(matched_rules)}


@app.post("/trigger-manual")
async def trigger_manual_workflow(
    action: str,
    event_data: Dict,
    background_tasks: BackgroundTasks
):
    """Manually trigger a workflow action."""
    
    if action not in ACTION_HANDLERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action: {action}. Available: {list(ACTION_HANDLERS.keys())}"
        )
    
    # Execute action
    handler = ACTION_HANDLERS[action]
    result = await handler(event_data)
    
    return {
        "status": "completed",
        "action": action,
        "result": result
    }


@app.get("/workflows")
async def list_workflows():
    """List all configured workflows."""
    return {
        "workflows": WORKFLOW_RULES,
        "available_actions": list(ACTION_HANDLERS.keys())
    }


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "service": "Dav1d Workflow Automation",
        "workflows_active": len(WORKFLOW_RULES),
        "actions_available": len(ACTION_HANDLERS),
        "notion_logging": bool(notion and NOTION_WORKFLOWS_DB)
    }


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Dav1d Workflow Automation Server...")
    print(f"📊 Project: {PROJECT_ID}")
    print(f"📍 Location: {LOCATION}")
    print(f"🔧 Active workflows: {len(WORKFLOW_RULES)}")
    print(f"⚡ Available actions: {list(ACTION_HANDLERS.keys())}")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=3001)
