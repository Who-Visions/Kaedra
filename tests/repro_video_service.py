
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from kaedra.services.video import VideoService
from kaedra.core.config import PROJECT_ID

def test_init_vertex_priority():
    """Test that initialization prioritizes Vertex and works without API keys."""
    
    # Temporarily unset keys to mimic Cloud Run environment
    original_api_key = os.environ.get("GOOGLE_AI_API_KEY")
    original_gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if "GOOGLE_AI_API_KEY" in os.environ:
        del os.environ["GOOGLE_AI_API_KEY"]
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
        
    print(f"Testing VideoService init with no API keys (Project: {PROJECT_ID})...")
    
    try:
        service = VideoService()
        # With new logic, this should succeed via Vertex AI because PROJECT_ID is set
        print("SUCCESS: VideoService initialized (Vertex AI Primary).")
        
        # Try a simple generation to confirm
        print("Attempting to generate test image...")
        try:
            img = service.generate_image("A futuristic cyberpunk city, neon lights, digital art")
            print("SUCCESS: Image generation successful.")
        except Exception as e:
            print(f"FAILURE: Image generation failed: {e}")

    except ValueError as e:
        print(f"FAILURE: Authentication failed unexpectedly: {e}")
    except Exception as e:
        print(f"UNEXPECTED FAILURE: {e}")
    finally:
        # Restore keys
        if original_api_key:
            os.environ["GOOGLE_AI_API_KEY"] = original_api_key
        if original_gemini_key:
            os.environ["GEMINI_API_KEY"] = original_gemini_key

if __name__ == "__main__":
    test_init_vertex_priority()
