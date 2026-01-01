import sys
import time
try:
    import sounddevice as sd
    import numpy as np
    print(f"[*] sounddevice version: {sd.__version__}")
    print(f"[*] numpy version: {np.__version__}")
except ImportError as e:
    print(f"[!] ImportError: {e}")
    sys.exit(1)
except OSError as e:
    print(f"[!] OSError (PortAudio?): {e}")
    sys.exit(1)

print("\n--- Audio Devices ---")
try:
    devices = sd.query_devices()
    print(devices)
except Exception as e:
    print(f"[!] Error querying devices: {e}")

print("\n--- Testing Output ---")
try:
    fs = 44100
    duration = 1.0  # seconds
    f = 440.0  # Hz
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    my_array = 0.5 * np.sin(2 * np.pi * f * t)
    
    print("[*] Playing 440Hz sine wave...")
    sd.play(my_array, fs)
    sd.wait()
    print("[*] Playback complete.")
except Exception as e:
    print(f"[!] Playback verification failed: {e}")

print("\n--- Testing Input (RMS) ---")
try:
    duration = 3 # seconds
    print(f"[*] Recording for {duration} seconds (speak now)...")
    def callback(indata, frames, time, status):
        if status:
            print(status)
        rms = np.sqrt(np.mean(indata**2))
        sys.stdout.write(f"\rRMS: {rms:.4f} " + "|" * int(rms * 100))
        sys.stdout.flush()

    with sd.InputStream(callback=callback):
        sd.sleep(duration * 1000)
    print("\n[*] Input test complete.")
except Exception as e:
    print(f"[!] Input verification failed: {e}")
