"""
YouTube Transcript Ingestion Pipeline
Fetches transcripts from YouTube channels and pushes to Notion Ingestion Queue.

Usage:
    python tools/ingest_youtube.py --channel @TheWhyFiles --limit 5
    python tools/ingest_youtube.py --video "https://youtube.com/watch?v=..."
"""
import argparse
import json
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Add project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from google import genai
from google.genai import types
from tools.sync_notion import NotionBridge
from kaedra.core.config import PROJECT_ID
from kaedra.services.notion import retry_with_backoff

# Initialize Gemini via shared factory
from kaedra.core.config import get_gemini_client, MODELS
client = get_gemini_client()

# STT & Storage
from kaedra.services.storage_utils import upload_to_gcs, delete_from_gcs, blob_exists

STT_BUCKET = f"kaedra-ingestion-temp-{PROJECT_ID}"
NODE_PATH = r"C:\Program Files\nodejs\node.exe"

# Paths
CACHE_DIR = ROOT / "cache" / "youtube"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@retry_with_backoff(initial_delay=15.0)
def summarize_lore(transcript: str, title: str) -> str:
    """Use Gemini to summarize the transcript for Lorentz context."""
    print(f"   🧠 Analyzing lore context with Gemini...")
    
    # Truncate for summary if context is too huge, though Gemini handles 1M+
    # We'll send the first 100k chars for a quick summary
    sample = transcript[:100000]
    
    prompt = f"""
    [LORE ANALYST MODE]
    Analyze the following YouTube transcript: "{title}"
    
    Extract:
    1. **Key Entity**: Primary characters, organizations, or locations.
    2. **Universe Facts**: Lore rules, historical events, or cosmic laws mentioned.
    3. **Narrative Hooks**: Interesting plot points for a story engine.
    4. **Notion Metadata**: Suggest values for:
       - Status: New
       - Type: Intelligence
       - Universe Era: (Infer if possible)
       - Importance: (1-10)
    
    Format as a clean Markdown summary for a Notion page.
    
    TRANSCRIPT:
    {sample}
    """
    
    try:
        response = client.models.generate_content(
            model=MODELS.get("flash", "gemini-3-flash-preview"), # Fast and capable
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )
        return response.text or "Summary generation failed."
    except Exception as e:
        print(f"   ⚠️ Gemini summary failed: {e}")
        return "Lore summary unavailable."


def run_ytdlp(args: list, timeout: int = 120) -> str:
    """Run yt-dlp with common arguments and error handling."""
    base_args = [
        "yt-dlp",
        "--no-warn",
        "--js-runtime", NODE_PATH, # Fix JS runtime missing
        "--quiet"
    ]
    full_command = base_args + args
    try:
        cmd = full_command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            print(f"⚠️ yt-dlp error: {result.stderr[:200]}")
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"⏰ yt-dlp timed out after {timeout}s")
        return None
    except FileNotFoundError:
        print("❌ yt-dlp not found. Install with: pip install yt-dlp")
        return None
    except Exception as e:
        print(f"❌ yt-dlp failed: {e}")
        return None


def get_channel_videos(channel: str, limit: int = 5) -> List[Dict]:
    """Get recent video info from a channel."""
    print(f"📺 Fetching videos from {channel}...")
    
    # Get video list as JSON
    output = run_ytdlp([
        "--flat-playlist",
        "--playlist-end", str(limit),
        "--dump-json",
        f"https://www.youtube.com/{channel}/videos"
    ], timeout=60)
    
    if not output:
        return []
    
    videos = []
    for line in output.strip().split("\n"):
        if line.strip():
            try:
                data = json.loads(line)
                videos.append({
                    "id": data.get("id"),
                    "title": data.get("title", "Untitled"),
                    "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                    "duration": data.get("duration"),
                    "uploader": data.get("uploader", channel)
                })
            except json.JSONDecodeError:
                continue
    
    print(f"   Found {len(videos)} videos")
    return videos


