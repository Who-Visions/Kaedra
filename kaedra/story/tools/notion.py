"""
StoryEngine Notion Tools
Read and write to Notion pages.
"""
from typing import Dict, Optional
from kaedra.services.notion import NotionService
from ..ui import console


def _get_service() -> Optional[NotionService]:
    """Get a NotionService instance."""
    try:
        return NotionService()
    except Exception:
        return None


def index_full_universe(grep_query: str = "") -> str:
    """
    List ALL pages in the Veil Verse integration (50+ pages).
    Optionally filters by title if grep_query is provided.
    Use this to map the entire knowledge base.
    """
    console.print(f"[dim]>> [NOTION] Indexing entire universe (Grep: '{grep_query}')...[/]")
    try:
        notion = NotionService()

        # Paginated fetch of all pages
        all_results = []
        has_more = True
        next_cursor = None

        while has_more:
            resp = notion.client.search(
                filter={"property": "object", "value": "page"},
                start_cursor=next_cursor,
                page_size=100
            )
            results = resp.get("results", [])
            all_results.extend(results)
            has_more = resp.get("has_more", False)
            next_cursor = resp.get("next_cursor")

            if len(all_results) > 200: break # Safety cap

        # Filter and Format
        matches = []
        for p in all_results:
            pid = p["id"]
            props = p.get("properties", {})
            title = "Untitled"

            # Find title property
            for k, v in props.items():
                if v["type"] == "title":
                    title = "".join([t["plain_text"] for t in v.get("title", [])])
                    break

            if not grep_query or grep_query.lower() in title.lower():
                matches.append(f"- {title} (ID: {pid})")

        count = len(matches)
        if not matches:
            return f"No pages found matching '{grep_query}'"

        return f"Universe Index ({count} pages):\n" + "\n".join(matches)

    except Exception as e:
        return f"[Error indexing universe: {e}]"



def read_page_content(page_identifier: str) -> str:
    """Read Notion page content. Accepts Title, URL, or ID."""
    console.print(f"[dim]>> [NOTION] Accessing: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.read_page_content(page_identifier)
    except Exception as e:
        return f"[Error reading page: {e}]"



def list_universe_pages() -> str:
    """List all available pages in the Cinematic Universe (Root DB)."""
    console.print("[dim]>> [NOTION] Scanning VeilVerse Root...[/]")
    try:
        notion = NotionService()
        db_id = "2d90b4b4-0f65-8001-98fe-cbf8a4a2146a"
        url = f"https://api.notion.com/v1/databases/{db_id}/query"

        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # Query Root DB for everything
        with httpx.Client() as client:
            resp = client.post(url, json={"page_size": 20}, headers=headers, timeout=10.0)

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            pages = []
            for r in results:
                props = r.get("properties", {})
                # Extract Name
                title_prop = props.get("Name", {}).get("title", [])
                title = "".join([t["plain_text"] for t in title_prop]) if title_prop else "Untitled"

                # Extract Category
                cat_prop = props.get("Category", {}).get("select", {})
                cat = cat_prop.get("name") if cat_prop else "Uncategorized"

                pages.append(f"- [{cat}] {title} (ID: {r['id']})")

            if pages:
                return "VeilVerse Root Index:\n" + "\n".join(pages)

        # Fallback to broad list if DB fails or is empty
        pages = notion.list_subpages()
        if not pages:
            results = notion.global_search("Lore", limit=5) + notion.global_search("Universe", limit=5)
            pages = [f"[{r['type']}] {r['title']}" for r in results]

        return ", ".join(pages) if pages else "No pages found."
    except Exception as e:
        return f"[Error listing pages: {e}]"



def search_universe(query: str) -> str:
    """
    Search the entire workspace for lore, characters, or locations.
    Use this if list_universe_pages doesn't show what you need.
    """
    console.print(f"[dim]>> [NOTION] Global Search: '{query}'...[/]")
    try:
        notion = NotionService()
        results = notion.global_search(query, limit=10)
        if not results:
            return f"No results found for '{query}' in the workspace."

        lines = [f"- [{r['type']}] {r['title']} (ID: {r['id']})" for r in results]
        return "Notion Global Search Results:\n" + "\n".join(lines)
    except Exception as e:
        return f"[Error searching Notion: {e}]"


def update_page_content(page_identifier: str, text: str) -> str:
    """Append text to a Notion page. Requires user confirmation."""
    console.print(f"[dim]>> [NOTION] Preparing write to: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.append_to_page(page_identifier, text)
    except Exception as e:
        return f"[Error writing: {e}]"


def run_lore_automations() -> str:
    """
    Run Agent-Layer automations on the VeilVerse Universe (Notion).
    Fixes timeline eras, scales character power, and enforces retcon safety.
    """
    from tools.agent_automations import VeilVerseAutomator
    console.print("[dim]>> [NOTION] Running Agent-Layer Automations...[/]")
    try:
        automator = VeilVerseAutomator()
        automator.run_all()
        return "Lore automations completed successfully. Timeline, Power, and Retcons synced."
    except Exception as e:
        return f"[Error running automations: {e}]"
def sync_roadmap_item(title: str, drive_url: str, status: str = "Outline", milestones: str = "") -> str:
    """Sync a roadmap project to the Notion Master Index."""
    console.print(f"[dim]>> [NOTION] Syncing roadmap: '{title}'...[/]")
    try:
        notion = NotionService()
        return notion.sync_roadmap_item(title, drive_url, status, milestones)
    except Exception as e:
        return f"[Error syncing roadmap: {e}]"


def create_lore_page(title: str, content: str, parent_title: str = "Veil Verse") -> str:
    """
    Create a new Lore Page in the Veil Verse.
    Use this to permanently save new characters, locations, or artifacts.
    """
    console.print(f"[dim]>> [NOTION] creating lore: '{title}' in '{parent_title}'...[/]")
    try:
        notion = NotionService()
        # Find parent ID by title
        parent_id = notion.search_page(parent_title)
        if not parent_id:
            return f"Error: Parent page '{parent_title}' not found."

        # Construct content blocks
        blocks = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            }
        ]

        page_id = notion.create_page(title, parent_page_id=parent_id, content_blocks=blocks)
        if page_id:
            return f"Successfully created Page '{title}' (ID: {page_id})"
        return "Failed to create page."
    except Exception as e:
        return f"[Error creating lore: {e}]"


