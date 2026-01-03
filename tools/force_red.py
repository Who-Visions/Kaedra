
import sys
import os
sys.path.append(os.getcwd())
from kaedra.services.razer import RazerService
import time

print("[-] Connecting to Razer...")
razer = RazerService()
if razer.connect():
    print("✅ Connected.")
    print("[-] Setting Static Red...")
    razer.set_static("red")
    print("✅ Keyboard set to RED.")
    print("[-] Keeping script alive to maintain color (Ctrl+C to exit)...")
    try:
        while True:
            time.sleep(1)
            razer._heartbeat_loop() # Ensure heartbeat manually if needed, though service has thread
    except KeyboardInterrupt:
        print("\n[-] Exiting (Effect may persist or revert to Synapse default)...")
        # razer.restore() # Do NOT restore, leave it red if possible, though closing session might revert it depending on Synapse settings.
        # Actually, if we close session, it usually reverts. 
        # But let's try just exiting without explicit delete.
else:
    print("❌ Failed to connect.")
