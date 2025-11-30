import os
from google.cloud import storage
from google.api_core.exceptions import NotFound, Forbidden

# Configuration
PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"
BUCKET_NAME = f"dav1d-memory-{PROJECT_ID}"

def setup_memory_bucket():
    print(f"Initializing Memory Infrastructure for Project: {PROJECT_ID}")
    print(f"Target Bucket: {BUCKET_NAME}")
    
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        
        # Check if bucket exists
        try:
            bucket = storage_client.get_bucket(BUCKET_NAME)
            print(f"Found existing bucket: {bucket.name}")
        except NotFound:
            print(f"Creating new bucket: {BUCKET_NAME} in {LOCATION}...")
            bucket = storage_client.create_bucket(BUCKET_NAME, location=LOCATION)
            print(f"Created bucket: {bucket.name}")
        
        # Enable Versioning (Safety for memory)
        print("Enabling object versioning...")
        bucket.versioning_enabled = True
        bucket.patch()
        print("Versioning enabled.")
        
        # Create folder structure placeholders
        blobs = [
            "memory/.keep",
            "chat_logs/.keep",
            "resources/.keep"
        ]
        
        for blob_name in blobs:
            blob = bucket.blob(blob_name)
            if not blob.exists():
                blob.upload_from_string("")
                print(f"Created placeholder: {blob_name}")
                
        print("\n✅ Memory Infrastructure Setup Complete!")
        print(f"gs://{BUCKET_NAME}/")
        
    except Forbidden:
        print("❌ Error: Permission denied. Please ensure you have Storage Admin role.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_memory_bucket()
