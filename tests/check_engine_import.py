
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("Attempting to import StoryEngine...")
    from kaedra.story.engine import StoryEngine
    print("✅ StoryEngine imported successfully.")
except Exception as e:
    print(f"❌ Error importing StoryEngine: {e}")
    import traceback
    traceback.print_exc()
