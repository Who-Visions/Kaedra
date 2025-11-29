#!/usr/bin/env python3
"""
DAV1D API Configuration Setup
Quick script to configure all API keys
"""

import os
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
ENV_EXAMPLE = Path(__file__).parent / ".env.example"

def setup_api_keys():
    """Interactive setup for API keys"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  DAV1D API Configuration Setup                                ║
    ║  Configure your API keys for YouTube, Maps, and more         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if .env exists
    if ENV_FILE.exists():
        response = input("\n⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled. Edit .env manually.")
            return
    
    # Copy from .env.example
    if ENV_EXAMPLE.exists():
        with open(ENV_EXAMPLE, 'r') as f:
            env_content = f.read()
    else:
        print("❌ .env.example not found!")
        return
    
    print("\n📝 Let's configure your API keys...")
    print("(Press Enter to skip any key)\n")
    
    # API Key 1 - From the screenshot
    print("=" * 60)
    print("1️⃣  GOOGLE_API_KEY (Vertex AI / Gemini)")
    print("   You just created this: AIzaB8RN6LQSVdpjnglSqGkC1G3HmiVPa4IpW1NDJmg...")
    google_api_key = input("   Paste your full API key: ").strip()
    
    if google_api_key:
        env_content = env_content.replace("GOOGLE_API_KEY=your_api_key_here", 
                                         f"GOOGLE_API_KEY={google_api_key}")
    
    # YouTube API Key
    print("\n" + "=" * 60)
    print("2️⃣  YOUTUBE_API_KEY")
    print("   Get from: https://console.cloud.google.com/apis/credentials")
    print("   Enable: https://console.cloud.google.com/apis/library/youtube.googleapis.com")
    youtube_key = input("   API Key (or Enter to skip): ").strip()
    
    if youtube_key:
        env_content = env_content.replace("YOUTUBE_API_KEY=your_youtube_api_key_here",
                                         f"YOUTUBE_API_KEY={youtube_key}")
    
    # Maps API Key
    print("\n" + "=" * 60)
    print("3️⃣  GOOGLE_MAPS_API_KEY")
    print("   Get from: https://console.cloud.google.com/google/maps-apis/credentials")
    print("   Enable: Geocoding, Places, Directions, Distance Matrix APIs")
    maps_key = input("   API Key (or Enter to skip): ").strip()
    
    if maps_key:
        env_content = env_content.replace("GOOGLE_MAPS_API_KEY=your_maps_api_key_here",
                                         f"GOOGLE_MAPS_API_KEY={maps_key}")
    
    # Save .env file
    with open(ENV_FILE, 'w') as f:
        f.write(env_content)
    
    print("\n" + "=" * 60)
    print("✅ Configuration saved to .env")
    print("\n📋 Next steps:")
    print("   1. Install dependencies: pip install -r requirements.txt")
    print("   2. Test the setup: python burn_credits.py")
    print("   3. Run Dav1d: python dav1d.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        setup_api_keys()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
