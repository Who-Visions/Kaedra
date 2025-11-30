"""
Test image generation with save functionality - Xoah Lin Oda scene
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add current dir to path for imports
sys.path.insert(0, os.getcwd())

from dav1d import get_model, MODELS

prompt = """Xoah Lin Oda sprinting through the crowded night streets of Olympus Mons, third person wide shot. She is a Haitian and Japanese Martian woman in her late twenties, lean and athletic, mid brown skin, long dreadlocks whipping behind her as she runs. She wears a fitted black courier jacket with subtle glowing seams, tactical pants, light armor plates, no bulky cybernetics, gear looks practical and street worn, not shiny.

In her hand she clutches a small dark shard container at her chest. Behind her, several Syndicate enforcers push through the crowd, silhouettes with sleek masks and red visor strips, moving like trained hunters. A hovering drone searches above them with a harsh spotlight cutting through the scene.

Environment: Olympus mega city streets at ground level beneath a towering pyramid skyline, stacked bridges and platforms overhead. Neon shop signs in mixed Martian languages and kanji, cables and steam vents, Breath Stone vents glowing faint cyan in alley corners. Far above, the thin Martian sky glows faint red at the horizon.

Mood and style: tense chase, sense of danger and motion. Camera low and slightly behind Xoah, shallow depth of field, motion blur on her legs and background crowds, sharp focus on her face and the shard case. Lighting is cinematic, red and blue rim light from police style sirens, soft ambient neon reflections on wet pavement. Blend of ultra realistic 3D and anime cinematic style with Afro Samurai grit and subtle Ghost in the Shell influence. No text, no watermark. Wide frame, 16 by 9 composition."""

print("="*80)
print("🎨 DAV1D IMAGE GENERATION TEST - Xoah Lin Oda Scene")
print("="*80)
print(f"\n📝 Prompt length: {len(prompt)} characters")
print(f"🎯 Model: Gemini 3 Pro Image (vision_pro)")
print(f"💡 Reason: Complex cinematic prompt with anime/realistic blend\n")

try:
    # Use Gemini 3 Pro Image for this complex artistic prompt
    model_name = MODELS["vision_pro"]
    print(f"Initializing model: {model_name}")
    
    model = get_model(model_name)
    print("✓ Model initialized")
    
    print("\n🎬 Generating cinematic scene...")
    print("This may take 30-60 seconds for high-quality generation...\n")
    
    response = model.generate_content(prompt)
    
    print("="*80)
    print("✅ GENERATION COMPLETE!")
    print("="*80)
    
    if hasattr(response, 'saved_paths'):
        print(f"\n{response.text}\n")
        print(f"📊 Image size: {len(response.generated_images[0].image.image_bytes):,} bytes")
        print(f"📁 Saved to: {response.saved_paths[0]}")
        
        # Verify file exists
        import os
        if os.path.exists(response.saved_paths[0]):
            file_size = os.path.getsize(response.saved_paths[0])
            print(f"✓ File verified: {file_size:,} bytes on disk")
        else:
            print("⚠ Warning: File path reported but file not found")
    else:
        print(f"\n{response.text}")
        print("\n⚠ Note: Response doesn't have saved_paths attribute")
        print("This might be using generate_content instead of generate_images")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
