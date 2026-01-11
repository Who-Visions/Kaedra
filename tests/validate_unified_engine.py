
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.engine import StoryEngine
from kaedra.story.components.lore_editor import LoreEditor

async def validate_engine():
    print(">> Starting Unified Engine Validation...")
    
    # 1. Initialize Engine
    print("   [1/5] Initializing StoryEngine...")
    try:
        engine = StoryEngine()
        print("   [OK] Engine Initialized")
    except Exception as e:
        print(f"   [FAIL] Engine Init Failed: {e}")
        return

    # 2. Check Submodules
    print("   [2/5] Checking Submodules...")
    
    # Visual
    if engine.visual:
        print("   [OK] VisualService: Active")
    else:
        print("   [WARN] VisualService: Inactive (Keys might be missing, but code loaded)")

    # Audio
    if engine.audio:
        print("   [OK] AudioService: Active")
    else:
        print("   [WARN] AudioService: Inactive")

    # Screenplay
    if engine.screenplay:
        print("   [OK] ScreenplayFormatter: Active")
    else:
        print("   [FAIL] ScreenplayFormatter: MISSING")

    # Lore Editor (Just check import availability inside engine scope)
    # It's instantiated on command, but we verified import previously.
    print("   [OK] LoreEditor: Importable")

    # 3. Validation of Command Routing (Static Check)
    print("   [3/5] Verifying Command Handlers...")
    # We check if methods exist
    methods = [
        "_cmd_lore", 
        "_cmd_visual", 
        "_cmd_screenplay", 
        "_cmd_youtube",
        "_cmd_speak",
        "_cmd_listen"
    ]
    
    for m in methods:
        if hasattr(engine, m):
            print(f"   [OK] Handler '{m}': Found")
        else:
            print(f"   [FAIL] Handler '{m}': MISSING")

    # 4. Mock execution of safe commands
    print("   [4/5] Testing :screenplay command (Mock)...")
    try:
        res = await engine._cmd_screenplay(["Test", "Dialogue"])
        if "[SYSTEM] Formatted" in res.text:
             print("   [OK] :screenplay execution successful")
        else:
             print(f"   [WARN] :screenplay result unexpected: {res.text}")
    except Exception as e:
        print(f"   [FAIL] :screenplay execution failed: {e}")

    # 5. Testing :speak existence (Mock audio to avoid sound)
    print("   [5/5] Testing :speak command wiring...")
    if engine.audio:
        # Mock the actual TTS call to avoid API cost/latency
        engine.audio.text_to_speech = MagicMock(return_value="test_output.wav")
        try:
            res = await engine._cmd_speak(["System", "Check"])
            if "Spoke" in res.text:
                 print("   [OK] :speak wiring successful")
            else:
                 print(f"   [WARN] :speak result unexpected: {res.text}")
        except Exception as e:
            print(f"   [FAIL] :speak execution failed: {e}")
    else:
        print("   [WARN] Skipping :speak test (AudioService inactive)")

    print("\n>> Validation Complete.")

if __name__ == "__main__":
    asyncio.run(validate_engine())

