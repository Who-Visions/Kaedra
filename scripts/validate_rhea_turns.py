
import sys
import os
import asyncio
import time
from typing import List

# Ensure we can import from local kaedra package
sys.path.append(os.getcwd())

from kaedra.story.components.co_writer import CoWriter

PROMPTS = [
    "1. Yo Rhea, check in.",
    "2. What is your primary directive?",
    "3. Brainstorm 3 sci-fi tropes.",
    "4. Critique: 'The cat sat on the mat.'",
    "5. Give me a plot twist for a mystery.",
    "6. How do you feel about Dav1d?",
    "7. What is the capital of Haiti?",
    "8. Define 'Ratchet Scholar'.",
    "9. Give me a fashion tip for a cyborg.",
    "10. Write a haiku about neon lights.",
    "11. analyzing potential plot holes...",
    "12. What music should I listen to while coding?",
    "13. Translate 'Hello' into Kreyol.",
    "14. What is your favorite emoji?",
    "15. Explain quantum entanglement simply.",
    "16. Give me a tough love productivity tip.",
    "17. Who built you?",
    "18. Describe your outfit.",
    "19. Are we syncing to BigQuery?",
    "20. Final vibe check before logout."
]

def run_validation():
    print("🚀 Starting 20-Turn Rhea Validation Suite...")
    cowriter = CoWriter()
    
    success_count = 0
    total_time = 0
    
    for i, prompt in enumerate(PROMPTS):
        print(f"\n[Turn {i+1}/20] Request: {prompt}")
        start = time.perf_counter()
        
        try:
            response = cowriter.consult(prompt)
            elapsed = time.perf_counter() - start
            total_time += elapsed
            
            if "[!]" in response:
                print(f"❌ FAILED: {response}")
            else:
                prefix = response[:100].replace("\n", " ") + "..."
                print(f"✅ SUCCESS ({elapsed:.2f}s): {prefix}")
                success_count += 1
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            
        # Mild delay to be nice to the API
        time.sleep(0.5)

    print("-" * 40)
    print(f"🏁 VALIDATION COMPLETE")
    print(f"Score: {success_count}/20")
    print(f"Avg Latency: {total_time/20:.2f}s")
    
    if success_count == 20:
        print("✨ PERFECT RUN")
    else:
        print("⚠️ SOME FAILURES DETECTED")

if __name__ == "__main__":
    run_validation()
