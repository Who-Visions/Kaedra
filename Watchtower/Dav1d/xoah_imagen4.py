"""
Test image save with Imagen 4 - Xoah Lin Oda scene
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.getcwd())
from dav1d import get_model, MODELS

prompt = """Xoah Lin Oda sprinting through the crowded night streets of Olympus Mons, third person wide shot. She is a Haitian and Japanese Martian woman in her late twenties, lean and athletic, mid brown skin, long dreadlocks whipping behind her as she runs. She wears a fitted black courier jacket with subtle glowing seams, tactical pants, light armor plates, no bulky cybernetics, gear looks practical and street worn, not shiny.

In her hand she clutches a small dark shard container at her chest. Behind her, several Syndicate enforcers push through the crowd, silhouettes with sleek masks and red visor strips, moving like trained hunters. A hovering drone searches above them with a harsh spotlight cutting through the scene.

Environment: Olympus mega city streets at ground level beneath a towering pyramid skyline, stacked bridges and platforms overhead. Neon shop signs in mixed Martian languages and kanji, cables and steam vents, Breath Stone vents glowing faint cyan in alley corners. Far above, the thin Martian sky glows faint red at the horizon.

Mood and style: tense chase, sense of danger and motion. Camera low and slightly behind Xoah, shallow depth of field, motion blur on her legs and background crowds, sharp focus on her face and the shard case. Lighting is cinematic, red and blue rim light from police style sirens, soft ambient neon reflections on wet pavement. Blend of ultra realistic 3D and anime cinematic style with Afro Samurai grit and subtle Ghost in the Shell influence. No text, no watermark. Wide frame, 16 by 9 composition."""

print("="*80)
print("🎨 DAV1D IMAGE SAVE TEST - Xoah Lin Oda")
print("="*80)
print(f"\n📝 Prompt: {len(prompt)} chars")
print(f"🎯 Model: Imagen 4 (vision)")
print("\n🎬 Generating...\n")

try:
    model = get_model(MODELS["vision"])
    response = model.generate_content(prompt)
    
    print("="*80)
    print("✅ SUCCESS!")
    print("="*80)
    print(f"\n{response.text}\n")
    
    if hasattr(response, 'saved_paths') and response.saved_paths:
        filepath  = response.saved_paths[0]
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✓ File verified: {size:,} bytes")
            print(f"✓ Location: {os.path.dirname(filepath)}")
            
            # List images directory
            images_dir = os.path.dirname(filepath)
            files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
            print(f"\n📂 Images directory contains {len(files)} file(s):")
            for f in sorted(files):
                print(f"  - {f}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
