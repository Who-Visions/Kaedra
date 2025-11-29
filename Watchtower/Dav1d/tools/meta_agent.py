"""
Meta Agent - The Tool Builder
Philosophy: Agents building Agents (Recursive AI)
Model: gemini-2.5-pro
"""

import os
import sys
import argparse
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def generate_tool_script(description: str) -> tuple[str, str, str]:
    """
    Generates a Python CLI tool script based on the description.
    Returns: (filename, code, explanation)
    """
    
    prompt = f"""You are an expert Python developer specializing in building self-contained CLI tools.
    
    TASK: Build a robust, single-file Python CLI script for the following requirement:
    "{description}"
    
    REQUIREMENTS:
    1. Use 'argparse' for CLI arguments.
    2. Be self-contained (minimal external dependencies, use standard library where possible).
    3. If external deps are needed, list them in a comment at the top (e.g., # pip install requests).
    4. Include a '__main__' block.
    5. Include concise docstrings.
    6. filename should be snake_case ending in .py (e.g., check_weather.py).
    
    RESPONSE FORMAT:
    return JSON only:
    {{
        "filename": "tool_name.py",
        "code": "... full python code ...",
        "description": "One sentence summary of what this tool does."
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )
    
    import json
    data = json.loads(response.text)
    return data["filename"], data["code"], data["description"]

def update_readme(filename: str, description: str):
    """Updates tools/README.md with the new tool."""
    readme_path = os.path.join("tools", "README.md")
    entry = f"\n### {filename}\n*   **Command:** `python tools/{filename}`\n*   **Description:** {description}\n"
    
    if os.path.exists(readme_path):
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        print("Warning: tools/README.md not found.")

def main():
    parser = argparse.ArgumentParser(description="Meta Agent: Build new tools using AI.")
    parser.add_argument("prompt", help="Description of the tool you want to build.")
    args = parser.parse_args()
    
    print(f"🤖 Meta Agent: Analyzing request '{args.prompt}'...")
    
    try:
        filename, code, desc = generate_tool_script(args.prompt)
        
        # Save to tools/ directory
        file_path = os.path.join("tools", filename)
        
        if os.path.exists(file_path):
            print(f"⚠️  Warning: {filename} already exists. Overwriting...")
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        print(f"✅ Successfully built: {file_path}")
        
        # Update Registry
        update_readme(filename, desc)
        print(f"📚 Updated Registry: tools/README.md")
        
        print("\nTo run your new tool:")
        print(f"python tools/{filename} --help")
        
    except Exception as e:
        print(f"❌ Error building tool: {e}")

if __name__ == "__main__":
    main()
