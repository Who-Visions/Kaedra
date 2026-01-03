
import sys
import os
import time

sys.path.append(os.getcwd())

from kaedra.services.razer import RazerService

print("════════════════════════════════════════════════════════════")
print("   KAEDRA RAZER CONNECTION - PERSISTENT MODE")
print("════════════════════════════════════════════════════════════")
print()
print("This script will STAY CONNECTED so you can enable the app")
print("in Razer Synapse > Chroma Apps.")
print()
print("Press Ctrl+C when you're done.")
print()
print("════════════════════════════════════════════════════════════")
print()

razer = RazerService()
print("[1] Connecting to Razer Synapse...")

if razer.connect():
    print(f"✅ CONNECTED: {razer.uri}")
    print()
    print(">>> NOW GO TO: Razer Chroma > CHROMA APPS tab")
    print(">>> Look for 'Kaedra Story Engine' and TOGGLE IT ON")
    print()
    print("Keeping connection alive... (Ctrl+C to exit)")
    print()
    
    try:
        seconds = 0
        while True:
            time.sleep(5)
            seconds += 5
            print(f"  ... still connected ({seconds}s) - go enable the app!")
    except KeyboardInterrupt:
        print()
        print("[X] Exiting...")
        razer.close()
        print("✅ Disconnected cleanly.")
else:
    print("❌ Failed to connect to Razer Synapse.")
    print("   Make sure Synapse is running.")
