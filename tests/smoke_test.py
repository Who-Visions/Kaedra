import sys
import os
import time
from unittest.mock import MagicMock, patch
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from universe_text import StoryEngine, Mode

# Define the 25-step sequence
STEPS = [
    "We touch down on the red dust of Chryse Planitia.", # 1. Normal: Landing
    "freeze",                                           # 2. Command: Freeze
    "Describe the dust plume suspended in thin air.",   # 3. Freeze: Detail
    "zoom",                                             # 4. Command: Zoom
    "Focus on the landing strut compressing.",          # 5. Zoom: Tech detail
    "escalate",                                         # 6. Command: Escalate
    "A proximity alarm blares! The ground is unstable.",# 7. Escalate: Crisis
    "calm",                                             # 8. Command: Calm
    "Stabilize the ship using thrusters.",              # 9. Normal: Resolution
    "pov Commander Lewis",                              # 10. Command: POV
    "How does the red horizon make me feel?",           # 11. POV: Interiority
    "next",                                             # 12. Command: Next Scene (EVA)
    "Suiting up for the first walk.",                   # 13. Normal
    "god",                                              # 14. Command: God Mode
    "What is the atmospheric composition here?",        # 15. God: Lore/Science
    "normal",                                           # 16. Resume
    "Stepping onto the ladder.",                        # 17. Normal
    "debug",                                            # 18. Command: Debug
    "tree",                                             # 19. Command: Tree
    "rewind",                                           # 20. Command: Rewind
    "Check the O2 levels before stepping out.",         # 21. Normal (Alt path)
    "Read the page 'Mars Mission Protocols'",           # 22. Notion Read
    "Write 'First Footprint' to page 'Sol 1 Log'",      # 23. Notion Write
    "tree",                                             # 24. Command: Tree
    "coherence",                                        # 25. Command: Coherence (New)
    "exit"                                              # 26. Exit
]

CONFIRM_RESPONSES = [True] * 5 # Always say yes to confirmations

async def run_smoke_test():
    print("🚀 STARTING 25-STEP SMOKE TEST")
    
    # Mock External Services to avoid side effects & API costs (optional, but safer for smoke)
    # We WILL use real Gemini if possible, or Mock it if we want pure logic test.
    # Let's use REAL Gemini to verifying "functions work", but MOCK Notion/LIFX.
    
    with patch('universe_text.LIFXService') as MockLIFX, \
         patch('universe_text.NotionService') as MockNotion, \
         patch('rich.prompt.Prompt.ask', side_effect=STEPS) as MockAsk, \
         patch('rich.prompt.Confirm.ask', side_effect=CONFIRM_RESPONSES) as MockConfirm:
        
        # Setup Mocks
        mock_lifx = MockLIFX.return_value
        mock_lifx.list_lights.return_value = [] # Empty list for init
        
        mock_notion = MockNotion.return_value
        mock_notion.read_page_content.return_value = "Content of Galactic Codex..."
        mock_notion.append_to_page.return_value = "Success"
        mock_notion.list_subpages.return_value = ["Page A", "Page B", "Galactic Codex"]

        # Initialize Engine
        engine = StoryEngine()
        
        # Run
        print(f"Loaded {len(STEPS)} steps.")
        await engine.run()
        
    print("✅ SMOKE TEST COMPLETE")

if __name__ == "__main__":
    try:
        asyncio.run(run_smoke_test())
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
