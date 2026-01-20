"""
FULL SCREENPLAY GENERATOR (v2 - LIVE SYNC)
Stitch & Slay - A Feature Film

Target: 90-120 pages (~20,000-30,000 words)
Method: Two-pass generation with Kaedra (structure) + Rhea (dialogue)
Features: Scene continuity, checkpointing, robust LIVE Notion writing
"""
import os
import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv
from notion_client import Client

sys.path.append(os.getcwd())
from kaedra.story.components.co_writer import CoWriter

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID", "2ed1da33ec0981fbb5b2d79108b3f413").strip()

# Checkpoint file for resume capability
CHECKPOINT_FILE = Path("screenplay_checkpoint.json")

# === STORY BIBLE ===
STORY_BIBLE = """
TITLE: "STITCH & SLAY"
GENRE: Drama / Social Commentary / Romance
LOGLINE: A rising Black cosplayer must choose between a lucrative AI sponsorship that could destroy her craft—and the indie authenticity that made her a star.

SETTING: Philadelphia & NYC, 2026

PROTAGONIST:
- Name: Jada "JadaCraft" Monroe
- Age: 27
- Heritage: Black American (Philly roots)
- Look: Voluptuous, curvy, unapologetically thick. Dark skin, dreadlocks.
- Skills: Master-level seamstress, armor fabrication, LED work, prosthetics. 
- Voice: AAVE, Philly slang, direct, funny, vulnerable.

SUPPORTING CAST:
1. MARCUS "MarcFab" JOHNSON (30) - Fellow Black cosplayer, older head, mentor figure. 
2. ELENA VANCE ( white cosplay influencer) - White cosplay influencer, performative ally.
3. DEVON COLE (28) - TechCorp rep. Smooth talker.
4. TITI (65) - Jada's grandmother. Voice of wisdom.

ACTUAL STRUCTURE (26 scenes) - See SCENE_LIST.
"""

# === SCENE BREAKDOWN ===
SCENE_LIST = [
    ("INT. JADA'S WORKSHOP - NIGHT", "Jada finishes her masterpiece armor, alone. We see her skill, her grind, her body, her world."),
    ("INT. JADA'S WORKSHOP - NIGHT (CONT'D)", "The TechCorp email arrives. Jada reads it, conflicted. She calls Marcus."),
    ("INT. MARCUS'S APARTMENT - NIGHT", "Phone call with Marcus. He warns her about selling out. Hints at their history."),
    ("INT. TITI'S HOUSE - DAY", "Jada visits Titi. Grandmother wisdom about values, roots, and not forgetting who you are."),
    ("EXT. PHILADELPHIA CONVENTION CENTER - DAY", "Jada arrives at PhillyCon. The energy, the crowds, the cosplayers."),
    ("INT. CONVENTION FLOOR - DAY", "A gatekeeper questions Jada's craft. She handles it with grace."),
    ("INT. CONVENTION FLOOR - LATER", "Elena appears, performative ally. Subtle shade."),
    ("INT. CONVENTION PANEL ROOM - DAY", "Jada on a panel. A fan asks about AI. Her answer goes viral."),
    ("INT. UPSCALE RESTAURANT - NIGHT", "First meeting with Devon (TechCorp). Real temptation."),
    ("MONTAGE: JADA'S RISE", "Photoshoots, brand deals. Money vs Loneliness."),
    ("INT. JADA'S WORKSHOP - DAY", "Jada working with TechCorp AI assist. Feels weird."),
    ("INT. COFFEE SHOP - DAY", "Marcus confronts Jada. Tension. Unspoken feelings."),
    ("INT. CONVENTION FLOOR - NYC CON - DAY", "Jada sees an AI copy of her design. Shock."),
    ("INT. TECHCORP OFFICE - DAY", "Jada confronts Devon. Gaslighting. 'It's just inspiration.'"),
    ("EXT. NYC STREET - NIGHT", "Jada walks alone. Feels isolated."),
    ("INT. JADA'S APARTMENT - NIGHT", "Elena 'exposes' Jada. Community turns on her."),
    ("INT. TITI'S HOSPITAL ROOM - DAY", "Titi is sick. Reminds Jada what matters."),
    ("INT. JADA'S WORKSHOP - NIGHT", "All is lost. Jada cries over old photos."),
    ("INT. JADA'S WORKSHOP - DAWN", "Resolve. New handmade design starts."),
    ("INT. COMMUNITY CENTER - DAY", "Jada plans 'Handmade Showcase'."),
    ("INT. PHONECALL / SPLIT SCREEN", "Marcus calls. They reconnect."),
    ("INT. NYC CONVENTION CENTER - MAIN HALL - DAY", "The Showcase. Elena planning sabotage."),
    ("INT. BACKSTAGE - DAY", "Elena caught trying to cut power. Confrontation."),
    ("INT. MAIN STAGE - DAY", "Jada takes stage. Speech on authenticity."),
    ("INT. MAIN STAGE - DAY (CONT'D)", "Crowd roars. Marcus and Titi proud."),
    ("EXT. NYC CONVENTION CENTER - NIGHT", "Jada and Marcus walk out together. Hopeful ending."),
]