def get_transcript(video_id: str, video_title: str) -> Optional[str]:
    """Download and extract transcript for a video."""
    print(f"   📝 Getting transcript: {video_title[:50]}...")
    
    # Check cache first
    cache_file = CACHE_DIR / f"{video_id}.txt"
    if cache_file.exists():
        print(f"   💾 Using cached transcript")
        return cache_file.read_text(encoding="utf-8")
    
    # Download auto-generated subtitles
    temp_dir = CACHE_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    output = run_ytdlp([
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--sub-format", "vtt",
        "-o", str(temp_dir / "%(id)s"),
        f"https://www.youtube.com/watch?v={video_id}"
    ], timeout=120)
    
    # Find downloaded subtitle file
    vtt_files = list(temp_dir.glob(f"{video_id}*.vtt"))
    if not vtt_files:
        print(f"    🧠 No subtitles found for {video_id}. Switching to Gemini 3 Multimodal...")
        transcript = transcribe_audio_multimodal(video_id, video_title)
        if transcript:
             # Cache STT result
             cache_file.write_text(transcript, encoding="utf-8")
             print(f"    ✅ Gemini 3 Transcript cached ({len(transcript)} chars)")
             return transcript
        return None
    
    # Parse VTT to plain text
    vtt_content = vtt_files[0].read_text(encoding="utf-8", errors="ignore")
    transcript = parse_vtt_to_text(vtt_content)
    
    # Cache it
    if transcript:
        cache_file.write_text(transcript, encoding="utf-8")
        print(f"   ✅ Transcript cached ({len(transcript)} chars)")
    
    # Cleanup temp
    for f in temp_dir.glob("*"):
        f.unlink()
    
    return transcript


def transcribe_audio_multimodal(video_id: str, video_title: str) -> Optional[str]:
    """Extract audio, upload to GCS (if needed), and transcribe via Gemini 3."""
    temp_audio = CACHE_DIR / f"{video_id}.wav"
    blob_name = f"ingestion/{video_id}.wav"
    gcs_uri = f"gs://{STT_BUCKET}/{blob_name}"

    # 1. Bucket Cooling: Check if file already exists in GCS
    if blob_exists(STT_BUCKET, blob_name):
        print(f"    ❄️ Found existing audio in bucket: {gcs_uri}. Skipping extraction/upload.")
    else:
        # 2. Extract audio using yt-dlp
        print(f"    🎙️ Extracting audio for Gemini 3...")
        run_ytdlp([
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "-o", str(CACHE_DIR / video_id),
            f"https://www.youtube.com/watch?v={video_id}"
        ], timeout=300)
        
        if not temp_audio.exists():
            print(f"    ❌ Audio extraction failed for {video_id}")
            return None

        # 3. Upload to GCS
        try:
            print(f"    ☁️ Uploading audio to GCS: {blob_name}")
            upload_to_gcs(str(temp_audio), STT_BUCKET, blob_name)
        except Exception as e:
            print(f"    ❌ GCS Upload failed: {e}")
            return None
        finally:
            if temp_audio.exists():
                temp_audio.unlink()

    # 4. Gemini 3 Multimodal Transcription
    try:
        print(f"    🧠 Sending audio to Gemini 3 Flash for transcription...")
        
        prompt = f"""
        TRANSCRIPTION AND LORE EXTRACTION TASK
        Video: {video_title}
        
        1. Please transcribe the audio precisely into clean text.
        2. Format the output with clear speaker markers if possible.
        3. Do not omit any narrative or world-building details.
        
        Keep the transcription as the primary output.
        """
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_uri(file_uri=gcs_uri, mime_type="audio/wav"),
                prompt
            ],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low")
            )
        )
        
        if not response.text:
            print(f"    ❌ Gemini 3 returned no text.")
            return None
            
        return response.text

    except Exception as e:
        print(f"    ❌ Gemini 3 Transcription failed: {e}")
        return None


def parse_vtt_to_text(vtt_content: str) -> str:
    """Convert VTT subtitle format to plain text."""
    lines = []
    skip_next = False
    
    for line in vtt_content.split("\n"):
        line = line.strip()
        
        # Skip header and timestamps
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            skip_next = False
            continue
        if not line or line.isdigit():
            continue
        
        # Remove VTT formatting tags
        import re
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"\[.*?\]", "", line)
        
        if line and line not in lines[-3:] if lines else True:  # Dedupe
            lines.append(line)
    
    return " ".join(lines)


