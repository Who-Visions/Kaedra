"""
Chroma SDK Diagnostic - Figure out WHY nothing is lighting up
"""
import requests
import time
import subprocess

CHROMA_SDK_URL = "http://localhost:54235/razer/chromasdk"

def check_sdk_status():
    print("=" * 60)
    print("🔍 CHROMA SDK DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Check if SDK is responding
    print("\n[1] Checking SDK availability...")
    try:
        r = requests.get(CHROMA_SDK_URL, timeout=5)
        print(f"    ✅ SDK responding: {r.json()}")
    except Exception as e:
        print(f"    ❌ SDK NOT responding: {e}")
        print("    → Ensure Razer Synapse is running with Chroma Connect enabled")
        return False
    
    # 2. Check if RzSDKServer is running
    print("\n[2] Checking RzSDKServer process...")
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq RzSDKServer.exe"],
            capture_output=True, text=True
        )
        if "RzSDKServer.exe" in result.stdout:
            print("    ✅ RzSDKServer.exe is running")
        else:
            print("    ❌ RzSDKServer.exe NOT found")
            return False
    except Exception as e:
        print(f"    ⚠️ Could not check process: {e}")
    
    # 3. Create session and hold it
    print("\n[3] Creating Chroma session...")
    payload = {
        "title": "Kaedra Diagnostic",
        "description": "Testing SDK Control",
        "author": {"name": "Kaedra", "contact": "diagnostic"},
        "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
        "category": "application"
    }
    
    try:
        r = requests.post(CHROMA_SDK_URL, json=payload, timeout=5)
        data = r.json()
        print(f"    Response: {data}")
        
        if "uri" not in data:
            print("    ❌ Failed to get session URI")
            return False
            
        uri = data["uri"]
        print(f"    ✅ Session URI: {uri}")
        
        # Wait for port
        print("    Waiting 3s for SDK port...")
        time.sleep(3)
        
    except Exception as e:
        print(f"    ❌ Session creation failed: {e}")
        return False
    
    # 4. Send to EVERY endpoint and log responses
    print("\n[4] Testing ALL endpoints with BRIGHT RED...")
    endpoints = ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"]
    
    red_static = {"effect": "CHROMA_STATIC", "param": {"color": 255}}  # Pure RED
    
    for ep in endpoints:
        try:
            r = requests.put(f"{uri}/{ep}", json=red_static, timeout=5)
            result = r.json()
            status = "✅" if result.get("result") == 0 else "❌"
            print(f"    {status} {ep}: {result}")
        except Exception as e:
            print(f"    ❌ {ep}: ERROR - {e}")
    
    # 5. Hold and prompt user
    print("\n" + "=" * 60)
    print("🚨 ALL DEVICES SHOULD BE RED NOW 🚨")
    print("=" * 60)
    print("""
If you see RED on ANY device, the SDK is working for that device.
If you see NOTHING:

1. Open Razer Synapse 4
2. Go to SETTINGS (gear icon) > MODULES
3. Ensure "CHROMA CONNECT" is ENABLED (toggle ON)
4. Go to CHROMA STUDIO > LINKED APPS or CONNECT > APPS
5. Look for "Kaedra Diagnostic" in the list
6. Drag it to the TOP of the app priority list

Also check:
- Windows Settings > Personalization > Dynamic Lighting → DISABLE IT
- Each device in Synapse should show "Chroma RGB" not "Dynamic Lighting"

Press ENTER when ready to continue...
""")
    
    # Keep alive while user checks
    print("Holding RED for 60 seconds (check your devices!)...")
    for i in range(60):
        try:
            requests.put(f"{uri}/heartbeat", timeout=2)
            # Re-send RED every 5 seconds to overcome any priority switching
            if i % 5 == 0:
                for ep in endpoints:
                    try:
                        requests.put(f"{uri}/{ep}", json=red_static, timeout=2)
                    except:
                        pass
        except:
            pass
        time.sleep(1)
        if i % 10 == 0:
            print(f"    {60-i}s remaining...")
    
    # 6. Cleanup
    print("\n[5] Cleaning up...")
    try:
        requests.delete(uri, timeout=5)
        print("    ✅ Session closed")
    except:
        pass
    
    return True


if __name__ == "__main__":
    check_sdk_status()
    input("\nPress ENTER to exit...")
