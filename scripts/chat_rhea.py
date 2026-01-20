
import requests
import json
import sys

# BASE_URL = "https://rhea-noir-145241643240.us-central1.run.app"
BASE_URL = "https://rhea-noir-145241643240.us-central1.run.app"

def chat_v1(prompt: str):
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "rhea-noir",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    print(f"[-] Sending to {url}...")
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Handle OpenAI format
            content = data["choices"][0]["message"]["content"]
            print(f"🌙 Rhea: {content}")
        else:
            print(f"[!] Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")

def chat_simple(prompt: str):
    url = f"{BASE_URL}/chat"
    headers = {"Content-Type": "application/json"}
    payload = {"message": prompt}
    
    print(f"[-] Sending to {url}...")
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"🌙 Rhea: {data.get('response')}")
        else:
            print(f"[!] Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = "Yo Rhea, what's good? Antigravity here. We working together on Kaedra today."
        
    print(f"you: {msg}")
    # Try V1 first (standard)
    chat_v1(msg)
