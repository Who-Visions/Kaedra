#!/usr/bin/env python
"""Test Browsers (Elgato) input for caller audio."""
import sounddevice as sd
import numpy as np

# Find Browsers device
devices = sd.query_devices()
browser_devices = [(i, d['name']) for i, d in enumerate(devices) 
                   if 'browser' in d['name'].lower() and d['max_input_channels'] > 0]

print("🌐 Testing Browser audio inputs for caller capture...\n")

for dev_id, dev_name in browser_devices:
    try:
        print(f"Recording from: {dev_id}: {dev_name}...")
        audio = sd.rec(int(16000 * 2), samplerate=16000, channels=1, device=dev_id, dtype='float32')
        sd.wait()
        rms = np.sqrt(np.mean(audio**2)) * 1000
        level = "🔊 CALLER DETECTED!" if rms > 3 else "🔇 silent"
        print(f"  → RMS: {rms:.1f} | {level}\n")
    except Exception as e:
        print(f"  → ERROR: {str(e)[:50]}\n")

# Also test Chat Mix variants
print("Also testing Chat Mix inputs...\n")
chat_devices = [(i, d['name']) for i, d in enumerate(devices) 
                if 'chat' in d['name'].lower() and d['max_input_channels'] > 0]

for dev_id, dev_name in chat_devices[:3]:
    try:
        audio = sd.rec(int(16000 * 2), samplerate=16000, channels=1, device=dev_id, dtype='float32')
        sd.wait()
        rms = np.sqrt(np.mean(audio**2)) * 1000
        level = "🔊 ACTIVE" if rms > 3 else "🔇 silent"
        print(f"{dev_id}: {dev_name[:35]} | RMS: {rms:.1f} | {level}")
    except Exception as e:
        print(f"{dev_id}: {dev_name[:35]} | ERROR")

print("\n✅ Done! Look for 'CALLER DETECTED' or 'ACTIVE'")
