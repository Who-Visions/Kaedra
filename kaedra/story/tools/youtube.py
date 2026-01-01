"""
StoryEngine YouTube Tools
Ingest YouTube content and save evidence packets.
"""
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

from kaedra.ingestion import IngestionManager


def extract_youtube_id(url: str) -> str:
    """Tries to extract a stable video id from common YouTube URL formats. Falls back to a short hash if no id found."""
    if not url: 
        return "unknown"
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/live/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m: 
            return m.group(1)
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def safe_slug(s: str, max_len: int = 60) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    return (s[:max_len] or "untitled").strip("_")


def ensure_dict_result(result: Any) -> Dict[str, Any]:
    """Normalizes IngestionManager result into a dict."""
    if isinstance(result, dict): 
        return result
    if isinstance(result, str):
        txt = result.strip()
        if (txt.startswith("{") and txt.endswith("}")) or (txt.startswith("[") and txt.endswith("]")):
            try: 
                return json.loads(txt)
            except Exception: 
                return {"raw_text": result}
        return {"raw_text": result}
    return {"raw": str(result)}


def save_youtube_evidence_packet(packet: Dict[str, Any], url: str, out_root: str = "exports/youtube") -> Dict[str, str]:
    """Writes JSON packet and MD brief to disk. (v7.5)"""
    video_id = extract_youtube_id(url)
    now = datetime.now()
    day_dir = Path(out_root) / now.strftime("%Y%m%d")
    day_dir.mkdir(parents=True, exist_ok=True)

    title = ""
    # Try common fields from IngestionManager or raw
    meta = packet.get("metadata") or packet.get("source") or {}
    if isinstance(meta, dict): 
        title = meta.get("title") or ""

    slug = safe_slug(title) if title else "video"
    base = f"{video_id}_{slug}_{now.strftime('%H%M%S')}"

    json_path = day_dir / f"{base}.json"
    md_path = day_dir / f"{base}.md"

    packet_out = {
        "source_url": url,
        "video_id": video_id,
        "ingested_at": now.isoformat(),
        "data": packet,
    }

    json_path.write_text(json.dumps(packet_out, indent=2, ensure_ascii=False), encoding="utf-8")

    # MD Brief
    transcript = packet.get("text", {}).get("transcript", "") if isinstance(packet.get("text"), dict) else ""
    md = [
        f"# YouTube Evidence Packet",
        f"",
        f"**Title:** {title or '(unknown)'}",
        f"**Video ID:** {video_id}",
        f"**Source:** {url}",
        f"**Ingested:** {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Persistence",
        f"- JSON: `{json_path}`",
        f"- MD: `{md_path}`",
        f""
    ]
    if transcript:
        md.append("## Transcript Excerpt")
        md.append("")
        md.append(transcript[:2000] + ("..." if len(transcript) > 2000 else ""))

    md_path.write_text("\n".join(md), encoding="utf-8")
    return {"json_path": str(json_path), "md_path": str(md_path)}


def ingest_youtube_content(url: str) -> str:
    """Ingest a YouTube video and auto-save Evidence Packet (JSON + MD Brief)."""
    try:
        manager = IngestionManager()
        result = manager.process_url(url)
        packet = ensure_dict_result(result)
        saved = save_youtube_evidence_packet(packet, url)
        return (
            "[INGEST OK]\n"
            f"Saved JSON: {saved['json_path']}\n"
            f"Saved MD: {saved['md_path']}\n"
        )
    except Exception as e:
        return f"[Ingestion Failed: {e}]"
