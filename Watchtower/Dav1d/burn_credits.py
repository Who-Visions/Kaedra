#!/usr/bin/env python3
"""
AGGRESSIVE CREDIT BURNER
Burns through your $50 Gemini trial credit before December 22, 2025

Run this daily to maximize credit usage.
Target: $2.08/day × 24 days = $50
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai.types import GenerateContentConfig

PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

class CreditBurner:
    """Systematically burns GCP credits using premium APIs"""
    
    def __init__(self):
        self.total_spent = 0.0
        self.session_log = []
        
    def log(self, activity, cost):
        """Log activity and cost"""
        self.total_spent += cost
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {activity}: ${cost:.3f}"
        self.session_log.append(entry)
        print(f"💰 {entry} | Total: ${self.total_spent:.2f}")
    
    def burn_with_gemini_pro(self, count=10):
        """Use expensive Gemini 3.0 Pro model
        Cost: ~$0.014 per query
        """
        print(f"\n🧠 BURNING CREDITS: Gemini 3.0 Pro ({count} queries)")
        
        prompts = [
            "Write a comprehensive 5000-word business plan for scaling an AI startup",
            "Analyze the entire history of computer science and explain key innovations",
            "Create a detailed technical specification for a multi-agent AI system",
            "Explain quantum computing to a 5-year-old, then to a PhD physicist",
            "Write a complete guide to building serverless applications on GCP",
            "Analyze the philosophical implications of artificial general intelligence",
            "Create a detailed marketing strategy for a B2B SaaS product",
            "Explain the complete software development lifecycle with examples",
            "Write a research paper on the future of human-computer interaction",
            "Analyze the economic impact of AI on the labor market"
        ]
        
        for i in range(count):
            try:
                prompt = prompts[i % len(prompts)]
                print(f"  Query {i+1}/{count}: {prompt[:60]}...")
                
                response = client.models.generate_content(
                    model="gemini-3-pro-preview",
                    contents=prompt,
                    config=GenerateContentConfig(
                        temperature=1.0,
                        max_output_tokens=8192  # Force max output
                    )
                )
                
                # Estimate cost: $2/M input + $12/M output
                # Rough estimate: 50 tokens in, 2000 tokens out
                cost = (50 * 2 / 1_000_000) + (2000 * 12 / 1_000_000)
                self.log(f"Gemini 3.0 Pro query {i+1}", cost)
                
                time.sleep(1)  # Rate limit
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
    
    def burn_with_imagen(self, count=20):
        """Generate images with Imagen
        Cost: ~$0.04 per image
        """
        print(f"\n🎨 BURNING CREDITS: Imagen 4 ({count} images)")
        
        prompts = [
            "A cyberpunk cityscape at night with neon lights",
            "A futuristic AI robot in a modern office",
            "Abstract digital art representing artificial intelligence",
            "A professional headshot of a tech entrepreneur",
            "A minimalist logo design for an AI startup",
            "A modern web application interface mockup",
            "A sleek dashboard with data visualizations",
            "A futuristic command center with holographic displays",
            "An elegant business card design",
            "A vibrant social media banner for tech company",
            "A professional presentation slide template",
            "A modern mobile app interface",
            "An isometric illustration of cloud infrastructure",
            "A retro-futuristic poster design",
            "A minimalist icon set for productivity app"
        ]
        
        for i in range(count):
            try:
                prompt = prompts[i % len(prompts)]
                print(f"  Image {i+1}/{count}: {prompt[:50]}...")
                
                from google.genai.types import GenerateImagesConfig
                
                response = client.models.generate_images(
                    model="imagen-4.0-generate-001",
                    prompt=prompt,
                    config=GenerateImagesConfig(
                        number_of_images=1,
                        safety_filter_level="block_only_high"
                    )
                )
                
                # Save image
                images_dir = Path("credit_burner_images")
                images_dir.mkdir(exist_ok=True)
                
                for idx, img in enumerate(response.generated_images):
                    filename = f"burn_{i+1}_{idx+1}.png"
                    img.image.save(images_dir / filename)
                
                cost = 0.04  # $0.04 per image
                self.log(f"Imagen generation {i+1}", cost)
                
                time.sleep(2)  # Rate limit
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                # If quota hit, wait longer
                if "RESOURCE_EXHAUSTED" in str(e):
                    print("  ⏳ Quota hit, cooling down 70s...")
                    time.sleep(70)
                continue
    
    def burn_with_flash_high_volume(self, count=100):
        """Use Flash model at high volume
        Cost: ~$0.0019 per query × 100 = $0.19
        """
        print(f"\n⚡ BURNING CREDITS: Gemini 2.5 Flash high-volume ({count} queries)")
        
        for i in range(count):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Write a detailed explanation of topic number {i}",
                    config=GenerateContentConfig(
                        max_output_tokens=2048
                    )
                )
                
                if i % 10 == 0:
                    cost = 0.0019 * 10
                    self.log(f"Flash batch ({i-9}-{i})", cost)
                
            except Exception as e:
                print(f"  ❌ Error at {i}: {e}")
                continue
    
    def burn_with_grounding(self, count=20):
        """Use Vertex AI Grounding (expensive!)
        Cost: ~$0.035 per search = $0.70 for 20
        """
        print(f"\n🔍 BURNING CREDITS: Vertex AI Grounding ({count} searches)")
        
        from google.genai.types import Tool, GoogleSearch
        
        queries = [
            "Latest AI news and developments",
            "Best practices for cloud architecture",
            "How to scale a SaaS business",
            "Machine learning trends 2025",
            "Startup funding strategies",
            "Enterprise AI adoption",
            "Cloud cost optimization techniques",
            "AI ethics and regulation",
            "DevOps best practices",
            "Product management frameworks"
        ]
        
        for i in range(count):
            try:
                query = queries[i % len(queries)] + f" (search {i+1})"
                print(f"  Search {i+1}/{count}: {query[:50]}...")
                
                chat = client.chats.create(
                    model="gemini-2.5-pro",
                    config=GenerateContentConfig(
                        tools=[Tool(google_search=GoogleSearch())],
                        temperature=0.7
                    )
                )
                
                response = chat.send_message(f"Search the web and summarize: {query}")
                
                cost = 0.035  # $35 per 1000 queries
                self.log(f"Grounding search {i+1}", cost)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
    
    def daily_burn_routine(self):
        """Complete daily routine to burn ~$2/day"""
        print("\n" + "="*70)
        print("🔥 DAILY CREDIT BURN ROUTINE")
        print("="*70)
        print(f"Target: $2.08/day to use $50 in 24 days")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Mix of expensive operations
        self.burn_with_imagen(count=15)          # $0.60
        self.burn_with_gemini_pro(count=5)       # $0.70
        self.burn_with_grounding(count=15)       # $0.53
        self.burn_with_flash_high_volume(count=50)  # $0.10
        
        # Add more Pro queries to hit target
        self.burn_with_gemini_pro(count=2)       # $0.28
        
        print("\n" + "="*70)
        print(f"✅ DAILY ROUTINE COMPLETE")
        print(f"Total spent this session: ${self.total_spent:.2f}")
        print(f"Target: $2.08/day")
        print(f"Variance: ${self.total_spent - 2.08:+.2f}")
        print("="*70)
        
        # Save log
        log_dir = Path("credit_burn_logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"burn_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(log_file, 'w') as f:
            f.write(f"Credit Burn Session - {datetime.now()}\n")
            f.write("="*70 + "\n\n")
            for entry in self.session_log:
                f.write(entry + "\n")
            f.write(f"\nTotal: ${self.total_spent:.2f}\n")
        
        print(f"\n📝 Log saved to: {log_file}")


def main():
    """Main execution"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  💰 AGGRESSIVE CREDIT BURNER 💰                              ║
    ║                                                              ║
    ║  Target: Use $50 in 24 days before December 22, 2025        ║
    ║  Strategy: $2.08/day via expensive API calls                ║
    ║                                                              ║
    ║  This script will:                                           ║
    ║  • Generate 15 images with Imagen ($0.60)                   ║
    ║  • Run 7 Gemini 3.0 Pro queries ($0.98)                     ║
    ║  • Execute 15 web searches ($0.53)                           ║
    ║  • Blast 50 Flash queries ($0.10)                            ║
    ║  ≈ $2.21/day                                                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start burning credits... (Ctrl+C to cancel) ")
    
    burner = CreditBurner()
    burner.daily_burn_routine()
    
    print("\n🎉 Run this script DAILY to hit your $50 target!")
    print("💡 Tip: Set up a cron job or Task Scheduler to automate this.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Credit burning interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
