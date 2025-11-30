"""
Simple direct test - bypassing dav1d.py entirely
"""
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import GenerateImagesConfig, GenerateContentConfig

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

prompt = "A futuristic cityscape with neon lights"

print("Testing Imagen 4...")
try:
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=GenerateImagesConfig(number_of_images=1)
    )
    print(f"✓ Imagen 4 works! Generated {len(response.generated_images)} image(s)")
    
    # Save it
    from pathlib import Path
    images_dir = Path.cwd() / "images"
    images_dir.mkdir(exist_ok=True)
    filepath = images_dir / "test_imagen4.png"
    response.generated_images[0].image.save(str(filepath))
    print(f"✓ Saved to: {filepath}")
    
except Exception as e:
    print(f"✗ Imagen 4 failed: {e}")

print("\nTesting Gemini 3 Pro Image...")
try:
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            temperature=1.0
        )
    )
    print(f"✓ Gemini 3 Pro works!")
    print(f"Text: {response.text[:100] if hasattr(response, 'text') else 'No text'}")
    
    # Try to extract and save image
    if hasattr(response, 'candidates') and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                for idx, part in enumerate(candidate.content.parts):
                    if hasattr(part, 'inline_data'):
                        from pathlib import Path
                        images_dir = Path.cwd() / "images"
                        images_dir.mkdir(exist_ok=True)
                        filepath = images_dir / f"test_gemini3pro.png"
                        with open(filepath, 'wb') as f:
                            f.write(part.inline_data.data)
                        print(f"✓ Saved image to: {filepath}")
                        break
    
except Exception as e:
    print(f"✗ Gemini 3 Pro failed: {e}")
    import traceback
    traceback.print_exc()
