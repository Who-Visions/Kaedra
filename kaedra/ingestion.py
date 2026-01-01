import os
import json
import logging
import re
import subprocess
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
from pathlib import Path

# Google Cloud Imports
from googleapiclient.discovery import build
try:
    from google.cloud import vision
    from google.cloud import videointelligence
    CLOUD_AVAILABLE = True
except ImportError:
    vision = None
    videointelligence = None
    CLOUD_AVAILABLE = False

from google import genai
from google.genai import types

# Setup Logger
log = logging.getLogger("ingestion")
log.setLevel(logging.INFO)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[INGEST] %(message)s'))
    log.addHandler(handler)

PROJECT_ID = os.getenv("PROJECT_ID", "who-visions")

class EvidencePacket(TypedDict):
    source: Dict[str, Any]
    text: Dict[str, Any]
    vision: Dict[str, Any]
    nlp: Dict[str, Any]
    engine_controls: Dict[str, Any]

class YTDLPIngester:
    """Primary ingestion using yt-dlp to bypass OAuth/API hurdles."""
    
    def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract metadata and subtitles using yt-dlp."""
        cmd = [
            "yt-dlp",
            "-J",                  # Dump JSON
            "--no-warnings",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", "en",
            url,
        ]
        try:
            log.info(f"Running yt-dlp for {url}...")
            # Use shell=True on Windows if needed, but list is safer
            out = subprocess.check_output(cmd, text=True, encoding="utf-8")
            data = json.loads(out)
            
            # Extract metadata
            meta = {
                "type": "youtube",
                "video_id": data.get("id"),
                "title": data.get("title"),
                "channel": data.get("uploader"),
                "published_at": data.get("upload_date"),
                "description": data.get("description"),
                "duration": data.get("duration"),
                "view_count": data.get("view_count")
            }
            
            # Extract transcript (best effort from subtitles field)
            transcript = "[No transcript found by yt-dlp]"
            # yt-dlp -J with --sub-lang en often puts subtitle info in requested_subtitles
            # For simplicity in this logic, we'll note that yt-dlp downloaded the files if they exist,
            # but for a pure JSON "Evidence Packet" we might need to read the .vtt files it generated.
            # However, for now we will mark availability.
            has_subs = len(data.get("requested_subtitles", {})) > 0
            
            return {
                "metadata": meta,
                "transcript_available": has_subs,
                "raw_data": data
            }
        except Exception as e:
            log.error(f"yt-dlp failed: {e}")
            return {"error": str(e)}

class YouTubeIngester:
    """Optional fallback using YouTube Data API v3 (Public Metadata Only)."""
    def __init__(self):
        # Use YOUTUBE_API_KEY specifically for YouTube to avoid 401/403 with Gemini key
        self.developer_key = os.environ.get("YOUTUBE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if self.developer_key:
             self.youtube = build("youtube", "v3", developerKey=self.developer_key, cache_discovery=False)
        else:
             self.youtube = None

    def get_metadata_fallback(self, video_id: str) -> Dict[str, Any]:
        if not self.youtube: return {}
        try:
            request = self.youtube.videos().list(part="snippet,contentDetails", id=video_id)
            response = request.execute()
            if not response["items"]: return {}
            item = response["items"][0]
            snippet = item["snippet"]
            return {
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "published_at": snippet["publishedAt"]
            }
        except Exception as e:
            log.warning(f"YouTube API Fallback failed: {e}")
            return {}

class VisualIngester:
    def __init__(self):
        self.enabled = False
        try:
            self.vision_client = vision.ImageAnnotatorClient()
            self.video_client = videointelligence.VideoIntelligenceServiceClient()
            self.enabled = True
        except Exception as e:
            log.warning(f"Google Cloud Vision/Video APIs unavailable: {e}")
            self.vision_client = None
            self.video_client = None

class NarrativeMapper:
    def __init__(self):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        self.model = "gemini-2.0-flash-exp"

    def analyze_packet(self, meta: dict, transcript: str) -> Dict[str, Any]:
        """Use Gemini to map source data into narrative beats."""
        # MVP: Return structured placeholder
        return {
            "entities": [meta.get("channel", "Unknown")], 
            "claims": [], 
            "beat_map": [{"beat": 1, "theme": "Introduction", "intensity": 0.3}]
        }

class IngestionManager:
    def __init__(self):
        self.ytdlp = YTDLPIngester()
        self.yt_api = YouTubeIngester()
        self.visual = VisualIngester()
        self.mapper = NarrativeMapper()

    def process_url(self, url: str) -> Dict[str, Any]:
        """Process URL and return EvidencePacket dict."""
        # 1. yt-dlp Extraction
        result = self.ytdlp.extract_info(url)
        if "error" in result:
             return {"error": result["error"]}
        
        meta = result["metadata"]
        vid = meta["video_id"]
        raw_data = result.get("raw_data", {})
        
        # 2. Cleanup Transcript (In a real impl, we'd read the .vtt files here)
        transcript = "[Transcript extraction placeholder]"
        if result["transcript_available"]:
             # Try to find transcript text in raw_data if mapped, otherwise note it
             transcript = raw_data.get("description", "")[:500] + "..." # Fallback to description snippet
        
        # 3. Create Packet
        packet: EvidencePacket = {
            "source": meta,
            "text": {
                "transcript": transcript,
                "captions_available": result["transcript_available"]
            },
            "vision": {"thumbnail_labels": [], "shot_segments": []},
            "nlp": self.mapper.analyze_packet(meta, transcript),
            "engine_controls": {"anchor_ratio_target": 0.5}
        }
        
        return {
            "packet": packet,
            "raw_data": raw_data,
            "metadata": meta,
            "video_id": vid
        }

def get_video_id(url: str) -> Optional[str]:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None
