#!/usr/bin/env python3
"""
Setup GCS bucket for DAV1D image storage
Creates bucket and configures it for image storage with lifecycle management
"""
import os
from dotenv import load_dotenv
load_dotenv()

from google.cloud import storage

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = "us-east4"
BUCKET_NAME = f"dav1d-images-{PROJECT_ID}"

print("="*80)
print("🎨 DAV1D Image Storage Bucket Setup")
print("="*80)
print(f"\nProject: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"Bucket: {BUCKET_NAME}\n")

try:
    # Initialize GCS client
    storage_client = storage.Client(project=PROJECT_ID)
    
    # Check if bucket exists
    try:
        bucket = storage_client.get_bucket(BUCKET_NAME)
        print(f"✓ Bucket already exists: {BUCKET_NAME}")
    except Exception:
        # Create bucket
        print(f"Creating bucket: {BUCKET_NAME}...")
        bucket = storage_client.create_bucket(
            BUCKET_NAME,
            location=LOCATION
        )
        print(f"✓ Bucket created!")
    
    # Enable versioning (keep previous versions of images)
    bucket.versioning_enabled = True
    bucket.patch()
    print("✓ Versioning enabled")
    
    # Set lifecycle rule to delete old versions after 30 days
    # (keeps current version forever, but auto-cleans old versions)
    lifecycle_rules = [
        {
            "action": {"type": "Delete"},
            "condition": {
                "numNewerVersions": 3,  # Keep last 3 versions
                "isLive": False  # Only delete non-current versions
            }
        }
    ]
    bucket.lifecycle_rules = lifecycle_rules
    bucket.patch()
    print("✓ Lifecycle rules configured (keeps last 3 versions)")
    
    # Create folder structure
    folders = [
        "imagen/",      # Imagen 4 generations
        "gemini/",      # Gemini image generations
        "archive/",     # Archived images
    ]
    
    print("\n📁 Creating folder structure...")
    for folder in folders:
        blob = bucket.blob(folder + ".placeholder")
        blob.upload_from_string("")
        print(f"  ✓ {folder}")
    
    print(f"\n{'='*80}")
    print("✅ SETUP COMPLETE!")
    print(f"{'='*80}")
    print(f"\n🌐 Bucket URL: https://console.cloud.google.com/storage/browser/{BUCKET_NAME}")
    print(f"📊 Images will be saved to: gs://{BUCKET_NAME}/")
    print(f"\n💡 Bucket features:")
    print(f"  • Versioning: Enabled")
    print(f"  • Location: {LOCATION}")
    print(f"  • Lifecycle: Auto-cleanup after 3 versions")
    print(f"  • Folders: imagen/, gemini/, archive/")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print(f"\n💡 Make sure you have permissions:")
    print(f"  • storage.buckets.create")
    print(f"  • storage.buckets.update")
