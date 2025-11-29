import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import GenerateImagesConfig

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# Test both Imagen 4 and Gemini 3 Pro Image
models_to_test = [
    ("Imagen 4", "imagen-4.0-generate-001"),
    ("Gemini 3 Pro Image", "gemini-3-pro-image-preview"),
]

simple_prompt = "A futuristic robot in a neon cityscape"

for name, model_id in models_to_test:
    print(f"\n{'='*60}")
    print(f"Testing: {name} ({model_id})")
    print(f"{'='*60}")
    
    try:
        response = client.models.generate_images(
            model=model_id,
            prompt=simple_prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                safety_filter_level="block_only_high"
            )
        )
        print(f"✓ SUCCESS!")
        print(f"  Images: {len(response.generated_images)}")
        print(f"  Size: {len(response.generated_images[0].image.image_bytes):,} bytes")
    except Exception as e:
        print(f"✗ FAILED: {str(e)[:200]}")
