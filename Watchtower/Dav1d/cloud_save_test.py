"""Test cloud-first image saving with GCS"""
import os, sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.getcwd())

# Force reload
import importlib
if 'dav1d' in sys.modules:
    importlib.reload(sys.modules['dav1d'])
    
from dav1d import get_model, MODELS

prompt = "A cyberpunk warrior with neon armor, dramatic lighting, futuristic city background"

print("="*80)
print("🌐 Testing Cloud-First Image Save")
print("="*80)
print(f"\nPrompt: {prompt}")
print(f"Model: Imagen 4\n")

try:
    model = get_model(MODELS["vision"])
    response = model.generate_content(prompt)
    
    print("="*80)
    print("✅ SUCCESS!")
    print("="*80)
    print(f"\n{response.text}\n")
    
    if hasattr(response, 'gcs_urls') and response.gcs_urls:
        print("="*80)
        print("☁️  CLOUD STORAGE")
        print("="*80)
        for url in response.gcs_urls:
            print(f"  {url}")
        
        print(f"\n💡 View in console:")
        bucket_name = url.split('/')[2]
        print(f"  https://console.cloud.google.com/storage/browser/{bucket_name}")
    
    if hasattr(response, 'saved_paths') and response.saved_paths:
        print(f"\n="*80)
        print("💾 LOCAL CACHE")
        print("="*80)
        for path in response.saved_paths:
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  {os.path.basename(path)} ({size:,} bytes)")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