class ContinuityTracker:
    def __init__(self):
        self.threads = []
        self.props = []
        self.emotional_state = "focused, tired but determined"
        self.last_location = ""

    def update(self, text: str, header: str):
        self.last_location = header
        if "armor" in text.lower() and "armor" not in self.props:
            self.props.append("Jada's armor")
        if "techcorp" in text.lower() and "TechCorp offer" not in self.threads:
            self.threads.append("TechCorp offer")

    def get_context(self) -> str:
        return f"\nCONTINUITY:\n- Location: {self.last_location}\n- Props: {', '.join(self.props[-3:])}\n- Threads: {', '.join(self.threads[-3:])}\n- Mood: {self.emotional_state}"

# === NOTION SYNC ===
def get_notion_client():
    if not NOTION_TOKEN: return None
    return Client(auth=NOTION_TOKEN)

def ensure_screenplay_page(client: Client, title: str, existing_id: Optional[str] = None) -> str:
    if existing_id:
        try:
            p = client.pages.retrieve(existing_id)
            return p["id"]
        except: pass

    parent_id = NOTION_PARENT_PAGE_ID
    new_page = client.pages.create(
        parent={"page_id": parent_id},
        properties={"title": {"title": [{"text": {"content": title}}]}},
        children=[
            {"object": "block", "type": "heading_1", "heading_1": {"rich_text": [{"text": {"content": title}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Written by Kaedra + Rhea Noir"}}]}},
            {"object": "block", "type": "divider", "divider": {}},
        ]
    )
    print(f"✨ Created Notion Page: {new_page['url']}")
    return new_page["id"]

def append_scene_to_notion(client: Client, page_id: str, scene_num: int, header: str, content: str):
    blocks = [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": f"SCENE {scene_num}: {header}"}}]}},
    ]
    parts = [p.strip() for p in content.split("\n\n") if p.strip()]
    for p in parts:
        safe = p[:1800]
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": safe}}]}})
    
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    
    # 80 blocks batch limit
    for i in range(0, len(blocks), 80):
        client.blocks.children.append(block_id=page_id, children=blocks[i:i+80])

# === CORE LOOP ===
def save_checkpoint(index: int, scenes: list, continuity: ContinuityTracker, page_id: str):
    data = {
        "scene_index": index,
        "scenes": scenes,
        "notion_page_id": page_id,
        "continuity": {
            "threads": continuity.threads,
            "props": continuity.props,
            "emotional_state": continuity.emotional_state,
            "last_location": continuity.last_location
        }
    }
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_checkpoint():
    if not CHECKPOINT_FILE.exists(): return 0, [], ContinuityTracker(), None
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    c = ContinuityTracker()
    c.threads = data["continuity"]["threads"]
    c.props = data["continuity"]["props"]
    c.emotional_state = data["continuity"].get("emotional_state", "determined")
    c.last_location = data["continuity"].get("last_location", "")
    return data["scene_index"], data["scenes"], c, data.get("notion_page_id")

def main():
    cw = CoWriter()
    notion = get_notion_client()
    
    start_idx, all_scenes, continuity, page_id = load_checkpoint()
    
    if notion:
        page_id = ensure_screenplay_page(notion, "STITCH & SLAY (Live Script)", page_id)
        # Update checkpoint with page_id immediately
        save_checkpoint(start_idx, all_scenes, continuity, page_id)
        # Link for user
        page_info = notion.pages.retrieve(page_id)
        print(f"🔗 LIVE NOTION LINK: {page_info.get('url')}")
    else:
        print("⚠️ No Notion token found. Continuing locally.")

    for i in range(start_idx, len(SCENE_LIST)):
        header, desc = SCENE_LIST[i]
        print(f"\n🎬 [SCENE {i+1}/{len(SCENE_LIST)}] {header}")
        
        prev_sum = all_scenes[-1][:500] if all_scenes else ""
        
        # Pass 1: Kaedra
        print("  [1/2] Kaedra structure...")
        structure = cw.consult(f"Structure this scene: {header}\n{desc}\n{continuity.get_context()}\nPrev summary: {prev_sum}")
        
        # Pass 2: Rhea
        print("  [2/2] Rhea dialogue...")
        scene_text = cw.consult(f"Write the full scene based on this structure:\n{structure}\n{continuity.get_context()}")
        
        # Save
        continuity.update(scene_text, header)
        all_scenes.append(f"{header}\n\n{scene_text}")
        
        if notion:
            print("  🔼 Syncing to Notion...")
            append_scene_to_notion(notion, page_id, i+1, header, scene_text)
            
        save_checkpoint(i+1, all_scenes, continuity, page_id)
        print(f"  ✅ Complete. {len(scene_text.split())} words.")

if __name__ == "__main__":
    main()
