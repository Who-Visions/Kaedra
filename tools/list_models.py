
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def list_models():
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        print("Listing models...")
        # v1beta is the default for the SDK usually
        models = client.models.list()
        for m in models:
            print(f"- {m.name}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
