"""
Secure all buckets and create logs bucket.
"""
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOGS_BUCKET_NAME = f"dav1d-logs-{PROJECT_ID}"

def secure_buckets():
    print("="*80)
    print("🔒 SECURING BUCKETS")
    print("="*80)
    
    client = storage.Client(project=PROJECT_ID)
    buckets = list(client.list_buckets())
    
    print(f"Found {len(buckets)} buckets.")
    
    for bucket in buckets:
        print(f"\nChecking: {bucket.name}")
        
        # 1. Check Public Access Prevention
        iam_config = bucket.iam_configuration
        if not iam_config.public_access_prevention == "enforced":
            print(f"  ⚠️  Public access not enforced. Enforcing now...")
            bucket.iam_configuration.public_access_prevention = "enforced"
            bucket.patch()
            print(f"  ✓ Secured: Public access blocked.")
        else:
            print(f"  ✓ Secure: Public access blocked.")
            
        # 2. Check Uniform Bucket Level Access (Recommended)
        if not iam_config.uniform_bucket_level_access_enabled:
            print(f"  ℹ️  Uniform access not enabled (optional but recommended).")
        
    # Create Logs Bucket
    print(f"\n{'='*80}")
    print("📝 LOGS BUCKET SETUP")
    print(f"{'='*80}")
    
    try:
        bucket = client.get_bucket(LOGS_BUCKET_NAME)
        print(f"✓ Logs bucket exists: {LOGS_BUCKET_NAME}")
    except Exception:
        print(f"Creating logs bucket: {LOGS_BUCKET_NAME}...")
        bucket = client.create_bucket(LOGS_BUCKET_NAME, location="us-east4")
        
        # Enable versioning for logs (important for audit)
        bucket.versioning_enabled = True
        bucket.patch()
        print(f"✓ Created and enabled versioning.")
        
        # Block public access
        bucket.iam_configuration.public_access_prevention = "enforced"
        bucket.patch()
        print(f"✓ Secured.")

if __name__ == "__main__":
    secure_buckets()
