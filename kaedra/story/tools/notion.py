"""
StoryEngine Notion Tools
Read and write to Notion pages.
"""
from kaedra.services.notion import NotionService
from ..ui import console


def read_page_content(page_identifier: str) -> str:
    """Read Notion page content. Accepts Title, URL, or ID."""
    console.print(f"[dim]>> [NOTION] Accessing: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.read_page_content(page_identifier)
    except Exception as e:
        return f"[Error reading page: {e}]"


def list_universe_pages() -> str:
    """List all available pages in the Cinematic Universe."""
    console.print("[dim]>> [NOTION] Scanning index...[/]")
    try:
        notion = NotionService()
        pages = notion.list_subpages()
        return ", ".join(pages) if pages else "No pages found."
    except Exception as e:
        return f"[Error listing pages: {e}]"


def update_page_content(page_identifier: str, text: str) -> str:
    """Append text to a Notion page. Requires user confirmation."""
    console.print(f"[dim]>> [NOTION] Preparing write to: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.append_to_page(page_identifier, text)
    except Exception as e:
        return f"[Error writing: {e}]"
