
from PIL import Image
from pathlib import Path

def probe_metadata():
    folder = Path(r"C:\Users\super\Watchtower\Shadow Dweller\Shadow Dweller")
    files = list(folder.glob("*.png"))[:3]
    
    for f in files:
        print(f"\nScanning: {f.name}")
        try:
            with Image.open(f) as img:
                print("Format:", img.format)
                print("Info:", img.info)
                if img.text:
                    print("Text:", img.text)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    probe_metadata()