def create_tracker_db(title: str, parent_title: str = "Veil Verse") -> str:
    """Create a new Tracker Database (e.g. 'Quest Log', 'Inventory')."""
    console.print(f"[dim]>> [NOTION] Creating DB: '{title}'...[/]")
    try:
        notion = NotionService()
        parent_id = notion.search_page(parent_title)
        if not parent_id:
            return f"Error: Parent page '{parent_title}' not found."

        schema = {
            "Item": {"title": {}},
            "Status": {"select": {"options": [{"name": "Active", "color": "green"}, {"name": "Done", "color": "blue"}]}},
            "Tags": {"multi_select": {}}
        }

        db_id = notion.create_database(parent_id, title, schema)
        return f"Successfully created Database '{title}' (ID: {db_id})" if db_id else "Failed to create DB."
    except Exception as e:
        return f"[Error creating DB: {e}]"


def add_notion_comment(page_identifier: str, comment_text: str) -> str:
    """Leave a comment on a specific Notion page (by Title or ID)."""
    console.print(f"[dim]>> [NOTION] Commenting on '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        page_id = notion._extract_id(page_identifier) or notion.search_page(page_identifier)
        if not page_id:
            return f"Error: Page '{page_identifier}' not found."

        cid = notion.create_comment(page_id, comment_text)
        return f"Comment added to '{page_identifier}'" if cid else "Failed to comment."
    except Exception as e:
        return f"[Error commenting: {e}]"


def get_notion_users() -> str:
    """List all workspace users."""
    try:
        notion = NotionService()
        users = notion.get_users()
        return "\n".join([f"- {u['name']} ({u['type']})" for u in users])
    except Exception as e:
        return f"[Error listing users: {e}]"



def safe_get_property(props: dict, prop_name: str, prop_type: str) -> any:
    """Null-safe property extraction based on VeilVerse API Contract."""
    prop = props.get(prop_name, {})

    if prop_type == "title":
        arr = prop.get("title", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""

    elif prop_type == "rich_text":
        arr = prop.get("rich_text", [])
        return arr[0].get("text", {}).get("content", "") if arr else ""

    elif prop_type == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None

    elif prop_type == "multi_select":
        arr = prop.get("multi_select", [])
        return [item.get("name") for item in arr if item.get("name")]

    elif prop_type == "status":
        status = prop.get("status")
        return status.get("name") if status else None

    elif prop_type == "number":
        return prop.get("number")

    elif prop_type == "url":
        return prop.get("url")

    elif prop_type == "date":
        date = prop.get("date")
        return date.get("start") if date else None

    return None

def get_character(name: str) -> str:
    """Retrieves full character profile including power levels and species."""
    return _query_entity(name, "Character")



def get_location(name: str) -> str:
    """Retrieves location details, maps, and events."""
    return _query_entity(name, "Location")


def get_event(name: str) -> str:
    """Retrieves historical event or timeline entry."""
    return _query_entity(name, "Event")



def get_entity(name: str) -> str:
    """Retrieves any entity by name, regardless of category (useful for drafts)."""
    return _query_entity(name, category=None)




def create_entity(name: str, category: str, content: str, attribution: str = "StoryEngine", queue_for_scribe: bool = False) -> str:
    """
    Creates a new entity in the Veil Verse Universe DB (Draft Mode).
    Category: Character, Location, Event, Item, Quest, Artifact, Faction, Lore, Technology, Magic System, Species.
    queue_for_scribe: If True, flags for Notion AI review.
    """
    console.print(f"[dim]>> [NOTION] Creating {category}: '{name}'...[/]")
    try:
        notion = NotionService()
        db_id = "2d90b4b4-0f65-8001-98fe-cbf8a4a2146a"

        # Build Page based on Expanded Rulebook Schema
        props = {
            "Name": {"title": [{"text": {"content": name}}]},
            "Category": {"select": {"name": category}},
            "Canon Status": {"select": {"name": "Draft"}},
            "Status": {"status": {"name": "Active"}},
            "Description": {"rich_text": [{"text": {"content": content[:2000]}}]},
        }

        # Category-Specific defaults based on Rulebook
        if category == "Character":
            props["Species/Race"] = {"multi_select": [{"name": "Unknown"}]}
            props["Affiliation"] = {"multi_select": [{"name": "Neutral"}]}
            props["Power Level"] = {"select": {"name": "Standard"}}

        elif category == "Location":
            props["Universe Era"] = {"select": {"name": "Modern Era"}}

        elif category == "Event":
            props["Timeline Year"] = {"number": 2026}
            props["Universe Era"] = {"select": {"name": "Modern Era"}}

        elif category == "Artifact":
            props["Tags"] = {"multi_select": [{"name": "Artifact"}, {"name": "Legendary"}]}

        elif category == "Item":
            props["Tags"] = {"multi_select": [{"name": "Item"}]}

        elif category == "Quest":
            props["Story Arc"] = {"select": {"name": "Standalone"}}
            props["Appears In"] = {"multi_select": [{"name": "Side Stories"}]}

        elif category == "Faction":
            props["Affiliation"] = {"multi_select": [{"name": "Independent"}]}

        elif category == "Lore":
            props["Canon Status"] = {"select": {"name": "Proposed"}}

        elif category == "Species":
            props["Canon Status"] = {"select": {"name": "Proposed"}}
            props["Home World"] = {"rich_text": [{"text": {"content": "Unknown"}}]}

        elif category == "Magic System":
            props["Tags"] = {"multi_select": [{"name": "Magic"}]}

            props["Tags"] = {"multi_select": [{"name": "Veil-Tech"}]}
            props["Production Status"] = {"select": {"name": "Concept"}}

        # Scribe Queue Handling
        if queue_for_scribe:
            # Get existing tags if any (from defaults above)
            existing = props.get("Tags", {}).get("multi_select", [])
            # Add Scribe-Queue
            existing.append({"name": "Scribe-Queue"})
            props["Tags"] = {"multi_select": existing}

            # Add marker block
            children.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "SCRIBE: Expand this entity."}}],
                    "icon": {"emoji": "🤖"},
                    "color": "gray_background"
                }
            })

        new_page = notion.client.pages.create(
            parent={"database_id": db_id},
            properties=props,
            children=children
        )
        return f"Created {category} '{name}' (ID: {new_page['id']})"

    except Exception as e:
        return f"[Error creating entity: {e}]"









