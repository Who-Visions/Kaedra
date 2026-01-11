import json

LOG_PATH = r"C:\Users\super\AppData\Local\Razer\RazerAppEngine\User Data\Logs\chroma-studio.log"

def parse_dimensions():
    print(f"Reading {LOG_PATH}...")
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if "refreshPreviewEngine" in line and "\"devices\":[" in line:
                    try:
                        start = line.find("data:") + 5
                        json_str = line[start:].strip()
                        data = json.loads(json_str)
                        devices = data.get('payload', {}).get('devices', [])
                        
                        for dev in devices:
                            name = dev.get('productName')
                            config = dev.get('config', {})
                            rows = config.get('MatrixMaxRow')
                            cols = config.get('MatrixMaxCol')
                            leds = dev.get('leds', [])
                            
                            print(f"\n--- {name} ---")
                            print(f"ContainerID: {dev.get('deviceContainerId')}")
                            print(f"Matrix: {rows} Rows x {cols} Cols")
                            if leds:
                                print(f"First LED: Row {leds[0].get('row')}, Col {leds[0].get('col')}")
                                print(f"Last LED:  Row {leds[-1].get('row')}, Col {leds[-1].get('col')}")
                            print("-" * 30)
                            
                    except Exception as e:
                        print(f"Error parsing: {e}")
    except Exception as e:
        print(f"File error: {e}")

if __name__ == "__main__":
    parse_dimensions()
