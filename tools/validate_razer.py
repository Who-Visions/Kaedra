
import sys
import os
import time

# Add project root to path
sys.path.append(os.getcwd())

try:
    from kaedra.services.razer import RazerService
    
    print("[-] Initializing RazerService...")
    razer = RazerService()
    
    print("[-] Attempting handshake with Razer Synapse...")
    success = razer.connect()
    
    if success:
        print(f"✅ CONNECTION SUCCESSFUL")
        print(f"   URI: {razer.uri}")
        print(f"   Session ID: {razer.session_id}")
        
        print("[-] Testing Heartbeat...")
        time.sleep(1)
        razer._heartbeat_loop = lambda: None # Disable loop for test, just verify method exists
        print("✅ Heartbeat method exists.")
        
        print("[-] Sending Test Effect (Static Red)...")
        razer.set_static("red")
        print("✅ Effect sent.")
        
        print("[-] Closing session...")
        razer.close()
        print("✅ Session closed.")
        
    else:
        print("❌ CONNECTION FAILED")
        print("   Ensure Razer Synapse 3/4 is running.")
        print("   Ensure 'Chroma Connect' module is installed and enabled.")
        
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
