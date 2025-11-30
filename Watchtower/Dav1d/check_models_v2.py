
import os
import sys
from google import genai

# Force us-east4
PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"

print(f"Checking models in {LOCATION} for project {PROJECT_ID}...")

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    print("Client initialized.")
    
    print("Listing models...")
    models = list(client.models.list())
    
    print(f"\nFound {len(models)} models.")
    print("-" * 40)
    for m in models:
        if "gemini" in m.name.lower():
            print(f"NAME: {m.name}")
            print(f"DISPLAY: {m.display_name}")
            print("-" * 20)
            
except Exception as e:
    print(f"\nERROR: {e}")
