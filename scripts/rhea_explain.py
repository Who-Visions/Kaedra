
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Add root to path for imports
sys.path.append(os.getcwd())
try:
    from kaedra.story.components.co_writer import CoWriter
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from kaedra.story.components.co_writer import CoWriter

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = "2ed1da33-ec09-81aa-8c21-facec89f9d00" # Xoah-Lin Oda — Character Hub

def get_page_text(client, page_id):
    """(Same extractor as before)"""
    try:
        # Properties
        text = ["=== PROPERTIES ==="]
        page = client.pages.retrieve(page_id)
        props = page.get("properties", {})
        for key, val in props.items():
            vtype = val.get("type")
            content = "N/A"
            if vtype == "title": content = "".join([t.get("plain_text", "") for t in val.get("title", [])])
            elif vtype == "rich_text": content = "".join([t.get("plain_text", "") for t in val.get("rich_text", [])])
            elif vtype == "select": content = val.get("select", {}).get("name") if val.get("select") else "None"
            elif vtype == "multi_select": content = ", ".join([x.get("name") for x in val.get("multi_select", [])])
            if content and content != "N/A": text.append(f"{key}: {content}")
        
        # Blocks
        text.append("\n=== BODY CONTENT ===")
        blocks = client.blocks.children.list(block_id=page_id).get("results", [])
        for b in blocks:
            btype = b.get("type")
            content = b.get(btype, {}).get("rich_text", [])
            plain = "".join([t.get("plain_text", "") for t in content])
            if plain: text.append(plain)
        return "\n".join(text)
    except: return ""

def main():
    client = Client(auth=NOTION_TOKEN)
    content = get_page_text(client, PAGE_ID)
    
    print("[-] Consulting Rhea Noir for Reasoning...")
    cowriter = CoWriter()
    
    # We ask her to explain the specific quote the user noticed
    quote = "She's not saving the world; she's owning her place in it."
    
    prompt = f"""
    CONTEXT:
    {content}
    
    PREVIOUS TAKE:
    "{quote}"
    
    QUESTION:
    Why did you say that? Explain your reasoning based on the lore provided. 
    Break down the connection between "Voidblade Courier", "Convergence", and your conclusion about her autonomy.
    """
    
    response = cowriter.consult(prompt)
    print("\n🌙 Rhea Noir Explains:")
    print("=" * 40)
    print(response)
    print("=" * 40)

if __name__ == "__main__":
    main()
