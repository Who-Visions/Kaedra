"""
Kaedra x Rhea Collaboration Test
Validates 2-agent story generation and Notion output.
"""
import os
import sys
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.getcwd())
from kaedra.story.components.co_writer import CoWriter

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# --- STORY PREMISE ---
PREMISE = """
TITLE: "Stitch & Slay"
GENRE: Drama / Slice-of-Life / Social Commentary
SETTING: Northeast America, 2026

PROTAGONIST:
Name: Jada "JadaCraft" Monroe
Age: 27
Location: Philly / NYC cosplay circuit
Background: Self-taught seamstress, rising cosplay star known for:
    - Master-level craftsmanship (armor, LEDs, prosthetics)
    - Her unapologetic body: voluptuous, curvy—features celebrated in Black culture but often fetishized or ignored in mainstream cosplay
    - Viral moments for both her talent AND her figure (double-edged sword)

THEMES:
1. Racism in the cosplay community (gatekeeping, colorism, fetishization)
2. Body positivity vs. objectification (the line between owning your sexuality and being reduced to it)
3. AI anxiety (2026: AI art is stealing commissions, AI costumes are emerging)
4. The hustle: Patreon, OF-adjacent content?, sponsorships, conventions
5. Love: Dating while famous, Black, and "too much" for some

CORE TENSION:
Jada is offered a major sponsorship deal from a tech company pushing AI-assisted costume fabrication.
Does she take the bag and become the face of something that might kill her craft?
Or does she stay indie and risk being left behind?
"""

def get_kaedra_beat(premise: str) -> str:
    """Simulate Kaedra's tactical story structure."""
    # In a full integration, this would call StoryEngine.generate()
    # For now, we use the CoWriter with a "Kaedra voice" prompt
    cw = CoWriter()
    prompt = f"""
    You are KAEDRA, the Shadow Tactician. Your task is to outline the FIRST SCENE of this story.
    Be tactical. Be precise. Structure the beat: WHO, WHERE, WHAT, TENSION.
    
    PREMISE:
    {premise}
    
    Output a scene outline (not full prose). Focus on:
    - Opening image
    - Character introduction
    - Inciting tension (first hint of conflict)
    """
    return cw.consult(prompt)

def get_rhea_dialogue(scene_outline: str, premise: str) -> str:
    """Rhea adds voice and dialogue."""
    cw = CoWriter()
    prompt = f"""
    You are RHEA NOIR, the Vibe Specialist and Kaedra's assistant.
    Kaedra has provided a scene outline. Your job is to ADD DIALOGUE and INTERNAL MONOLOGUE.
    Make Jada REAL. Give her voice—AAVE, Philly slang, the way a Black woman talks to herself while grinding.
    
    PREMISE:
    {premise}
    
    KAEDRA'S SCENE OUTLINE:
    {scene_outline}
    
    Write the scene with dialogue. Make it pop. 2-3 pages max.
    """
    return cw.consult(prompt)

def write_to_notion(title: str, content: str):
    """Create a new page in Notion with the story content."""
    if not NOTION_TOKEN:
        print("[!] No NOTION_TOKEN, skipping write.")
        return None
    
    client = Client(auth=NOTION_TOKEN)
    
    # Find a parent page to put this under (use search for "Scripts" or create top-level)
    # For simplicity, we'll create under a known parent or as a top-level page in a database
    # Let's search for a "Scripts" or "Stories" database/page
    
    # Fallback: Create as a child of the first page we can find
    search_res = client.search(query="Story").get("results", [])
    parent_id = None
    for r in search_res:
        if r.get("object") == "page":
            parent_id = r.get("id")
            break
    
    if not parent_id:
        print("[!] No parent page found, searching for any page...")
        all_pages = client.search().get("results", [])
        for p in all_pages:
            if p.get("object") == "page":
                parent_id = p.get("id")
                break
    
    if not parent_id:
        print("[!] Cannot find any parent page. Aborting Notion write.")
        return None
    
    # Create the page
    new_page = client.pages.create(
        parent={"page_id": parent_id},
        properties={
            "title": [{"text": {"content": title}}]
        },
        children=[
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "Stitch & Slay - Scene 1"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": content[:2000]}}]}  # Notion block limit
            }
        ]
    )
    
    return new_page.get("url")

def main():
    print("=" * 50)
    print("🎬 KAEDRA x RHEA COLLABORATION TEST")
    print("=" * 50)
    
    # Step 1: Kaedra outlines
    print("\n[1/3] KAEDRA (Shadow Tactician) - Structuring Scene...")
    kaedra_beat = get_kaedra_beat(PREMISE)
    print("-" * 40)
    print(kaedra_beat[:500] + "..." if len(kaedra_beat) > 500 else kaedra_beat)
    print("-" * 40)
    
    # Step 2: Rhea adds dialogue
    print("\n[2/3] RHEA NOIR (Vibe Specialist) - Adding Dialogue...")
    rhea_scene = get_rhea_dialogue(kaedra_beat, PREMISE)
    print("-" * 40)
    print(rhea_scene[:1000] + "..." if len(rhea_scene) > 1000 else rhea_scene)
    print("-" * 40)
    
    # Step 3: Write to Notion
    print("\n[3/3] Writing to Notion...")
    combined = f"=== KAEDRA'S OUTLINE ===\n{kaedra_beat}\n\n=== RHEA'S SCENE ===\n{rhea_scene}"
    url = write_to_notion("Stitch & Slay - Scene 1 (Collab Test)", combined)
    
    if url:
        print(f"✅ SUCCESS! Notion Page: {url}")
    else:
        print("⚠️ Notion write skipped or failed.")
    
    print("\n" + "=" * 50)
    print("🏁 COLLABORATION TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    main()
