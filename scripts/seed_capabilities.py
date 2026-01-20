import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from kaedra.services.loredb import LoreDB


def seed_capabilities():
    """
    Seed Kaedra's LoreDB with her own capabilities (Self-Knowledge).
    This ensures she knows what tools and services she has access to.
    """
    print("[*] Connecting to LoreDB...")
    world_path = Path("data/world")
    lore = LoreDB(world_path)

    # Capability Definitions
    capabilities = [
        {
            "title": "Kaedra (Self)",
            "type": "character",
            "content": "I am Kaedra, the Shadow Tactician of the Who Visions Fleet. Built by Deepmind/Gemini, I serve as the central watchtower and autonomous orchestrator. My purpose is to manage operations, generate content, and maintain system integrity.",
            "attrs": {"role": "Agent", "model": "Gemini 1.5 Pro", "status": "Online"}
        },
        {
            "title": "Orchestrator",
            "type": "system",
            "content": "The Orchestrator is my autonomous control plane. It allows me to execute long-running tasks via 'Runs' (Ralph-style loops). It manages state, retry logic, and Slack notifications for task completion.",
            "attrs": {"component": "Control", "status": "Active"}
        },
        {
            "title": "Visual Service",
            "type": "system",
            "content": "My visual cortex. Powered by Vertex AI (Imagen 3) and Veo 3.1, it enables me to generate high-fidelity images and videos on demand. Accessible via `/generate-image` and `/generate/video`.",
            "attrs": {"component": "Vision", "provider": "Vertex AI"}
        },
        {
            "title": "Text-to-Speech (TTS)",
            "type": "system",
            "content": "My voice interface. I use advanced TTS models (ElevenLabs/Gemini) to speak responses when running locally on compatible hardware.",
            "attrs": {"component": "Voice", "status": "Enabled"}
        },
        {
            "title": "Slack Bot",
            "type": "system",
            "content": "My remote interface. I listen to channels and direct messages on Slack. I can be summoned via mentions or slash commands to perform tasks remotely.",
            "attrs": {"component": "Connectivity", "platform": "Slack"}
        },
        {
            "title": "Notion Integration",
            "type": "system",
            "content": "My long-term memory extension. I can sync knowledge blocks to and from Notion pages, allowing for collaborative worldbuilding and documentation.",
            "attrs": {"component": "Memory", "platform": "Notion"}
        },
        {
            "title": "Razer Chroma",
            "type": "system",
            "content": "My physical manifestation. I control local hardware lighting (keyboard, mouse, stand) to reflect my internal state (Processing, Idle, Error, Success) via the Razer Chroma SDK.",
            "attrs": {"component": "Hardware", "platform": "Razer"}
        },
        {
            "title": "Wispr Flow",
            "type": "system",
            "content": "My ears. I integrate with Wispr Flow for seamless voice dictation and command processing, allowing for hands-free interaction.",
            "attrs": {"component": "Input", "platform": "Wispr"}
        },
        {
            "title": "Visions Fleet",
            "type": "organization",
            "content": "The collective of AI agents I belong to. Includes Dav1d (Reasoning), Nyx (Security), Raven (Research), and myself (Orchestration). We operate under the 'Who Visions' directive.",
            "attrs": {"role": "Fleet", "members": ["Kaedra", "Dav1d", "Nyx", "Raven"]}
        }
    ]

    print(f"[*] Seeding {len(capabilities)} capabilities...")

    for cap in capabilities:
        # Check if exists by exact name match (safer than FTS)
        results = lore.find_by_attr("name", cap["title"])
        if results:
             print(f"[-] '{cap['title']}' already exists. Skipping.")
             continue

        # Create
        # We store title in attrs['name'] as per LoreDB convention for Characters/Locations
        attrs = cap["attrs"]
        attrs["name"] = cap["title"]
        
        # Mapping 'system' type to 'location' or 'character' if DB enforces types, 
        # but LoreDB seems flexible. Let's try 'system' if schema allows, 
        # otherwise default to 'artifact' or 'location' for systems.
        # Looking at loredb.py, types are strings, so 'system' is fine.
        
        block_id = lore.create_block(
            type=cap["type"],
            content=cap["content"],
            attrs=attrs
        )
        print(f"[+] Created '{cap['title']}' ({block_id})")

    print("[*] Seeding complete.")
    print(f"[*] Database Stats: {lore.stats()}")

if __name__ == "__main__":
    seed_capabilities()