def request_scribe_expansion(page_name: str, instructions: str) -> str:
    """
    Flags a page for "Scribe" (Notion AI) expansion.
    1. Tags page with "Scribe-Queue"
    2. Appends [SCRIBE: instructions] block for AI to pick up.
    """
    console.print(f"[dim]>> [NOTION] Flagging '{page_name}' for Scribe...[/]")
    try:
        notion = NotionService()
        page_id = notion.search_page(page_name)
        if not page_id:
            # Try falling back to fuzzy search or get_entity strategy?
            # Let's trust search_page for now.
            return f"Error: Page '{page_name}' not found."

        # 1. Update Tags (append Scribe-Queue)
        # We need to read current tags first to not overwrite them?
        # Ideally yes. But for speed, let's just use a specialized update method if we had one.
        # NotionService doesn't have a specific tag appender exposed easily.
        # Let's try to append the marker first.

        # 2. Append Marker
        marker_text = f"**[SCRIBE: {instructions}]**"

        # We can also set Status to "Unknown" per user request, but Tags are safer for queues.
        # Let's update the page properties to add the tag.

        # Retrieve current tags
        client = notion.client
        curr_page = client.pages.retrieve(page_id)
        curr_props = curr_page.get("properties", {})

        # Handle "Tags" (Multi-select)
        tags_prop = curr_props.get("Tags", {}).get("multi_select", [])
        existing_tags = [t["name"] for t in tags_prop]

        if "Scribe-Queue" not in existing_tags:
            existing_tags.append("Scribe-Queue")

        # Update Page
        client.pages.update(
            page_id=page_id,
            properties={
                "Tags": {"multi_select": [{"name": t} for t in existing_tags]},
                # Optional: Set Status if requested, but let's stick to tags for now.
            }
        )

        # Append Block
        children = [
            {
                "object": "block",
                "type": "callout", # High visibility
                "callout": {
                    "rich_text": [{"text": {"content": f"SCRIBE: {instructions}"}}],
                    "icon": {"emoji": "🤖"},
                    "color": "gray_background"
                }
            }
        ]
        client.blocks.children.append(block_id=page_id, children=children)

        return f" flagged '{page_name}' for Scribe (Tag: Scribe-Queue, Marker Added)."

    except Exception as e:
        return f"[Error flagging for scribe: {e}]"


