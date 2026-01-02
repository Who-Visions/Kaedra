
import os
import vertexai
from vertexai.generative_models import GenerativeModel
import time

# Set credentials implicitly via environment if needed, or rely on default
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0939852539"
PROJECT_ID = "gen-lang-client-0939852539"
LOCATION = "us-central1"

print(f"[*] Initializing Vertex AI for {PROJECT_ID} in {LOCATION}...")
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print("[*] Vertex AI Initialized.")
except Exception as e:
    print(f"[!] Init Failed: {e}")
    exit(1)

model_name = "gemini-3-flash-preview"
print(f"[*] Testing model: {model_name}")

try:
    model = GenerativeModel(model_name)
    print("[*] Model instantiated.")
    
    print("[*] Sending test prompt...")
    start = time.time()
    response = model.generate_content("Hello, are you Gemini 3?")
    print(f"[*] Response received in {time.time() - start:.2f}s:")
    print(response.text)
    print("[*] SUCCESS")
except Exception as e:
    print(f"[!] FAILED: {e}")
