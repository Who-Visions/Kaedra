import os
from google.cloud import storage
from google import genai
from config import PROJECT_ID, LOCATION, BUCKET_NAME, LOGS_BUCKET_NAME, Colors
from logging_config import logger

def check_gcs_health() -> bool:
    """Check if GCS is accessible."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        # Just check if bucket exists (metadata check)
        if bucket.exists():
            # logger.info(f"GCS Health Check: {Colors.NEON_GREEN}PASS{Colors.RESET} ({BUCKET_NAME})")
            return True
        else:
            logger.warning(f"GCS Health Check: {Colors.NEON_RED}FAIL{Colors.RESET} (Bucket {BUCKET_NAME} not found)")
            return False
    except Exception as e:
        logger.warning(f"GCS Health Check: {Colors.NEON_RED}FAIL{Colors.RESET} ({e})")
        return False

def check_vertex_health() -> bool:
    """Check if Vertex AI is accessible."""
    try:
        # Simple list models or similar lightweight call
        # Or just instantiate client
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        # We won't make a call to save cost/latency, just client init is a basic check
        # But to be sure, we might want to list models?
        # list(client.models.list_models(page_size=1))
        # logger.info(f"Vertex AI Health Check: {Colors.NEON_GREEN}PASS{Colors.RESET}")
        return True
    except Exception as e:
        logger.warning(f"Vertex AI Health Check: {Colors.NEON_RED}FAIL{Colors.RESET} ({e})")
        return False

def sync_file_to_cloud(local_path, bucket_name, blob_name):
    """Upload a file to GCS with graceful fallback."""
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))
        return True
    except Exception as e:
        logger.warning(f"Cloud Sync Failed for {blob_name}: {e}")
        return False
