"""
Sort Shadow Dweller Assets using Gemini Vision (Flash).
Classifies images into concept folders based on visual content.
"""
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Config
load_dotenv()
IMAGE_DIR = Path(r"C:\Users\super\Watchtower\Shadow Dweller\Shadow Dweller")
BATCH_LIMIT = 50  # Safety limit for first run
MODEL_ID = "gemini-3-flash-preview"

console = Console()

CATEGORIES = [
    "Minitor",
    "Sentinels",
    "Veil",
    "Cyberpunk City",
    "Abstract",
    "Character Portrait",
    "Tech Interface",
    "Other"
]

def get_classification(client, image_path):
    """Ask Gemini to classify the image (with retry)."""
    backoff = 10
    for attempt in range(5):
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            prompt = f"""
            Analyze this image and classify it into EXACTLY ONE of these categories:
            {', '.join(CATEGORIES)}
            
            Return ONLY the category name. Nothing else.
            """
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type="image/png")]
            )
            return response.text.strip()
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                console.print(f"[yellow]Rate limit hit. Sleeping {backoff}s...[/]")
                time.sleep(backoff)
                backoff *= 2
            else:
                console.print(f"[red]Error classifying {image_path.name}: {e}[/]")
                return None
    return None

def main():
    if not IMAGE_DIR.exists():
        console.print(f"[red]Directory not found: {IMAGE_DIR}[/]")
        return

    # Initialize Client
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        console.print("[green]Gemini Client Initialized[/]")
    except Exception as e:
        console.print(f"[red]Failed to init client: {e}[/]")
        return

    # Create Category Folders
    for cat in CATEGORIES:
        (IMAGE_DIR / cat).mkdir(exist_ok=True)

    # Scan Files
    files = list(IMAGE_DIR.glob("*.png"))
    # Filter out files already in subfolders (glob is recursive? No, but check parent)
    files = [f for f in files if f.parent == IMAGE_DIR]
    
    console.print(f"Found {len(files)} images in root. Processing first {BATCH_LIMIT} with throttling...")
    
    processed = 0
    for image_file in files[:BATCH_LIMIT]:
        category = get_classification(client, image_file)
        
        if category:
            # Clean response just in case
            category = category.replace("*", "").strip()
            if category not in CATEGORIES:
                # Fallback if model hallucinates a new category
                console.print(f"[yellow]Model returned '{category}', defaulting to 'Other'[/]")
                category = "Other"
            
            # Get original date metadata (Creation time on Windows, or Modification time)
            timestamp = image_file.stat().st_mtime
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            # Construct new filename: YYYY-MM-DD_Originalname
            new_filename = f"{date_str}_{image_file.name}"
            
            console.print(f"[cyan]{image_file.name}[/] -> [bold magenta]{category}/{new_filename}[/]")
            
            # Move file and rename
            target_path = IMAGE_DIR / category / new_filename
            shutil.move(str(image_file), str(target_path))
            processed += 1
            
            # Rate limit politeness (Base 7s for 10 RPM safety)
            time.sleep(7) 
            
    console.print(f"[green]Sorted {processed} images successfully.[/]")

if __name__ == "__main__":
    main()
