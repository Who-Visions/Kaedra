
import sys
import os
import time

sys.path.append(os.getcwd())

from kaedra.services.razer import RazerService

print("════ CHROMA LINK VALIDATION ════")

razer = RazerService()
print("1. Connecting to Razer Synapse...")
if razer.connect():
    print(f"✅ Connected: {razer.uri}")
    
    print("\n2. Testing Static Color (Red on all 5 LEDs)...")
    razer.set_chromalink_static("red")
    time.sleep(2)
    
    print("3. Testing Fire Zones (5 LEDs with fire gradient)...")
    razer.set_chromalink_fire()
    time.sleep(2)
    
    print("4. Testing Custom Zones (Rainbow: R, O, Y, G, B)...")
    rainbow = [
        0x0000FF,  # LED 0: Red
        0x00A5FF,  # LED 1: Orange
        0x00FFFF,  # LED 2: Yellow
        0x00FF00,  # LED 3: Green
        0xFF0000,  # LED 4: Blue
    ]
    razer.set_chromalink_zones(rainbow)
    time.sleep(3)
    
    print("5. Closing session...")
    razer.close()
    print("✅ Done. Check your LIFX Chroma Connector connected bulbs.")
    
else:
    print("❌ Failed to connect to Razer Synapse.")
