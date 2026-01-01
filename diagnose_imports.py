import sys
import os

print(f"Python Version: {sys.version}")
print(f"Executable: {sys.executable}")

try:
    from googleapiclient.discovery import build
    print("Successfully imported googleapiclient.discovery")
except ImportError as e:
    print(f"Failed to import googleapiclient: {e}")

try:
    from google.cloud import vision
    from google.cloud import videointelligence
    print("Successfully imported vision/videointelligence from google.cloud")
except ImportError as e:
    print(f"Resilient fallback triggered for google.cloud: {e}")

try:
    from google import genai
    from google.genai import types
    print("Successfully imported google-genai")
except ImportError as e:
    print(f"Failed to import google-genai: {e}")

print("\n--- Testing kaedra.ingestion import ---")
try:
    from kaedra.ingestion import IngestionManager
    print("Successfully imported IngestionManager from kaedra.ingestion")
except ImportError as e:
    print(f"Failed to import IngestionManager: {e}")
except Exception as e:
    print(f"Unexpected error importing IngestionManager: {e}")
