from kaedra.services.razer import RazerService
import time
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_wave():
    print("Initializing Razer Service...")
    razer = RazerService()
    
    if not razer.connect():
        print("❌ Could not connect to Razer Synapse.")
        return

    print("✅ Connected. URI:", razer.uri)
    
    print("\n🌊 Starting WAVE effect (Green)...")
    print("Watch the Laptop Stand. It SHOULD pulse/wave in GREEN now.")
    print("Running for 10 seconds...")
    
    # Run the wave
    razer.start_wave_effect(color_name="green", period=2.0)
    
    try:
        for i in range(10):
            print(f"Tick {i+1}/10...")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping effect...")
        razer.close()
        print("Done.")

if __name__ == "__main__":
    test_wave()
