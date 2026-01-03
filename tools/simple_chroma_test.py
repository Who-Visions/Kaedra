
import sys
import os
import requests

sys.path.append(os.getcwd())

print("════ SIMPLE CHROMA TEST ════")

# Manual handshake
URI = "http://localhost:54235/razer/chromasdk"
payload = {
    "title": "Kaedra Story Engine",
    "description": "AI Narrative Lighting Control",
    "author": {"name": "Who Visions", "contact": "dave@whovisions.com"},
    "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
    "category": "application"
}

print("[1] Connecting...")
try:
    resp = requests.post(URI, json=payload, timeout=5)
    print(f"    Status: {resp.status_code}")
    print(f"    Response: {resp.text}")
    
    if resp.status_code == 200:
        data = resp.json()
        session_uri = data.get("uri")
        print(f"    Session URI: {session_uri}")
        
        # Test 1: CHROMA_NONE (Clear)
        print()
        print("[2] Testing CHROMA_NONE (Clear effect)...")
        r = requests.put(f"{session_uri}/keyboard", json={"effect": "CHROMA_NONE"})
        print(f"    Result: {r.json()}")
        
        # Test 2: Simple Static
        print()
        print("[3] Testing CHROMA_STATIC (Blue)...")
        r = requests.put(f"{session_uri}/keyboard", json={"effect": "CHROMA_STATIC", "param": {"color": 0xFF0000}})
        print(f"    Result: {r.json()}")
        
        # Test 3: Heartbeat
        print()
        print("[4] Testing Heartbeat...")
        r = requests.put(f"{session_uri}/heartbeat")
        print(f"    Result: {r.json()}")
        
        # Cleanup
        print()
        print("[5] Closing session...")
        requests.delete(session_uri)
        print("    Done.")
        
except Exception as e:
    print(f"ERROR: {e}")
