"""
Kaedra Chroma Stand Active Drive Test
Restored from 'debug_continuous_static.py' - verified working by User.
Actively drives the ChromaLink hardware with continuous frame updates to prevent timeout.
"""
import requests
import time

URI_INIT = "http://localhost:54235/razer/chromasdk"
APP_INFO = {
    "title": "Kaedra Story Engine",
    "description": "AI Narrative Lighting Control",
    "author": {
        "name": "Meralus",
        "contact": "meralus@watchtower.local"
    },
    "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
    "category": "application"
}

def rgb_to_bgr(r, g, b):
    return (b << 16) | (g << 8) | r

def run():
    print("INIT: Connecting...")
    try:
        resp = requests.post(URI_INIT, json=APP_INFO, timeout=2)
        if resp.status_code != 200:
            print(f"FAIL: {resp.text}")
            return
        
        data = resp.json()
        uri = data.get("uri")
        print(f"SUCCESS: Connected to {uri}")
        
        print("\n!!! LOOK AT STAND !!!")
        print("Driving RED continuously for 5 seconds...")
        
        t0 = time.time()
        last_heartbeat = 0
        
        # RED (Full Brightness)
        red_color = rgb_to_bgr(255, 0, 0)
        param = [red_color] * 5
        payload = {"effect": "CHROMA_CUSTOM", "param": param}
        
        while time.time() - t0 < 5.0:
            t = time.time() - t0
            if t - last_heartbeat >= 1.0:
                requests.put(f"{uri}/heartbeat", timeout=1)
                last_heartbeat = t
            
            # Re-send the SAME frame repeatedly
            requests.put(f"{uri}/chromalink", json=payload, timeout=0.2)
            time.sleep(0.1) # 10 FPS

        print("Driving GREEN continuously for 5 seconds...")
        t0 = time.time()
        green_color = rgb_to_bgr(0, 255, 0)
        param = [green_color] * 5
        payload = {"effect": "CHROMA_CUSTOM", "param": param}
        
        while time.time() - t0 < 5.0:
            t = time.time() - t0
            if t - last_heartbeat >= 1.0:
                requests.put(f"{uri}/heartbeat", timeout=1)
                last_heartbeat = t
            requests.put(f"{uri}/chromalink", json=payload, timeout=0.2)
            time.sleep(0.1)
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        print("Cleaning up...")
        try:
            requests.delete(uri, timeout=1)
        except: pass

if __name__ == "__main__":
    run()
