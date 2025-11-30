"""Final test of both image models with save - Xoah Lin Oda"""
import os, sys
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.getcwd())

# Force reload to get latest code changes
import importlib
if 'dav1d' in sys.modules:
    importlib.reload(sys.modules['dav1d'])
from dav1d import get_model, MODELS

prompt = """Xoah Lin Oda sprinting through crowded night streets of Olympus Mons, third person wide shot. Haitian and Japanese Martian woman, late twenties, athletic, mid brown skin, long dreadlocks flowing. Black courier jacket with glowing seams, tactical pants, light armor. She clutches a dark shard container. Behind her, Syndicate enforcers with red visor masks pursue through crowds. Drone spotlight searches above. Mega city streets, pyramid skyline, neon signs, cables, cyan Breath Stone vents. Red Martian sky. Tense chase, motion blur, cinematic lighting with red and blue rim lights, wet pavement reflections. Afro Samurai meets Ghost in the Shell style. 16:9 wide frame."""

models_to_test = [
    ("Imagen 4", "vision"),
    ("Gemini 3 Pro Image", "vision_pro")
]

for name, tier in models_to_test:
    print(f"\n{'='*80}")
    print(f"🎨 Testing: {name} ({tier})")
    print(f"{'='*80}\n")
    
    try:
        model = get_model(MODELS[tier])
        print(f"Generating with {MODELS[tier]}...")
        
        response = model.generate_content(prompt)
        
        print(f"\n✅ SUCCESS!\n")
        print(response.text)
        
        if hasattr(response, 'saved_paths') and response.saved_paths:
            for path in response.saved_paths:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"\n✓ Verified: {os.path.basename(path)} ({size:,} bytes)")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}\n")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print("✅ Test Complete - Check c:/Users/super/Watchtower/Dav1d/dav1d brain/images/")
print(f"{'='*80}")
