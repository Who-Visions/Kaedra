"""
Create Agent Registry Database in Notion
Mirrors the local AGENT_REGISTRY.md to Notion with proper database structure.
"""

import httpx
from datetime import datetime

import os
# The Observatory Integration Token
OBSERVATORY_TOKEN = os.getenv("OBSERVATORY_TOKEN")

# Parent page for the database (The Observatory TeamSpace)
PARENT_PAGE_ID = "2e7ca671311e8175882bc791e2f4d488"

headers = {
    "Authorization": f"Bearer {OBSERVATORY_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def create_agent_registry_db():
    """Create the Agent Registry database with proper schema."""
    
    db_payload = {
        "parent": {"page_id": PARENT_PAGE_ID},
        "title": [{"text": {"content": "🤖 Agent Registry"}}],
        "properties": {
            "Agent Name": {"title": {}},
            "Codename": {"rich_text": {}},
            "Platform": {
                "select": {
                    "options": [
                        {"name": "Human", "color": "green"},
                        {"name": "Gemini CLI", "color": "blue"},
                        {"name": "Vertex AI Cloud Run", "color": "purple"},
                        {"name": "Sub-agent", "color": "orange"}
                    ]
                }
            },
            "Role": {"rich_text": {}},
            "Status": {"status": {}},
            "Last Active": {"date": {}},
            "Notes": {"rich_text": {}},
            "API Endpoint": {"url": {}},
            "Hierarchy Level": {
                "number": {"format": "number"}
            }
        }
    }
    
    print("📦 Creating Agent Registry database...")
    response = httpx.post(
        "https://api.notion.com/v1/databases",
        headers=headers,
        json=db_payload,
        timeout=30.0
    )
    
    if response.status_code == 200:
        db_id = response.json()["id"]
        print(f"✅ Database created: {db_id}")
        return db_id
    else:
        print(f"⚠️ Error creating database: {response.status_code}")
        print(response.text[:500])
        return None


def add_agent(db_id: str, agent_data: dict):
    """Add an agent to the registry."""
    
    page_payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Agent Name": {"title": [{"text": {"content": agent_data["name"]}}]},
            "Codename": {"rich_text": [{"text": {"content": agent_data.get("codename", "")}}]},
            "Platform": {"select": {"name": agent_data["platform"]}},
            "Role": {"rich_text": [{"text": {"content": agent_data["role"]}}]},
            "Last Active": {"date": {"start": datetime.now().isoformat()}},
            "Hierarchy Level": {"number": agent_data.get("level", 0)},
            "Notes": {"rich_text": [{"text": {"content": agent_data.get("notes", "")}}]}
        }
    }
    
    # Add API endpoint if provided
    if agent_data.get("api_endpoint"):
        page_payload["properties"]["API Endpoint"] = {"url": agent_data["api_endpoint"]}
    
    response = httpx.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=page_payload,
        timeout=30.0
    )
    
    if response.status_code == 200:
        print(f"  ✅ Added: {agent_data['name']}")
        return response.json()["id"]
    else:
        print(f"  ⚠️ Error adding {agent_data['name']}: {response.text[:200]}")
        return None


def main():
    """Create database and populate with agents."""
    
    # Create the database
    db_id = create_agent_registry_db()
    if not db_id:
        return
    
    # Define agents in hierarchy order
    agents = [
        {
            "name": "Dave",
            "codename": "The Commander",
            "platform": "Human",
            "role": "Final decisions, strategic direction, creative vision",
            "level": 0,
            "status": "Active",
            "notes": "David A. Vega / Dav3 - Who Visions founder"
        },
        {
            "name": "Antigravity",
            "codename": "Desktop Agent",
            "platform": "Gemini CLI",
            "role": "Pair programming, file operations, browser automation",
            "level": 1,
            "status": "Active",
            "notes": "Runs locally via Gemini CLI. Has access to filesystem, terminal, browser."
        },
        {
            "name": "Kaedra",
            "codename": "Shadow Tactician",
            "platform": "Vertex AI Cloud Run",
            "role": "API services, fleet coordination, lore management",
            "level": 2,
            "status": "Active",
            "api_endpoint": "https://kaedra-69017097813.us-central1.run.app",
            "notes": "FastAPI service on Cloud Run. Speaks AAVE, thinks tactically."
        },
        {
            "name": "Blade",
            "codename": "Technical Executor",
            "platform": "Sub-agent",
            "role": "Technical execution, SDLC, builds, deployments",
            "level": 3,
            "status": "Active",
            "notes": "Sub-agent of Kaedra. Handles all technical/code tasks."
        },
        {
            "name": "Nyx",
            "codename": "Creative Director",
            "platform": "Sub-agent",
            "role": "Creative direction, research, lore writing",
            "level": 3,
            "status": "Active",
            "notes": "Sub-agent of Kaedra. Handles creative/research tasks."
        }
    ]
    
    print("\n👥 Adding agents to registry...")
    for agent in agents:
        add_agent(db_id, agent)
    
    print(f"\n✅ Agent Registry complete!")
    print(f"📍 Database ID: {db_id}")
    print(f"🔗 View at: https://notion.so/{db_id.replace('-', '')}")


if __name__ == "__main__":
    main()
