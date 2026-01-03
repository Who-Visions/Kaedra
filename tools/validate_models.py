
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from kaedra.story.config import FLASH_MODEL, PRO_MODEL, NARRATIVE_MODEL
    print("✅ Configuration Content Check:")
    print(f"   FLASH_MODEL:     {FLASH_MODEL}")
    print(f"   PRO_MODEL:       {PRO_MODEL}")
    print(f"   NARRATIVE_MODEL: {NARRATIVE_MODEL}")

    expected_flash = "gemini-3-flash-preview"
    
    if FLASH_MODEL != expected_flash:
        print(f"❌ ERROR: FLASH_MODEL should be {expected_flash}, but is {FLASH_MODEL}")
    else:
        print("✅ FLASH_MODEL matches expectation.")

    if NARRATIVE_MODEL != FLASH_MODEL:
        print("❌ ERROR: NARRATIVE_MODEL is not linked to FLASH_MODEL.")
    else:
        print("✅ NARRATIVE_MODEL is correctly linked.")

except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
