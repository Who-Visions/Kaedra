"""
Debug: Test with exact same code as working direct test
"""
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai.types import GenerateImagesConfig

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0285887798")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east4")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

prompt = "Xoah Lin Oda running through a futuristic city with neon lights, cinematic chase scene, Afro Samurai anime style"

print("Testing with Xoah prompt...")
try:
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=GenerateImagesConfig(
            number_of_images=1,
            safety_filter_level="block_only_high"
        )
    )
    print(f"✓ SUCCESS! Generated {len(response.generated_images)} image(s)")
    
    # Save it
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    images_dir = Path.cwd() / "images"
    images_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now(ZoneInfo("US/Eastern")).strftime("%Y%m%d_%H%M%S")
    filepath = images_dir / f"xoah_{timestamp}.png"
    response.generated_images[0].image.save(str(filepath))
    
    size = os.path.getsize(filepath)
    print(f"✓ Saved to: {filepath}")
    print(f"✓ Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
