import requests
import time
import json
import logging

# Configure minimal logging for better visibility in background
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger("ChromaPersistent")

DISCOVERY_URL = "http://localhost:54235/razer/chromasdk"
APP_INFO = {
    "title": "Kaedra Persistent Driver",
    "description": "Infinite loop to maintain lighting state",
    "author": {"name": "Antigravity", "contact": "https://github.com/Who-Visions/Kaedra"},
    "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
    "category": "application"
}

def rgb_to_bgr(r, g, b):
    return (b << 16) | (g << 8) | r

def run_persistent():
    log.info("Starting Persistent Chroma Driver...")
    
    while True:
        try:
            log.info(f"Attempting handshake with {DISCOVERY_URL}...")
            r = requests.post(DISCOVERY_URL, json=APP_INFO, timeout=2)
            
            if r.status_code == 200:
                data = r.json()
                log.info(f"Raw Handshake Response: {data}")
                uri = data.get("uri")
                if not uri:
                    log.warning("Connected but no URI in response. Synapse might be busy or session rejected.")
                    time.sleep(2)
                    continue
                    
                log.info(f"SUCCESS! Session URI: {uri}")
                
                # Active Drive Loop
                colors = [
                    rgb_to_bgr(255, 0, 0),   # Red
                    rgb_to_bgr(0, 255, 0),   # Green
                    rgb_to_bgr(0, 0, 255),   # Blue
                    rgb_to_bgr(255, 255, 0), # Yellow
                    rgb_to_bgr(255, 0, 255), # Magenta
                    rgb_to_bgr(0, 255, 255)  # Cyan
                ]
                
                last_heartbeat = 0
                frame_count = 0
                
                while True:
                    t_now = time.time()
                    
                    # 1. Heartbeat every 1s
                    if t_now - last_heartbeat >= 1.0:
                        requests.put(f"{uri}/heartbeat", timeout=1)
                        last_heartbeat = t_now
                    
                    # 2. Cycle colors slowly (every 2 seconds)
                    color_idx = (int(t_now) // 2) % len(colors)
                    color = colors[color_idx]
                    
                    # 3. Drive ALL accessory types to find the stand
                    # ChromaLink (5 LEDs)
                    requests.put(f"{uri}/chromalink", json={"effect": "CHROMA_CUSTOM", "param": [color] * 5}, timeout=0.2)
                    
                    # Mousepad (15 LEDs - Laptop Stand mapping!)
                    requests.put(f"{uri}/mousepad", json={"effect": "CHROMA_CUSTOM", "param": [color] * 15}, timeout=0.2)
                    
                    # Keyboard (Static for reference)
                    requests.put(f"{uri}/keyboard", json={"effect": "CHROMA_STATIC", "param": {"color": color}}, timeout=0.2)
                    
                    if frame_count % 10 == 0:
                        log.info(f"Active Drive: Tick {frame_count} | Color Index {color_idx}")
                    
                    frame_count += 1
                    time.sleep(0.1) # 10Hz active driving
                    
            else:
                log.warning(f"Handshake failed with status {r.status_code}. Retrying in 5s...")
                time.sleep(5)
                
        except requests.exceptions.ConnectionError:
            log.warning("SDK not reachable. Is Synapse running? Retrying in 5s...")
            time.sleep(5)
        except Exception as e:
            log.error(f"Unexpected error: {e}. Session likely closed. Reconnecting in 2s...")
            time.sleep(2)

if __name__ == "__main__":
    try:
        run_persistent()
    except KeyboardInterrupt:
        log.info("Stopped by user.")
