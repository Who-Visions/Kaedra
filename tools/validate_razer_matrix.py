
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

from kaedra.services.razer import RazerService
from kaedra.story.ui import log

print("[-] Initializing RazerService...")
razer = RazerService()

if razer.connect():
    print("✅ Connected to Razer Synapse.")
    print("[-] URI:", razer.uri)
    
    print("\n🔥 STARTING MATRIX FIRE EFFECT (5 SECONDS) 🔥")
    print("Look at your keyboard. You should see moving sparks.")
    
    razer.start_fire_effect()
    
    try:
        for i in range(5):
            print(f"Running... {5-i}")
            time.sleep(1)
    finally:
        print("[-] Stopping effect...")
        razer.stop_effect()
        razer.close()
        print("✅ Done.")

else:
    print("❌ Could not connect to Razer.")
