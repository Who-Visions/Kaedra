import json
try:
    with open("kaedra/config/fleet.json", "r", encoding="utf-8") as f:
        json.load(f)
    print("VALID JSON")
except Exception as e:
    print(f"INVALID JSON: {e}")
