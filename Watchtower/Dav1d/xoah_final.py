"""Test Xoah scene with working Imagen 4"""
import os, sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.getcwd())

# Reload to get latest
import importlib
if 'dav1d' in sys.modules:
    importlib.reload(sys.modules['dav1d'])
    
from dav1d import get_model, MODELS

prompt = """Xoah Lin Oda sprinting through the crowded night streets of Olympus Mons, third person wide shot. She is a Haitian and Japanese Martian woman in her late twenties, lean and athletic, mid brown skin, long dreadlocks whipping behind her as she runs. She wears a fitted black courier jacket with subtle glowing seams, tactical pants, light armor plates, no bulky cybernetics, gear looks practical and street worn, not shiny.

In her hand she clutches a small dark shard container at her chest. Behind her, several Syndicate enforcers push through the crowd, silhouettes with sleek masks and red visor strips, moving like trained hunters. A hovering drone searches above them with a harsh spotlight cutting through the scene.

Environment: Olympus mega city streets at ground level beneath a towering pyramid skyline, stacked bridges and platforms overhead. Neon shop signs in mixed Martian languages and kanji, cables and steam vents, Breath Stone vents glowing faint cyan in alley corners. Far above, the thin Martian sky glows faint red at the horizon.

Mood and style: tense chase, sense of danger and motion. Camera low and slightly behind Xoah, shallow depth of field, motion blur on her legs and background crowds, sharp focus on her face and the shard case. Lighting is cinematic, red and blue rim light from police style sirens, soft ambient neon reflections on wet pavement. Blend of ultra realistic 3D and anime cinematic style with Afro Samurai grit and subtle Ghost in the Shell influence. No text, no watermark. Wide frame, 16 by 9 composition."""

print("="*80)
print("🎨 XOAH LIN ODA - Imagen 4 Generation")
print("="*80)
print(f"\nPrompt: {len(prompt)} characters")
print("Model: Imagen 4 (imagen-4.0-generate-001)")
print("\n🎬 Generating epic chase scene...\n")

try:
    model = get_model(MODELS["vision"])
    response = model.generate_content(prompt)
    
    print("="*80)
    print("✅ GENERATION COMPLETE!")
    print("="*80)
    print(f"\n{response.text}\n")
    
    if hasattr(response, 'saved_paths') and response.saved_paths:
        for path in response.saved_paths:
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"📊 File size: {size:,} bytes ({size/1024/1024:.2f} MB)")
                print(f"📁 Full path: {path}")
                print(f"\n✓ Image successfully saved!")
                print(f"\n💡 Open with: explorer \"{os.path.dirname(path)}\"")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
