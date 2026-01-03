
import sys
import os
import time
import requests
import json

# Add project root to path
sys.path.append(os.getcwd())

from kaedra.services.razer import RazerService

print("════ RAZER DIAGNOSTICS ════")

razer = RazerService()
print("1. Attempting Handshake...")
try:
    if razer.connect():
        print(f"✅ CONNECTION SUCCESSFUL")
        print(f"   URI: {razer.uri}")
        
        print("\n2. Testing Control (Looping RGB)")
        print("   If you see 'Result: 0' but NO lights change, check Synapse > Connect > Apps.")
        
        colors = [
            ("Red", 0x0000FF),
            ("Green", 0x00FF00),
            ("Blue", 0xFF0000)
        ]
        
        for name, color in colors:
            print(f"   -> Setting {name}...", end=" ")
            payload = {"effect": "CHROMA_STATIC", "param": {"color": color}}
            resp = razer._send("keyboard", json_data=payload)
            print(f"API Response: {resp}")
            time.sleep(1)
            
        print("\n3. Testing Matrix Custom (Fire Spark)")
        grid = [[0x0000FF for _ in range(22)] for _ in range(6)] # All Red background
        payload = {
            "effect": "CHROMA_CUSTOM2", 
            "param": {
                "color": grid,
                "key": [[0]*22]*6
            }
        }
        resp = razer._send("keyboard", json_data=payload)
        print(f"   -> Custom Grid Sent. Response: {resp}")
        
        time.sleep(2)
        razer.close()
        print("\n✅ Diagnostics Complete.")
        
    else:
        print("❌ CONNECTION FAILED")
        print("   Is Razer Synapse running?")
        print("   Is the REST API enabled?")

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
