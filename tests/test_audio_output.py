import sounddevice as sd
import numpy as np
import time

def play_tone(device_idx=None, device_name="Default"):
    print(f"\n[?] Testing Device: {device_name} (Index: {device_idx})")
    fs = 24000
    duration = 1.0  # seconds
    f = 440.0  # Hz
    t = np.arange(int(fs * duration)) / fs
    # Generate sine wave: 440Hz
    audio = 0.5 * np.sin(2 * np.pi * f * t)
    # Convert to 16-bit PCM integer
    audio = (audio * 32767).astype(np.int16)
    
    try:
        sd.play(audio, samplerate=fs, device=device_idx, blocking=True)
        print(f"   [+] Playback command sent to {device_name}.")
    except Exception as e:
        print(f"   [!] Failed to play on {device_name}: {e}")

print("=== KAEDRA AUDIO DIAGNOSTIC ===")
print(f"Default Output Device Index: {sd.default.device[1]}")

devices = sd.query_devices()
print("\nAvailable Output Devices:")
found_chat_mix = None
for i, d in enumerate(devices):
    if d['max_output_channels'] > 0:
        print(f"  [{i}] {d['name']}")
        if "Chat Mix" in d['name'] or "Game" in d['name']:
            found_chat_mix = i

print("\n--- TEST 1: System Default ---")
play_tone(None, "System Default")

if found_chat_mix is not None:
    print(f"\n--- TEST 2: Chat Mix (Index {found_chat_mix}) ---")
    play_tone(found_chat_mix, "Chat Mix / Game")
else:
    print("\n[!] 'Chat Mix' or 'Game' device not explicitly found in list.")

print("\n=== END DIAGNOSTIC ===")
