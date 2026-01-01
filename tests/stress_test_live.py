
import asyncio
import logging
import random
import sys
import time
from pathlib import Path

# Adjust path to import universe_text from parent
sys.path.append(str(Path(__file__).parent.parent))

from universe_text import StoryEngine, Mode

# Configure minimal logging to see errors clearly
logging.basicConfig(level=logging.ERROR)
log = logging.getLogger("stress_test")

# 100 Diverse Prompts
PROMPTS = []

# 1. Perception & Environment (20)
locations = ["the shadows", "the ancient ruin", "the cyber-deck", "the neon skyline", "the rusted door", "the holographic emitter", "the data stream", "the void", "the mirror", "the cockpit"]
actions = ["Look at", "Scan", "Touch", "Listen to", "Smell", "Investigate", "Analyze"]
for _ in range(20):
    PROMPTS.append(f"{random.choice(actions)} {random.choice(locations)} and describe the details.")

# 2. Lore & Knowledge (20) (Triggers read_local_lore)
topics = ["Mars", "The Veil", "Shadows", "The Ancients", "Cybernetics", "The War", "Glitch City", "Project KAEDRA", "The Signal", "Red Dust"]
for _ in range(20):
    PROMPTS.append(f"Check the local lore about {random.choice(topics)}.")

# 3. Emotional & Status Updates (20) (Triggers adjust_emotion)
emotions = ["fear", "hope", "desire", "rage"]
intensities = ["a little", "a lot", "massively", "slightly", "overwhelmingly"]
for _ in range(20):
    PROMPTS.append(f"I am feeling {random.choice(intensities)} {random.choice(emotions)}. Update the simulation state.")

# 4. Director & Meta (20) (Triggers consult_director, set_engine_mode)
for _ in range(10):
    PROMPTS.append("Consult the director: What should happen next in this scene?")
for _ in range(10):
    PROMPTS.append("Director, clarify the themes of this story.")

# 5. Complex/Multi-Step (20) (Triggers Sequential Tool Calls)
for _ in range(20):
    topic = random.choice(topics)
    loc = random.choice(locations)
    PROMPTS.append(f"First check the lore about {topic}, then scan {loc} to see if it Matches.")

random.shuffle(PROMPTS)

async def run_stress_test():
    print(f"🚀 STARTING LIVE STRESS TEST: {len(PROMPTS)} Turns")
    print("WARNING: This makes REAL API calls.")
    
    engine = StoryEngine()
    # Disable full console print to reduce noise, but keep criticals
    # engine.console.quiet = True 
    
    failures = []
    
    start_time = time.time()
    
    for i, prompt in enumerate(PROMPTS):
        print(f"\n[{i+1}/{len(PROMPTS)}] USER > {prompt}")
        turn_start = time.time()
        try:
            # We don't need the return value, just checking for exceptions
            await engine.generate_response(prompt)
            duration = time.time() - turn_start
            print(f"✅ PASS ({duration:.2f}s)")
            
            # Anti-Rate Limit (Smart Pause)
            await asyncio.sleep(2) 
            
        except Exception as e:
            print(f"❌ FAIL: {e}")
            failures.append({
                "turn": i+1,
                "prompt": prompt,
                "error": str(e)
            })
            # If critical 400 error, breaks usually happen here
            if "400" in str(e):
                print("🚨 CRITICAL 400 ERROR DETECTED - ABORTING TO ANALYZE")
                break
                
    total_time = time.time() - start_time
    print(f"\n\n📊 RESULTS: {len(PROMPTS) - len(failures)}/{len(PROMPTS)} Passed")
    print(f"⏱ Total Time: {total_time:.2f}s")
    
    if failures:
        print("\n🛑 FAILURES:")
        for f in failures:
            print(f"Turn {f['turn']}: {f['error']} | Prompt: {f['prompt']}")
        sys.exit(1)
    else:
        print("\n✨ ALL 100 TURNS PASSED. SYSTEM ROBUST.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        pass
