import json
import os

LOG_PATH = r"C:\Users\super\AppData\Local\Razer\RazerAppEngine\User Data\Logs\chroma-studio.log"

def parse_log():
    print(f"Reading {LOG_PATH}...")
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if "refreshPreviewEngine" in line and "\"devices\":[" in line:
                    # Extract JSON payload
                    try:
                        # Find start of JSON
                        start = line.find("data:") + 5
                        json_str = line[start:].strip()
                        data = json.loads(json_str)
                        
                        devices = data.get('payload', {}).get('devices', [])
                        print(f"\nFound {len(devices)} devices:")
                        for dev in devices:
                            print(f"- Name: {dev.get('productName')}")
                            print(f"  PID: {dev.get('productId')} (0x{dev.get('productId'):04X})")
                            print(f"  ContainerID: {dev.get('deviceContainerId')}")
                            print(f"  DeviceID: {dev.get('deviceId')}")
                            print("-" * 30)
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON Parse Error: {e}")
                    except Exception as e:
                        print(f"Extraction Error: {e}")
    except Exception as e:
        print(f"File Error: {e}")

if __name__ == "__main__":
    parse_log()
