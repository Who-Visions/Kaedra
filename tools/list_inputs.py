#!/usr/bin/env python
"""List all audio INPUT devices."""
import sounddevice as sd

devices = sd.query_devices()
print("=== AUDIO INPUT DEVICES ===\n")
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f"{i:3}: {d['name'][:50]} (channels: {d['max_input_channels']})")
