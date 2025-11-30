"""
Evolution Tool - The Self-Improver
Reads session logs and updates the core persona (dav1d.txt) to reflect user feedback.
"""

import os
import sys
import argparse
import glob
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

PROFILE_PATH = os.path.join(os.path.expanduser("~"), ".dav1d", "resources", "profiles", "dav1d.txt")
LOGS_DIR = os.path.join(os.path.expanduser("~"), ".dav1d", "chat_logs")

def get_latest_log():
    """Finds the most recent session log."""
    list_of_files = glob.glob(os.path.join(LOGS_DIR, "*.md"))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)

def evolve_profile(log_path: str):
    """Analyzes log and updates profile."""
    print(f"🧬 Evolving based on: {log_path}")
    
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
        
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        current_profile = f.read()
        
    prompt = f"""You are an expert AI architect. Your job is to EVOLVE an AI agent's system prompt based on recent user interactions.

CURRENT PROFILE:
{current_profile}

RECENT SESSION LOG:
{log_content[-10000:]}  # Last 10k chars

TASK:
1. Analyze the log for:
   - Explicit user corrections (e.g., "Don't do X", "I want Y").
   - Implicit preferences (e.g., User ignored long explanations, preferred short ones).
   - Missed opportunities (Agent failed to use a tool or perspective).
2. Rewrite the CURRENT PROFILE to permanently incorporate these lessons.
3. Keep the structure (IDENTITY, PERSONALITY, etc.) but refine the content.
4. Be specific. If the user hates emojis, add "NO EMOJIS" to directives.

OUTPUT:
Return ONLY the new, full profile text. Do not add markdown code blocks around it.
"""

    print("🧠 Analyzing interaction patterns...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
            )
        )
        
        new_profile = response.text.strip()
        
        # Basic validation to ensure we didn't get a blank or error
        if len(new_profile) < 100 or "Error" in new_profile:
            print("❌ Evolution failed: Invalid response from model.")
            return

        # Backup old profile
        backup_path = PROFILE_PATH + ".bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(current_profile)
            
        # Write new profile
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            f.write(new_profile)
            
        print("✅ Profile Evolved! Changes saved to resources/profiles/dav1d.txt")
        print(f"   (Backup saved to {backup_path})")
        
    except Exception as e:
        print(f"❌ Evolution failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Evolve Dav1d's persona based on logs.")
    parser.add_argument("--log", "-l", help="Specific log file to analyze")
    args = parser.parse_args()
    
    target_log = args.log if args.log else get_latest_log()
    
    if not target_log:
        print("❌ No session logs found.")
        return
        
    evolve_profile(target_log)

if __name__ == "__main__":
    main()
