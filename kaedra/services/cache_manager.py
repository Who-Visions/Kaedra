"""
🧠 LoreCacheManager - Gemini Context Caching
Caches large World Bible contexts to reduce latency and cost.
Pattern: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Caching.ipynb
"""
import hashlib
from typing import Optional
from google.genai import types
from kaedra.core.config import get_gemini_client
from kaedra.story.config import FLASH_MODEL
from kaedra.story.ui import log

class LoreCacheManager:
    """Manages Gemini Context Caches for World Bibles."""
    
    def __init__(self, model: str = FLASH_MODEL):
        self.client = get_gemini_client()
        self.model = model
        self._cache_map = {} # Cache name by bible hash

    def _get_bible_hash(self, content: str) -> str:
        """Generate a stable hash for the bible content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get_or_create_cache(self, content: str, system_instruction: str, 
                            ttl_seconds: int = 3600) -> Optional[str]:
        """
        Returns a cache name for the given content. 
        Creates a new one if it doesn't exist or is expired.
        """
        bible_hash = self._get_bible_hash(content + system_instruction)
        
        # Check active caches
        try:
            active_caches = list(self.client.caches.list())
            for cache in active_caches:
                # We store the hash in the display_name or metadata if possible
                # For now, let's use display_name for simplicity in discovery
                if cache.display_name == f"lore_cache_{bible_hash[:16]}":
                    log.info("Using existing context cache: %s", cache.name)
                    return cache.name
        except Exception as e: # pylint: disable=broad-exception-caught
            log.warning("Failed to list caches: %s", e)

        # Create new cache
        log.info("Creating new context cache for %d chars...", len(content))
        try:
            # Note: Content must be at least 32,768 tokens for caching to be beneficial/allowed on some models
            # but we'll try anyway or handle the error
            cache_config = types.CreateCachedContentConfig(
                display_name=f"lore_cache_{bible_hash[:16]}",
                contents=[types.Content(role="user", parts=[types.Part(text=content)])],
                system_instruction=system_instruction,
                ttl=f"{ttl_seconds}s",
            )
            new_cache = self.client.caches.create(
                model=self.model,
                config=cache_config,
            )
            return new_cache.name
        except Exception as e: # pylint: disable=broad-exception-caught
            log.error("Failed to create context cache: %s", e)
            return None

    def delete_cache(self, name: str):
        """Manually delete a cache."""
        try:
            self.client.caches.delete(name=name)
            log.info(f"Deleted cache: {name}")
        except Exception as e:
            log.error(f"Failed to delete cache {name}: {e}")

    def refresh_ttl(self, name: str, ttl_seconds: int = 3600):
        """Update TTL for an existing cache."""
        try:
            self.client.caches.update(
                name=name,
                config=types.UpdateCachedContentConfig(ttl=f"{ttl_seconds}s")
            )
        except Exception as e:
            log.error(f"Failed to update TTL for {name}: {e}")

_MANAGER = None

def get_cache_manager() -> LoreCacheManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = LoreCacheManager()
    return _MANAGER
