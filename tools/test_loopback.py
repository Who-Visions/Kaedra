import sounddevice as sd
import numpy as np

try:
    # Get default output device
    default_out = sd.query_devices(kind='output')
    index = default_out['index']
    print(f"Default Output: {default_out['name']} (Index {index})")
    
    # Try to open loopback stream (WASAPI specific flag usually)
    # Note: official sounddevice might not support loopback=True directly without special build.
    # But checking if we can open it as input.
    
    # Usually loopback is accessed via special API or device config.
    # If this fails, we look for "Stereo Mix".
    
    try:
        # WASAPI Loopback hack: try opening input on output device?
        # Often requires 'loopback=True' in recent sd versions
        with sd.InputStream(device=index, channels=1, loopback=True) as stream:
             print("Success! Loopback supported via 'loopback=True'.")
    except TypeError:
        print("TypeError: 'loopback' argument not supported in this version.")
    except Exception as e:
        print(f"Failed direct loopback: {e}")
        
    # Check for "Stereo Mix"
    print("\nScanning for Stereo Mix...")
    devices = sd.query_devices()
    found = False
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0 and ("Mix" in dev['name'] or "Wave" in dev['name']):
            print(f"Found candidate: {dev['name']} (Index {i})")
            found = True
            
    if not found:
        print("No Stereo Mix found.")

except Exception as e:
    print(f"Fatal error: {e}")
