import sys
import os
sys.path.insert(0, os.getcwd())
print("[1] Start", flush=True)
import sounddevice
print("[2] Imported sounddevice", flush=True)

try:
    print("[3] Importing kaedra.story.engine...", flush=True)
    from kaedra.story.engine import StoryEngine
    print("[4] Imported StoryEngine", flush=True)
except Exception as e:
    print(f"[ERROR] Import failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[5] Initializing StoryEngine...", flush=True)
try:
    # Hack to avoid full Vertex AI auth check if that is hanging?
    # No, user wants live code.
    engine = StoryEngine()
    print("[6] Engine Initialized!", flush=True)
    
    if engine.audio_reactor:
        print(f"[7] AudioReactor Active: {engine.audio_reactor.device_index}", flush=True)
    else:
        print("[7] AudioReactor None", flush=True)
        
    print("[8] Checking Lights...", flush=True)
    if engine.lights.razer:
         print(f"[9] Razer Service URI: {engine.lights.razer.uri}", flush=True)
         
except Exception as e:
    print(f"[ERROR] Engine init failed: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("[10] Done", flush=True)
