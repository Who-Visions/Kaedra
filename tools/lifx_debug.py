from kaedra.services.lifx import LIFXService
import json

def main():
    print("[*] Initializing LIFX Service for Debugging...")
    try:
        lifx = LIFXService()
    except Exception as e:
        print(f"[!] Init Failed: {e}")
        return

    print("[*] Listing Lights...")
    lights = lifx.list_lights()
    
    if not lights:
        print("[!] No lights found. Check Token or Internet Connection.")
        return

    print(f"[✅] Found {len(lights)} lights:")
    for l in lights:
        print(f"  - Label: '{l.label}' | ID: {l.id} | Group: '{l.group}' | Power: {l.power} | Connected: {l.connected}")
        
    print("\n[*] Testing Selector 'group:Living Room'...")
    # Dry run check? API doesn't have dry run, but we can try to get state for just that group
    try:
        group_lights = lifx.list_lights("group:Living Room")
        print(f"[?] 'group:Living Room' matches {len(group_lights)} lights.")
    except Exception as e:
        print(f"[!] Error querying 'group:Living Room': {e}")

if __name__ == "__main__":
    main()
