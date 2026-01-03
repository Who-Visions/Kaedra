import sounddevice as sd

print(f"SoundDevice Version: {sd.__version__}")
print("\nScanning Audio Devices...\n")

try:
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        # Filter for inputs that might be system audio
        name = dev['name']
        api = dev['hostapi']
        
        # Highlight interesting ones
        if "Elgato" in name or "Chat" in name or "Mix" in name or "Output" in name or "Stream" in name:
             print(f"[{i}] {name} (In: {dev['max_input_channels']}, Out: {dev['max_output_channels']}, API: {api})")


except Exception as e:
    print(f"Error: {e}")
