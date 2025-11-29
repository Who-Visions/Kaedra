"""Direct test of cloud-first save - bypassing dav1d.py"""
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import GenerateImagesConfig
from google.cloud import storage
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = "us-east4"
BUCKET_NAME = f"dav1d-images-{PROJECT_ID}"

print("="*80)
print("🌐 Cloud-First Image Save Test")
print("="*80)
print(f"Project: {PROJECT_ID}")
print(f"Bucket: {BUCKET_NAME}\n")

# Generate image
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
prompt = "A futuristic robot with glowing cyan circuits, standing in a neon cityscape"

print(f"Generating: {prompt}\n")

try:
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=GenerateImagesConfig(number_of_images=1)
    )
    
    print("✓ Image generated!")
    
    # Save to GCS first
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket = gcs_client.bucket(BUCKET_NAME)
    
    timestamp = datetime.now(ZoneInfo("US/Eastern")).strftime("%Y%m%d_%H%M%S")
    filename = f"imagen_{timestamp}_1.png"
    
    # 1. Upload to cloud
    gcs_path = f"imagen/{filename}"
    blob = bucket.blob(gcs_path)
    image_bytes = response.generated_images[0].image.image_bytes
    blob.upload_from_string(image_bytes, content_type='image/png')
    gcs_url = f"gs://{BUCKET_NAME}/{gcs_path}"
    
    print(f"\n☁️  CLOUD:")
    print(f"   {gcs_url}")
    print(f"   https://console.cloud.google.com/storage/browser/{BUCKET_NAME}/imagen")
    
    # 2. Cache locally
    images_dir = Path.cwd() / "images"
    images_dir.mkdir(exist_ok=True)
    local_path = images_dir / filename
    
    with open(local_path, 'wb') as f:
        f.write(image_bytes)
    
    print(f"\n💾 LOCAL:")
    print(f"   {local_path}")
    print(f"   {len(image_bytes):,} bytes ({len(image_bytes)/1024/1024:.2f} MB)")
    
    print(f"\n{'='*80}")
    print("✅ Cloud-first save working perfectly!")
    print(f"{'='*80}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
