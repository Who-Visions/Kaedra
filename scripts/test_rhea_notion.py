
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Add root to path for imports
sys.path.append(os.getcwd())
try:
    from kaedra.story.components.co_writer import CoWriter
except ImportError:
    # Fallback if path weirdness
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from kaedra.story.components.co_writer import CoWriter

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = "2ed1da33-ec09-81aa-8c21-facec89f9d00" # Xoah-Lin Oda — Character Hub


def get_page_text(client, page_id):
    """Extract properties and block text."""
    print(f"[-] Reading Notion Page {page_id}...")
    
    # 1. Properties
    text = ["=== PROPERTIES ==="]
    try:
        page = client.pages.retrieve(page_id)
        props = page.get("properties", {})
        for key, val in props.items():
            vtype = val.get("type")
            content = "N/A"
            if vtype == "title":
                content = "".join([t.get("plain_text", "") for t in val.get("title", [])])
            elif vtype == "rich_text":
                 content = "".join([t.get("plain_text", "") for t in val.get("rich_text", [])])
            elif vtype == "select":
                content = val.get("select", {}).get("name") if val.get("select") else "None"
            elif vtype == "multi_select":
                content = ", ".join([x.get("name") for x in val.get("multi_select", [])])
            
            if content and content != "N/A":
                text.append(f"{key}: {content}")
    except Exception as e:
        print(f"[!] Error reading properties: {e}")

    # 2. Blocks
    text.append("\n=== BODY CONTENT ===")
    blocks = client.blocks.children.list(block_id=page_id).get("results", [])
    for b in blocks:
        btype = b.get("type")
        content = b.get(btype, {}).get("rich_text", [])
        plain = "".join([t.get("plain_text", "") for t in content])
        if plain:
            text.append(plain)
            
    return "\n".join(text)

def main():
    if not NOTION_TOKEN:
        print("[!] No NOTION_TOKEN found.")
        return

    client = Client(auth=NOTION_TOKEN)
    
    # 1. Get Text
    content = get_page_text(client, PAGE_ID)
    if not content or len(content) < 50:
        print("[!] Content mostly empty.")
        
    print(f"[-] Extracted {len(content)} chars of lore.")
    print("-" * 20)
    print(content[:1000])
    print("-" * 20)
    
    # 2. Ask Rhea
    print("[-] Consulting Rhea Noir...")
    cowriter = CoWriter()
    
    prompt = f"Here is a character profile from 'The Veil'. Analyze it. Who is this? What is their vibe? Give me a 'Ratchet Scholar' take on Xoah Lin Oda.\n\nPROFILE:\n{content}"
    
    response = cowriter.consult(prompt)
    print("\n🌙 Rhea Noir says (Analysis):")
    print("=" * 40)
    print(response)
    print("=" * 40)
    
    # 3. Turn 2: What would she DO? (High Reasoning)
    print("\n[-] Turn 2: Requesting Action [Gemini 3 Pro High Think]...")
    prompt_2 = f"""
    Context: {response}
    
    SCENARIO: The Veil is destabilizing in Sector 4. Nyx is compromised. 
    Based on your analysis of Xoah (Shadow Courier), what does she DO?
    
    INSTRUCTION: Use HIGH REASONING (Gemini 3 Pro) to determine her tactical and emotional response. 
    Write the beat.
    """
    
    # Pass the previous context explicitly if needed, but consult() is single-turn unless we modify it or Rhea preserves session.
    # We'll pass it in the prompt for now.
    response_2 = cowriter.consult(prompt_2)
    print("\n🌙 Rhea Noir says (Action):")
    print("=" * 40)
    print(response_2)
    print("=" * 40)

if __name__ == "__main__":
    main()

