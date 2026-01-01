"""
StoryEngine Context Manager
Manages conversation history with intelligent compression.
"""
from typing import Any, Dict, List

from google import genai
from google.genai import types

from .config import FLASH_MODEL
from .normalize import normalize_turn
from .ui import console, log


class ContextManager:
    """Manages conversation history with absolute fidelity for Gemini 3 signatures."""
    
    def __init__(self, client: genai.Client, max_turns: int = 100):
        self.client = client
        self.max_turns = max_turns
        self.history: List[types.Content] = []
        self.summaries: List[str] = []
        
    def add_text(self, role: str, text: str):
        """Add a turn as text (Lossless)."""
        content = types.Content(
            role=role,
            parts=[types.Part(text=text)]
        )
        self.history.append(content)
        
    def add_content(self, content: types.Content):
        """Add a raw Content object directly (Preserves thought_signatures)."""
        # Ensure we are storing the actual object instance
        self.history.append(content)
        
    def get_context(self) -> List[types.Content]:
        """Get the full narrative context without data loss."""
        api_context = []
        
        # 1. Inject summaries as a single system/user aggregate if they exist
        if self.summaries:
            summary_text = "\n---\n".join(self.summaries)
            api_context.append(types.Content(
                role="user",
                parts=[types.Part(text=f"[ARC SUMMARY: HISTORICAL CANON]\n{summary_text}\n[END SUMMARY]")]
            ))
            
        # 2. Sequential turns
        api_context.extend(list(self.history))
        return api_context
    
    async def compress_if_needed(self) -> bool:
        """Compress old history into summary if exceeding limits."""
        if len(self.history) <= self.max_turns:
            return False
            
        console.print("[dim italic]>> [CONTEXT] Synthesizing narrative wavefront...[/]")
        
        # Take oldest chunk for summarization
        # We keep the last 10 turns for local continuity
        split_idx = len(self.history) - 10
        to_summarize = self.history[:split_idx]
        self.history = self.history[split_idx:]
        
        # Build summarization prompt
        turns_text_list = []
        for t in to_summarize:
            role = t.role.upper()
            parts_text = []
            for p in (t.parts or []):
                if p.text:
                    parts_text.append(p.text)
                if p.function_call:
                    parts_text.append(f"[ACTION: {p.function_call.name}]")
                if p.function_response:
                    parts_text.append(f"[RESULT: {p.function_response.name}]")
            turns_text_list.append(f"{role}: {' '.join(parts_text)[:300]}")
        
        turns_text = "\n".join(turns_text_list)
        
        prompt = f"""Synthesize these historical events into a dense Narrative Canon.
Focus on established facts, character locations, and unresolved emotional tension.

HISTORICAL STREAM:
{turns_text}

CANON SUMMARY:"""

        try:
            response = self.client.models.generate_content(
                model=FLASH_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=500
                )
            )
            summary = response.candidates[0].content.parts[0].text
            self.summaries.append(summary)
            console.print(f"[dim green]>> [CONTEXT] Archived {len(to_summarize)} turns to Canon Summary.[/]")
            return True
        except Exception as e:
            log.warning(f"Summarization failed: {e}")
            return False
    
    def clear(self):
        self.history = []
        self.summaries = []

    def snapshot(self) -> List[types.Content]:
        """Return a deep copy of the current history."""
        # Using slice for shallow copy of list, but Content objects are effectively immutable here
        # For true safety, we construct a fresh list
        return list(self.history)

    def restore(self, snapshot: List[types.Content]):
        """Restore history from a snapshot."""
        self.history = list(snapshot)
