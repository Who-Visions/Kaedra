#!/usr/bin/env python3
"""
Create dedicated GCS bucket for Dav1d Veo 3 videos
"""

import os
from google.cloud import storage

PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"
BUCKET_NAME = "dav1d-veo-videos"

def create_video_bucket():
    """Create a dedicated bucket for Veo 3 videos"""
    
    print(f"🪣 Creating video bucket: {BUCKET_NAME}")
    
    try:
        client = storage.Client(project=PROJECT_ID)
        
        # Check if bucket exists
        bucket = client.bucket(BUCKET_NAME)
        if bucket.exists():
            print(f"✅ Bucket already exists: gs://{BUCKET_NAME}")
            return True
        
        # Create bucket
        bucket = client.create_bucket(
            BUCKET_NAME,
            location=LOCATION
        )
        
        # Set lifecycle rule: Delete videos older than 90 days
        bucket.add_lifecycle_delete_rule(age=90)
        bucket.patch()
        
        print(f"✅ Created bucket: gs://{BUCKET_NAME}")
        print(f"   Location: {LOCATION}")
        print(f"   Lifecycle: Delete after 90 days")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return False


if __name__ == "__main__":
    create_video_bucket()
