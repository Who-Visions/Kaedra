
from vertexai.preview import reasoning_engines
import vertexai

PROJECT = "gen-lang-client-0939852539"
LOCATION = "us-central1"
RESOURCE_ID = "projects/69017097813/locations/us-central1/reasoningEngines/5808320806819725312"

vertexai.init(project=PROJECT, location=LOCATION)

print(f"[*] Connecting to: {RESOURCE_ID}")
remote_app = reasoning_engines.ReasoningEngine(RESOURCE_ID)

print("[*] Sending query...")
response = remote_app.query(message="Yo, status check")
print(f"[*] Response: {response}")
