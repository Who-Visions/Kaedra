
import requests
import json

URI = "http://localhost:54235/razer/chromasdk"

# 1. Get version
print("════ RAZER SDK DIAGNOSTIC ════")
print()
print("[1] SDK Version:")
r = requests.get(URI)
print(f"    {r.json()}")

# 2. Init session
print()
print("[2] Creating Session...")
payload = {
    "title": "Kaedra Story Engine",
    "description": "AI Narrative Lighting Control",
    "author": {"name": "Who Visions", "contact": "dave@whovisions.com"},
    "device_supported": ["keyboard"],  # Only keyboard
    "category": "application"
}
r = requests.post(URI, json=payload, timeout=5)
data = r.json()
session = data.get("uri")
print(f"    Session: {session}")

# 3. Test different effect types
print()
print("[3] Testing Effect Types:")

effects = [
    ("CHROMA_NONE", {}),
    ("CHROMA_STATIC", {"color": 0xFF0000}),
    ("CHROMA_WAVE", {"direction": 1}),
]

for name, param in effects:
    payload = {"effect": name}
    if param:
        payload["param"] = param
    r = requests.put(f"{session}/keyboard", json=payload)
    result = r.json().get("result", "N/A")
    status = "✅" if result == 0 else f"❌ ({result})"
    print(f"    {name}: {status}")

# 4. Try ChromaLink
print()
print("[4] Testing ChromaLink:")
r = requests.put(f"{session}/chromalink", json={"effect": "CHROMA_STATIC", "param": {"color": 0x00FF00}})
result = r.json().get("result", "N/A")
status = "✅" if result == 0 else f"❌ ({result})"
print(f"    CHROMA_STATIC: {status}")

# Cleanup
print()
print("[5] Cleanup...")
requests.delete(session)
print("    Done.")