import httpx
from kaedra.core.config import NOTION_TOKEN



def _query_entity(name: str, category: str = None) -> str:
    """Helper to query the Universal Database by Name + Optional Category."""
    debug_cat = category if category else "Any"
    console.print(f"[dim]>> [NOTION] Querying {debug_cat}: '{name}'...[/]")
    try:
        notion = NotionService()
        db_id = "2d90b4b4-0f65-8001-98fe-cbf8a4a2146a"
        url = f"https://api.notion.com/v1/databases/{db_id}/query"

        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        # Build Filter
        if category:
            filter_obj = {
                "and": [
                    {"property": "Name", "title": {"contains": name}},
                    {"property": "Category", "select": {"equals": category}}
                ]
            }
        else:
            # Use 'equals' for stricter matching on fallback
            filter_obj = {"property": "Name", "title": {"equals": name}}

        body = {"filter": filter_obj}

        # Robust RAW Request
        with httpx.Client() as client:
            resp = client.post(url, json=body, headers=headers, timeout=10.0)

        if resp.status_code != 200:
            return f"[Error {resp.status_code}] querying {debug_cat}: {resp.text}"

        data = resp.json()
        results = data.get("results", [])

        if not results:
            return f"{debug_cat} '{name}' not found."

        # Get best match (first one)
        page_id = results[0]["id"]
        return notion.read_page_content(page_id)

    except Exception as e:
        console.print(f"[red]>> [Exception] {e}[/]")
        return f"[Error querying {debug_cat}: {e}]"






def delete_entity(block_id: str) -> bool:
    """
    Delete (archive) a Notion block or page by ID.
    
    Args:
        block_id: The UUID of the block/page to delete.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    service = _get_service()
    if not service:
        print("[!] Notion Service not available")
        return False
        
    return service.delete_block(block_id)


def create_database_tool(parent_page_id: str, 
                         title: str, 
                         properties: Dict,
                         is_inline: bool = False,
                         description: str = None) -> Optional[str]:
    """
    Create a new database in Notion.
    
    Args:
        parent_page_id: The ID of the parent page.
        title: The title of the new database.
        properties: The schema/properties definition (JSON dict).
        is_inline: Whether the database should be inline.
        description: Optional description for the database.
        
    Returns:
        str: The ID of the created database, or None if failed.
    """
    service = _get_service()
    if not service:
        print("[!] Notion Service not available")
        return None
        
    return service.create_database(parent_page_id, title, properties, is_inline, description)


def update_database_tool(database_id: str, 
                         title: str = None, 
                         properties: Dict = None,
                         description: str = None) -> bool:
    """
    Update an existing Notion database.
    
    Args:
        database_id: The ID of the database to update.
        title: New title (optional).
        properties: New schema/properties (optional).
        description: New description (optional).
        
    Returns:
        bool: True if successful, False otherwise.
    """
    service = _get_service()
    if not service:
        print("[!] Notion Service not available")
        return False
        
    return service.update_database(database_id, title, properties, description)


def retrieve_database_tool(database_id: str) -> Optional[Dict]:
    """
    Retrieve a Notion database object.
    
    Args:
        database_id: The ID of the database to retrieve.
        
    Returns:
        Dict: The database object, or None if failed.
    """
    service = _get_service()
    if not service:
        print("[!] Notion Service not available")
        return None
        
    return service.retrieve_database(database_id)
