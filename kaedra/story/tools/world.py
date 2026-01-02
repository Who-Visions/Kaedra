"""
🌍 WorldForge Tool Wrapper
Exposes the WorldForge pipeline to the StoryEngine tool system.
"""
from kaedra.story.worldforge import WorldForge

def worldforge_from_youtube(video_id: str, ingest_path: str) -> str:
    """
    Reverse-engineers a World Bible from an ingested YouTube transcript.
    
    Args:
        video_id: The YouTube video ID (e.g., "ER5tlEolIjw")
        ingest_path: Absolute path to the ingested JSON file (from ingest_youtube output)
        
    Returns:
        Path to the generated 'world_bible.json'.
    """
    forge = WorldForge()
    try:
        result_path = forge.forge(video_id, ingest_path)
        if result_path.startswith("Error"):
            return f"[WORLDFORGE FAILED] {result_path}"
        return f"[WORLDFORGE SUCCESS] Bible created at: {result_path}"
    except Exception as e:
        return f"[WORLDFORGE ERROR] {str(e)}"
