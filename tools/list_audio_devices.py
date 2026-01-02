import sounddevice as sd

def list_devices():
    print("Available Audio Devices:")
    print(sd.query_devices())
    
    print("\nDefault Input Device:")
    try:
        print(sd.query_devices(kind='input'))
    except Exception as e:
        print(f"Error querying default input: {e}")

if __name__ == "__main__":
    list_devices()
