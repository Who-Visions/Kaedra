#!/usr/bin/env python
"""Find which device has browser/YouTube audio."""
import sounddevice as sd
import numpy as np

print("🔍 Scanning for browser audio...\n")

# Devices to test
test_names = ["browser", "elgato out", "elgato only", "headphones"]

devices = sd.query_devices()
matches = [(i, d['name']) for i, d in enumerate(devices) 
           if any(t in d['name'].lower() for t in test_names) and d['max_input_channels'] > 0]

for dev_id, dev_name in matches[:8]:
    try:
        audio = sd.rec(int(16000 * 2), samplerate=16000, channels=1, device=dev_id, dtype='float32')
        sd.wait()
        rms = np.sqrt(np.mean(audio**2)) * 1000
        level = "🔊 AUDIO!" if rms > 5 else "🔇"
        print(f"{dev_id:3}: {dev_name[:40]} | RMS: {rms:5.1f} | {level}")
    except Exception as e:
        print(f"{dev_id:3}: {dev_name[:40]} | ERROR")

print("\n✅ Look for 'AUDIO!' - that's where browser sound is playing")
