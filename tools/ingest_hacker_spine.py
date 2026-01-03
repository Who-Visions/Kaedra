"""
Ingest Hacker Movie Spine from local README.
Parses markdown tables and pushes to Notion with hashtags for automation.
"""
import re
from pathlib import Path
from kaedra.services.notion import NotionService

def parse_readme(file_path: str):
    content = Path(file_path).read_text(encoding="utf-8")
    
    # Regex for markdown table row
    # | [Title](Link) | Genre | Year | Rating |
    pattern = r"\|\s*\[(.*?)\]\((.*?)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|"
    
    matches = re.findall(pattern, content)
    entries = []
    
    for m in matches:
        title, link, genre_raw, year, rating = m
        
        # Clean data
        genres = [g.strip().lower().replace(" ", "") for g in genre_raw.split("/")]
        tags = ["#hacker", "#reference"] + [f"#{g}" for g in genres]
        tag_str = " ".join(tags)
        
        # Format
        # * **Title** (Year) - #tags - [Link]
        formatted = f"**{title}** ({year.strip()}) - {tag_str} - [IMDb]({link})"
        entries.append(formatted)
        
    return entries

def main():
    readme_path = "temp_hacker_movies/readme.md"
    print(f"Parsing {readme_path}...")
    
    entries = parse_readme(readme_path)
    print(f"Found {len(entries)} movies.")
    
    if not entries:
        print("No entries found. Check regex.")
        return

    print("Initializing Notion Service...")
    notion = NotionService()
    
    page_title = "Hacker Movie Reference Spine"
    print(f"Creating page: '{page_title}'...")
    
    # Create Root Page
    page_id = notion.create_page(page_title)
    if not page_id:
        print("Failed to create page.")
        return
        
    # Batch upload (Notion block limit is 100, checking parser loop)
    # create_page adds a header, we define append_children logic here or loop
    
    print(f"Pushing {len(entries)} entries to Notion (Batching)...")
    
    # Chunking for API safety
    chunk_size = 50
    for i in range(0, len(entries), chunk_size):
        chunk = entries[i:i+chunk_size]
        blocks = []
        for text in chunk:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": text,
                                "link": None
                            }
                        }
                    ]
                }
            })
        
        notion.append_children(page_id, blocks)
        print(f"Pushed batch {i//chunk_size + 1}")

    print("Ingestion Complete.")

if __name__ == "__main__":
    main()