def push_to_notion(video: Dict, transcript: str, world_id: str, ai_summary: Optional[str] = None) -> bool:
    """Push transcript and AI summary to Notion Ingestion Queue."""
    print(f"   📤 Pushing to Notion: {video['title'][:40]}...")
    
    try:
        import httpx
        import toml
        
        # Load Notion config
        config_path = ROOT / "kaedra" / "config" / "notion.toml"
        config = toml.load(config_path)
        token = config["notion"]["token"]
        
        # Get Ingestion Queue database ID
        db_id = config["databases"]["ingestion_queue"]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"
        }
        
        # Prepare Notion blocks (Split transcript into 2000-char chunks)
        # Notion limit: 2000 characters per block
        chunk_size = 1900 
        all_blocks = []
        for i in range(0, len(transcript), chunk_size):
            chunk = transcript[i:i + chunk_size]
            all_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": chunk}}]
                }
            })

        # Base blocks
        initial_blocks = [
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "🎬"},
                    "rich_text": [{"text": {"content": f"Source: {video['url']}"}}]
                }
            }
        ]

        # Add AI Summary if available
        if ai_summary:
            initial_blocks.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "🧠 AI Lore Briefing"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "color": "blue_background",
                        "icon": {"emoji": "📖"},
                        "rich_text": [{"text": {"content": ai_summary[:2000]}}] # Notion callout text limit
                    }
                }
            ])

        initial_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "📜 Full Transcript"}}]
            }
        })
        
        # Take first 80 chunks for the initial page creation to be safe
        first_batch = all_blocks[:80]
        remaining_blocks = all_blocks[80:]

        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": video["title"][:100]}}]
                },
                "Status": {
                    "select": {"name": "New"}
                },
                "Source URL": {
                    "url": video["url"]
                }
            },
            "children": initial_blocks + first_batch
        }
        
        with httpx.Client(timeout=30.0) as client_http:
            resp = client_http.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=payload
            )
        
        if resp.status_code != 200:
            print(f"   ❌ Notion error ({resp.status_code}): {resp.text}")
            return False
            
        result = resp.json()
        page_id = result.get('id')
        
        # Append remaining blocks in batches of 100
        if remaining_blocks and page_id:
            print(f"   ➕ Appending {len(remaining_blocks)} remaining blocks...")
            with httpx.Client(timeout=30.0) as client_http:
                for i in range(0, len(remaining_blocks), 100):
                    batch = remaining_blocks[i:i + 100]
                    append_resp = client_http.patch(
                        f"https://api.notion.com/v1/blocks/{page_id}/children",
                        headers=headers,
                        json={"children": batch}
                    )
                if append_resp.status_code != 200:
                    print(f"   ⚠️ Append error ({append_resp.status_code}): {append_resp.text}")
        
        print(f"   ✅ Created: {result.get('url', 'URL not found')}")
        return True
        
    except Exception as e:
        print(f"   ❌ Notion push failed: {e}")
        return False


def ingest_channel(channel: str, limit: int, world_id: str):
    """Full pipeline: channel → transcripts → Notion."""
    print("=" * 60)
    print(f"YouTube Ingestion Pipeline")
    print(f"Channel: {channel}")
    print(f"Limit: {limit} videos")
    print("=" * 60)
    
    # Get video list
    videos = get_channel_videos(channel, limit)
    if not videos:
        print("❌ No videos found")
        return
    
    # Process each video
    success = 0
    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {video['title'][:50]}...")
        
        # Get transcript
        transcript = get_transcript(video["id"], video["title"])
        if not transcript:
            continue
            
        # AI Summary
        ai_summary = summarize_lore(transcript, video["title"])
        
        # Push to Notion
        if push_to_notion(video, transcript, world_id, ai_summary=ai_summary):
            success += 1
        
        # Rate limit
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print(f"✅ Ingested {success}/{len(videos)} videos to Notion")


def ingest_single_video(url: str, world_id: str):
    """Ingest a single video by URL."""
    print(f"📺 Ingesting: {url}")
    
    # Extract video ID
    import re
    match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
    if not match:
        print("❌ Invalid YouTube URL")
        return
    
    video_id = match.group(1)
    
    # Get video info
    output = run_ytdlp([
        "--dump-json",
        "--no-playlist",
        url
    ], timeout=30)
    
    if not output:
        return
    
    data = json.loads(output)
    video = {
        "id": video_id,
        "title": data.get("title", "Untitled"),
        "url": url,
        "uploader": data.get("uploader", "Unknown")
    }
    
    # Get transcript
    transcript = get_transcript(video_id, video["title"])
    if not transcript:
        return
        
    # AI Summary
    ai_summary = summarize_lore(transcript, video["title"])
    
    # Push to Notion
    push_to_notion(video, transcript, world_id, ai_summary=ai_summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Transcript Ingestion")
    parser.add_argument("--channel", type=str, help="YouTube channel handle (e.g., @TheWhyFiles)")
    parser.add_argument("--video", type=str, help="Single video URL")
    parser.add_argument("--limit", type=int, default=5, help="Max videos to ingest")
    parser.add_argument("--world", type=str, default="world_bee9d6ac", help="World ID")
    
    args = parser.parse_args()
    
    if args.video:
        ingest_single_video(args.video, args.world)
    elif args.channel:
        ingest_channel(args.channel, args.limit, args.world)
    else:
        print("Usage:")
        print("  python tools/ingest_youtube.py --channel @TheWhyFiles --limit 5")
        print("  python tools/ingest_youtube.py --video 'https://youtube.com/watch?v=...'")
