from google import genai
import os

client = genai.Client(vertexai=True, project="gen-lang-client-0285887798", location="us-east4")

models_to_test = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro-002"
]

print("Testing models...")
for model in models_to_test:
    try:
        print(f"Testing {model}...", end=" ")
        response = client.models.generate_content(model=model, contents="Hi")
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
