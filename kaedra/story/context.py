from __future__ import annotations

import copy
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # optional

try:
    import tiktoken  # type: ignore
except Exception:
    tiktoken = None  # optional

from google.genai import types


@dataclass
class _PruneInfo:
    did_prune: bool = False
    pruned_messages: int = 0
    before_tokens: int = 0
    after_tokens: int = 0
    ts: float = 0.0


class ContextManager:
    """
    Large budget context tracker with automatic pruning.

    Compatibility surface for existing engine code:
      - history: list[types.Content]
      - max_tokens: int
      - add_text(role, text)
      - add_content(content)
      - get_context()
      - snapshot() / restore(snapshot)
      - _estimate_tokens()
      - get_budget_status()
    """

    def __init__(
        self,
        client: Any,
        max_context_tokens: int = 1_000_000,
        prune_threshold: float = 0.85,
        target_usage: float = 0.75,
        min_keep: int = 10,
        tokenizer_model_hint: str = "cl100k_base",
    ) -> None:
        self.client = client
        self.max_tokens = int(max_context_tokens)

        self.prune_threshold = float(prune_threshold)
        self.target_usage = float(target_usage)
        self.min_keep = int(min_keep)

        self.history: List[types.Content] = []
        self._encoding = self._init_encoding(tokenizer_model_hint)
        self._last_prune = _PruneInfo()
        self.cached_content_name: Optional[str] = None
        self.last_cache_time: float = 0.0

    def _init_encoding(self, model_hint: str):
        if tiktoken is None:
            return None
        try:
            return tiktoken.get_encoding(model_hint)
        except Exception:
            try:
                return tiktoken.get_encoding("cl100k_base")
            except Exception:
                return None

    def add_text(self, role: str, text: str) -> None:
        content = types.Content(role=role, parts=[types.Part(text=text)])
        self.history.append(content)
        self._auto_prune_if_needed()

    def add_content(self, content: types.Content) -> None:
        self.history.append(content)
        self._auto_prune_if_needed()

    def get_context(self) -> List[types.Content]:
        return self.history

    def snapshot(self) -> Dict[str, Any]:
        return {
            "history": copy.deepcopy(self.history),
            "max_tokens": self.max_tokens,
            "prune_threshold": self.prune_threshold,
            "target_usage": self.target_usage,
            "min_keep": self.min_keep,
            "last_prune": copy.deepcopy(self._last_prune),
            "cached_content_name": self.cached_content_name
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self.history = snapshot.get("history", [])
        self.max_tokens = int(snapshot.get("max_tokens", self.max_tokens))
        self.prune_threshold = float(snapshot.get("prune_threshold", self.prune_threshold))
        self.target_usage = float(snapshot.get("target_usage", self.target_usage))
        self.min_keep = int(snapshot.get("min_keep", self.min_keep))
        self._last_prune = snapshot.get("last_prune", _PruneInfo())
        self.cached_content_name = snapshot.get("cached_content_name", None)

    def _count_text_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            try:
                return len(self._encoding.encode(text))
            except Exception:
                pass
        return max(1, len(text) // 4)

    def _estimate_tokens(self) -> int:
        total = 0

        for msg in self.history:
            total += 4

            parts = getattr(msg, "parts", None)
            if not parts:
                continue

            for p in parts:
                txt = getattr(p, "text", None)
                if txt:
                    total += self._count_text_tokens(txt)
                    continue

                inline = getattr(p, "inline_data", None)
                if inline is not None:
                    data = getattr(inline, "data", None)
                    if data is not None:
                        try:
                            total += max(50, int(len(data)) // 4)
                        except Exception:
                            total += 200
                    else:
                        total += 200
                    continue

                fc = getattr(p, "function_call", None)
                if fc is not None:
                    total += 150
                    continue

                fr = getattr(p, "function_response", None)
                if fr is not None:
                    total += 200
                    continue

                total += 25

        return int(total)

    def _auto_prune_if_needed(self) -> _PruneInfo:
        current = self._estimate_tokens()
        threshold_tokens = int(self.max_tokens * self.prune_threshold)

        if current < threshold_tokens:
            self._last_prune = _PruneInfo(did_prune=False, pruned_messages=0, before_tokens=current, after_tokens=current, ts=time.time())
            return self._last_prune

        before = current
        pruned = self._prune_to_target()
        after = self._estimate_tokens()

        self._last_prune = _PruneInfo(
            did_prune=pruned > 0,
            pruned_messages=pruned,
            before_tokens=before,
            after_tokens=after,
            ts=time.time(),
        )
        return self._last_prune

    def _prune_to_target(self) -> int:
        target_tokens = int(self.max_tokens * self.target_usage)
        pruned = 0

        while len(self.history) > self.min_keep and self._estimate_tokens() > target_tokens:
            self.history.pop(0)
            pruned += 1

        return pruned

    def get_budget_status(self, prune: bool = True) -> Dict[str, Any]:
        current = self._estimate_tokens()
        capacity = self.max_tokens
        usage_percent = (current / capacity * 100.0) if capacity > 0 else 0.0
        should_prune = current >= int(capacity * self.prune_threshold)

        prune_info = self._last_prune
        if prune and should_prune:
            prune_info = self._auto_prune_if_needed()
            current = prune_info.after_tokens
            usage_percent = (current / capacity * 100.0) if capacity > 0 else 0.0

        rss_mb = None
        if psutil is not None:
            try:
                rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            except Exception:
                rss_mb = None

        return {
            "current": current,
            "capacity": capacity,
            "usage_percent": usage_percent,
            "should_prune": should_prune,
            "pruned_messages": prune_info.pruned_messages,
            "rss_mb": rss_mb
        }


    def clear(self):
        """Clear context history."""
        self.history = []
        self._last_prune = _PruneInfo()
        self.cached_content_name = None
    def update_cache(self, model_name: str, system_instruction: str = None) -> Optional[str]:
        """
        Create or update a context cache using STABLE PAST strategy.
        Caches everything *except* the last turn if history is large.
        Returns cache resource name if active, else None.
        """
        # 1. Check eligibility (Min 32,768 tokens)
        current_tokens = self._estimate_tokens()
        MIN_CACHE_TOKENS = 32_768

        if current_tokens < MIN_CACHE_TOKENS:
            self.cached_content_name = None
            return None

        # 2. Stable Past Strategy
        # We cache history[:-1] so the current turn is always fresh input.
        # This allows multiple forks/retries of the current turn against the same cache.
        cache_contents = self.history[:-1] if len(self.history) > 1 else self.history

        try:
            config = types.CreateCachedContentConfig(
                model=model_name,
                contents=cache_contents,
                ttl="3600s", # 1 hour
                system_instruction=system_instruction
            )

            # Note: client.caches.create typically returns a resource with .name
            cache = self.client.caches.create(config=config)
            self.cached_content_name = cache.name
            self.last_cache_time = time.time()
            return self.cached_content_name

        except Exception:
            self.cached_content_name = None
            return None

