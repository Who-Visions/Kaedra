# Notion Integration for Dav1d
# Ported from HQ_WhoArt notion_webhook with Gemini AI

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from notion_client import Client as NotionClient
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Notion Configuration
NOTION_API_KEY = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")  # Main database to watch

# GCP Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

if not NOTION_API_KEY:
    raise RuntimeError("NOTION_TOKEN not set in .env")

# Initialize clients
notion = NotionClient(auth=NOTION_API_KEY)
gemini_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

app = FastAPI(title="Dav1d Notion Integration")


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def page_title_from_properties(page: dict) -> str:
    """Extract title from Notion page properties."""
    props = page.get("properties", {})
    
    # Try common title properties
    for key in ["Name", "Title", "title", "name"]:
        if key in props:
            prop = props[key]
            if prop.get("type") == "title":
                title_array = prop.get("title", [])
                if title_array:
                    return title_array[0].get("plain_text", "")
    
    return "Untitled"


def fetch_page_blocks(page_id: str) -> List[dict]:
    """Fetch all blocks from a Notion page with pagination."""
    all_blocks = []
    cursor = None
    
    while True:
        resp = notion.blocks.children.list(
            block_id=page_id,
            start_cursor=cursor,
            page_size=100
        )
        all_blocks.extend(resp.get("results", []))
        cursor = resp.get("next_cursor")
        if not cursor:
            break
    
    return all_blocks


def blocks_to_markdown(blocks: List[dict]) -> str:
    """Convert Notion blocks to markdown text."""
    lines = []
    
    for block in blocks:
        block_type = block.get("type")
        
        if block_type == "paragraph":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            if text.strip():
                lines.append(text)
        
        elif block_type == "heading_1":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            lines.append(f"# {text}")
        
        elif block_type == "heading_2":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            lines.append(f"## {text}")
        
        elif block_type == "heading_3":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            lines.append(f"### {text}")
        
        elif block_type == "bulleted_list_item":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            lines.append(f"• {text}")
        
        elif block_type == "numbered_list_item":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            lines.append(f"1. {text}")
        
        elif block_type == "to_do":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            checked = block[block_type].get("checked", False)
            checkbox = "[x]" if checked else "[ ]"
            lines.append(f"{checkbox} {text}")
        
        elif block_type == "code":
            text = rich_text_to_plain(block[block_type].get("rich_text", []))
            language = block[block_type].get("language", "")
            lines.append(f"```{language}\n{text}\n```")
    
    return "\n".join(lines)


def rich_text_to_plain(rich_text_array: List[dict]) -> str:
    """Convert Notion rich text to plain text."""
    return "".join([rt.get("plain_text", "") for rt in rich_text_array])


# ─────────────────────────────────────────────────────────────
# AI ANALYSIS WITH GEMINI
# ─────────────────────────────────────────────────────────────

