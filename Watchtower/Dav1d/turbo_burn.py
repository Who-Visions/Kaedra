#!/usr/bin/env python3
"""
TURBO BURN MODE - Gemini 3.0 Pro Exclusive
Burns credits faster using only the most expensive model
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai.types import GenerateContentConfig
from datetime import datetime
import time

PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def turbo_burn(target_spend: float = 5.0):
    """
    Burn credits using ONLY Gemini 3.0 Pro
    
    Args:
        target_spend: How much $ to burn (default: $5)
    """
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  🔥 TURBO BURN - Gemini 3.0 Pro Exclusive               ║
    ║  Target: ${target_spend:.2f}                                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Gemini 3.0 Pro cost: ~$0.014 per query (2000 output tokens)
    queries_needed = int(target_spend / 0.014)
    
    print(f"📊 Plan: {queries_needed} queries @ $0.014 each")
    print(f"⏱️  Estimated time: ~{queries_needed * 2 / 60:.1f} minutes\n")
    
    input("Press Enter to start... (Ctrl+C to cancel) ")
    
    prompts = [
        "Write a comprehensive 5000-word essay on the future of AI",
        "Analyze the complete history of computing in extreme detail",
        "Create a detailed business plan for a Fortune 500 AI company",
        "Explain quantum mechanics from first principles",
        "Write a complete guide to distributed systems architecture",
        "Analyze the philosophical implications of consciousness",
        "Create a comprehensive marketing strategy for enterprise SaaS",
        "Explain the entire software development lifecycle",
        "Write a research paper on human-computer interaction",
        "Analyze global economics and AI's impact on labor markets"
    ]
    
    total_spent = 0.0
    
    for i in range(queries_needed):
        try:
            prompt = prompts[i % len(prompts)]
            
            print(f"[{i+1}/{queries_needed}] {prompt[:50]}... ", end="", flush=True)
            
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=8192  # Max output = max cost
                )
            )
            
            cost = 0.014  # Rough estimate
            total_spent += cost
            
            print(f"✓ ${total_spent:.2f}")
            
            # Show progress every 10 queries
            if (i + 1) % 10 == 0:
                print(f"\n💰 Progress: ${total_spent:.2f} / ${target_spend:.2f} ({total_spent/target_spend*100:.1f}%)\n")
            
            time.sleep(1)  # Rate limit
            
            if total_spent >= target_spend:
                break
                
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(2)
            continue
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ TURBO BURN COMPLETE                                  ║
    ║  Spent: ${total_spent:.2f}                                          ║
    ║  Queries: {i+1}                                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Turbo burn credits with 3.0 Pro")
    parser.add_argument("--spend", type=float, default=5.0, help="Target spend ($)")
    
    args = parser.parse_args()
    
    try:
        turbo_burn(args.spend)
    except KeyboardInterrupt:
        print("\n\n⚠️  Burn cancelled")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
