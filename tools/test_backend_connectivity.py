import socket
import requests

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"

def test_backend():
    """Test if the backend is accessible."""
    local_ip = get_local_ip()
    print(f"🔍 Local IP Address: {local_ip}")
    print(f"📡 Testing backend connectivity...\n")
    
    # Test localhost
    print("Testing http://localhost:8000/health")
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print(f"✅ Localhost: {response.status_code}")
    except Exception as e:
        print(f"❌ Localhost: {e}")
    
    # Test 127.0.0.1
    print("\nTesting http://127.0.0.1:8000/health")
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=2)
        print(f"✅ 127.0.0.1: {response.status_code}")
    except Exception as e:
        print(f"❌ 127.0.0.1: {e}")
    
    # Test local IP
    print(f"\nTesting http://{local_ip}:8000/health")
    try:
        response = requests.get(f"http://{local_ip}:8000/health", timeout=2)
        print(f"✅ Local IP ({local_ip}): {response.status_code}")
    except Exception as e:
        print(f"❌ Local IP ({local_ip}): {e}")
    
    # Test the configured IP
    configured_ip = "192.168.1.187"
    print(f"\nTesting http://{configured_ip}:8000/health")
    try:
        response = requests.get(f"http://{configured_ip}:8000/health", timeout=2)
        print(f"✅ Configured IP ({configured_ip}): {response.status_code}")
    except Exception as e:
        print(f"❌ Configured IP ({configured_ip}): {e}")
    
    print(f"\n📱 For mobile access, use: http://{local_ip}:8000")
    print(f"⚠️ Make sure:")
    print(f"   1. Backend server is running")
    print(f"   2. Phone is on the same WiFi network")
    print(f"   3. Firewall allows port 8000")

if __name__ == "__main__":
    test_backend()