async def analyze_page_with_gemini(title: str, content: str) -> dict:
    """
    Use Gemini to analyze Notion page content and extract insights.
    
    Returns structured analysis with:
    - summary
    - key_points
    - action_items
    - tags
    - priority
    """
    
    prompt = f"""Analyze this Notion page and provide structured insights.

Page Title: {title}

Content:
{content}

Please provide:
1. A concise summary (2-3 sentences)
2. Key points (3-5 bullet points)
3. Action items (specific tasks to complete)
4. Relevant tags/categories
5. Priority level (low/medium/high/urgent)

Format your response as JSON with these keys:
{{
    "summary": "...",
    "key_points": ["point 1", "point 2", ...],
    "action_items": ["task 1", "task 2", ...],
    "tags": ["tag1", "tag2", ...],
    "priority": "medium"
}}
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
        return analysis
    
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        return {
            "summary": "Analysis unavailable",
            "key_points": [],
            "action_items": [],
            "tags": [],
            "priority": "low"
        }


async def write_analysis_back_to_notion(page_id: str, analysis: dict) -> None:
    """Write AI analysis back to the Notion page as a callout block."""
    
    # Create rich text for the callout
    summary = analysis.get("summary", "")
    key_points = analysis.get("key_points", [])
    action_items = analysis.get("action_items", [])
    priority = analysis.get("priority", "low")
    
    # Build callout content
    callout_text = f"🤖 **Dav1d AI Analysis**\n\n"
    callout_text += f"**Summary:** {summary}\n\n"
    
    if key_points:
        callout_text += "**Key Points:**\n"
        for point in key_points:
            callout_text += f"• {point}\n"
        callout_text += "\n"
    
    if action_items:
        callout_text += "**Action Items:**\n"
        for item in action_items:
            callout_text += f"✓ {item}\n"
        callout_text += "\n"
    
    callout_text += f"**Priority:** {priority.upper()}"
    
    try:
        # Append callout block to page
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": callout_text}
                            }
                        ],
                        "icon": {"emoji": "🧠"},
                        "color": "blue_background"
                    }
                }
            ]
        )
        print(f"✅ Analysis written back to page {page_id[:8]}")
    
    except Exception as e:
        print(f"⚠️  Failed to write analysis: {e}")


# ─────────────────────────────────────────────────────────────
# WEBHOOK PROCESSING
# ─────────────────────────────────────────────────────────────

async def process_notion_page(page_id: str, event_type: str) -> None:
    """
    Background task to process a Notion page:
    1. Fetch page content
    2. Analyze with Gemini
    3. Write insights back to Notion
    """
    
    print(f"🔔 Processing page: {page_id[:8]}... (event: {event_type})")
    
    try:
        # Fetch page
        page = notion.pages.retrieve(page_id=page_id)
        title = page_title_from_properties(page)
        
        # Fetch all blocks
        blocks = fetch_page_blocks(page_id)
        content = blocks_to_markdown(blocks)
        
        print(f"📄 Page: '{title}' | {len(content)} chars | {len(blocks)} blocks")
        
        if not content.strip():
            print("⏭️  Empty page, skipping analysis")
            return
        
        # Analyze with Gemini
        print(f"🧠 Analyzing with Gemini...")
        analysis = await analyze_page_with_gemini(title, content)
        print(f"✅ Analysis complete: {analysis.get('priority')} priority")
        
        # Write back to Notion
        await write_analysis_back_to_notion(page_id, analysis)
        
        print(f"✅ Page processing complete: {page_id[:8]}")
    
    except Exception as e:
        print(f"❌ Error processing page {page_id}: {e}")
        import traceback
        traceback.print_exc()


# ─────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────

@app.post("/notion-webhook")
async def notion_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main Notion webhook endpoint.
    Receives events from Notion and processes them in the background.
    """
    
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle webhook verification
    if "verification_token" in payload:
        return {"status": "received"}
    
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    # Extract event details
    entity = payload.get("entity", {})
    entity_type = entity.get("type")
    event_type = payload.get("type")
    
    # Only process page events
    if entity_type != "page":
        return {"status": "ignored", "reason": "not a page"}
    
    page_id = entity.get("id")
    if not page_id:
        raise HTTPException(status_code=400, detail="Missing page id")
    
    # Process in background
    background_tasks.add_task(
        process_notion_page,
        page_id=page_id,
        event_type=event_type
    )
    
    return {"status": "accepted"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Dav1d Notion Integration",
        "notion_connected": bool(NOTION_API_KEY),
        "gemini_configured": bool(PROJECT_ID)
    }


@app.post("/analyze-page/{page_id}")
async def analyze_page_manual(page_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger analysis for a specific Notion page.
    Useful for testing or re-analyzing existing pages.
    """
    
    background_tasks.add_task(
        process_notion_page,
        page_id=page_id,
        event_type="manual_trigger"
    )
    
    return {
        "status": "accepted",
        "page_id": page_id,
        "message": "Analysis queued"
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Dav1d Notion Integration Server...")
    print(f"📊 Project: {PROJECT_ID}")
    print(f"📍 Location: {LOCATION}")
    print(f"🔗 Notion API: {'✅ Connected' if NOTION_API_KEY else '❌ Not configured'}")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=3000)
