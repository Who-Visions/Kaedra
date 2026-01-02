import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import aiplatform

PROJECT_ID = "gen-lang-client-0939852539"
LOCATION = "us-central1"

def list_models():
    print(f"[*] Listing models for {PROJECT_ID} in {LOCATION}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    try:
        # P.S. The SDK doesn't have a simple "list_models" for GenerativeModel class directly 
        # exposing semantic names easily in all versions, but we can try the Model Garden / Model Registry API.
        # Alternatively, we just try to instantiate a few known candidates and see which doesn't error on 'get_model'.
        
        candidates = [
            "gemini-2.5-flash", 
            "gemini-2.5-flash-001",
            "gemini-2.5-flash-preview", 
            "gemini-2.5-pro",
            "gemini-2.5-flash-native-audio-preview-09-2025",
            "gemini-3-flash-preview",
            "gemini-2.0-flash-exp"
        ]
        
        print("\nChecking validity of specific model names:")
        for model_name in candidates:
            try:
                model = GenerativeModel(model_name)
                # Just checking object creation isn't enough, we need to try a dry run call or check existence
                # But typically 'GenerativeModel' constructor is lazy. 
                # Real verification happens on generation.
                print(f"  [?] {model_name} (Constructor OK)")
            except Exception as e:
                print(f"  [X] {model_name} (Constructor Failed: {e})")
                
        # Better: List from Model Garden if possible (requires different permission/API)
        # Using aiplatform.Model.list() usually lists custom trained models.
        # Foundation models are often under a specific publisher path.
        
        print("\n(Note: True validation requires making a test call)")
        
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    list_models()
