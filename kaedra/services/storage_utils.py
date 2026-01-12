"""
Kaedra Storage Utilities
Handles GCS bucket operations for ingestion pipelines.
"""
from google.cloud import storage
from kaedra.core.config import PROJECT_ID

def get_storage_client():
    return storage.Client(project=PROJECT_ID)

def ensure_bucket(bucket_name: str):
    """Ensure the temporary ingestion bucket exists."""
    client = get_storage_client()
    try:
        bucket = client.get_bucket(bucket_name)
        return bucket
    except Exception:
        print(f"   ☁️ Creating bucket: {bucket_name}")
        return client.create_bucket(bucket_name, location="us-central1")

def upload_to_gcs(local_path: str, bucket_name: str, destination_blob_name: str) -> str:
    """Uploads a file to the bucket and returns the gcs uri."""
    bucket = ensure_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{destination_blob_name}"

def delete_from_gcs(bucket_name: str, blob_name: str):
    """Deletes a blob from the bucket."""
    client = get_storage_client()
    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()
    except Exception as e:
        print(f"   ⚠️ Failed to delete {blob_name} from GCS: {e}")

def blob_exists(bucket_name: str, blob_name: str) -> bool:
    """Checks if a blob exists in the bucket."""
    client = get_storage_client()
    try:
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception:
        return False
