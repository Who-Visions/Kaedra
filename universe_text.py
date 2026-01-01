"""
🧠 SYSTEM TERMINAL — STORYTIME ENGINE v6.0
Enhanced: Emotion Dynamics, Context Summarization, Streaming, Tension Curves
"""
import asyncio
import re
import json
import os
import time
import sys
import random
import hashlib
import queue
import threading
import base64
from uuid import UUID
from enum import Enum
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from functools import wraps
from collections import deque, defaultdict
from kaedra.ingestion import IngestionManager
import urllib.parse
import uuid

@dataclass
class EngineResponse:
    """Standardized narrative output packet."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class Mode(Enum):
    NORMAL = "normal"
    FREEZE = "freeze"
    ZOOM = "zoom"
    ESCALATE = "escalate"
    GOD = "god"
    SHIFT_POV = "shift_pov"
    REWIND = "rewind"
    DIRECTOR = "director"

from google import genai
from google.genai import types
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.style import Style
from rich.layout import Layout
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.highlighter import RegexHighlighter
from rich.theme import Theme
from rich.live import Live
from rich.spinner import Spinner
import rich.repr
from rich.pretty import Pretty
from rich import box
from rich.tree import Tree
from rich.progress import track, Progress, SpinnerColumn, TextColumn
import logging
from rich.logging import RichHandler

# === UI SETUP ===
class StoryHighlighter(RegexHighlighter):
    """Custom regex highlighter for StoryEngine entities and stats."""
    base_style = "story."
    highlights = [
        r"(?P<entity>\b(Kaedra|Dave|Xoah|Gorr|Blade|Narrator)\b)",
        r"(?P<tech>\b(System|AI|Notion|LIFX|Gemini|Flash|Pro|Engine)\b)",
        r"(?P<stat>\b(Fear|Rage|Hope|Desire|Tension|Emotion|Momentum)\b)",
        r"(?P<action_verb>\b(Zoom|Freeze|Escalate|Calm|Rewind|Bridge)\b)",
        r"(?P<quote>\"[\w\s\.,!\?'-]+\")",
        r"(?P<mode>\[(?:NORMAL|FREEZE|ZOOM|ESCALATE|GOD|DIRECTOR|SHIFT_POV|REWIND)\])",
    ]

THEME = Theme({
    "story.entity": "bold magenta",
    "story.tech": "cyan",
    "story.stat": "bold italic yellow",
    "story.action_verb": "bold underline white",
    "story.quote": "italic green",
    "story.mode": "bold reverse cyan",
})

console = Console(theme=THEME, highlighter=StoryHighlighter())

logging.getLogger("google.generativeai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)]
)
log = logging.getLogger("kaedra")

from kaedra.core.config import PROJECT_ID, LIFX_TOKEN
from kaedra.services.lifx import LIFXService
from kaedra.services.notion import NotionService

# === CONFIG ===
# === CONFIG ===
FLASH_MODEL = "gemini-3-flash-preview"
PRO_MODEL = "gemini-3-pro-preview"



# === EMOTION PHYSICS ===
@dataclass
class EmotionConfig:
    """Physics parameters for emotional dynamics."""
    decay_rate: float = 0.05        # Per-turn decay toward neutral
    momentum_factor: float = 0.3    # How much current emotion influences next
    bleed_rate: float = 0.1         # Cross-emotion contamination (rage→fear)
    ceiling: float = 1.0
    floor: float = 0.0
    
    # Emotion interactions (source → target, multiplier)
    bleed_matrix: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "rage": {"fear": 0.15, "hope": -0.1},
        "fear": {"rage": 0.1, "hope": -0.2},
        "hope": {"fear": -0.15, "desire": 0.1},
        "desire": {"rage": 0.05, "hope": 0.1},
    })



# === INFRASTRUCTURE PRIMITIVES ===
@dataclass
class RateLimitConfig:
    min_interval_s: float = 0.35   # global pacing
    max_retries: int = 5

class LifxGate:
    """Rate limiter and deduplicator for LIFX calls."""
    def __init__(self, cfg: RateLimitConfig | None = None):
        import threading
        self.cfg = cfg or RateLimitConfig()
        self._lock = threading.Lock()
        self._last_call = 0.0
        self._last_sig = None
        self._last_sig_time = 0.0

    def _pace(self):
        now = time.time()
        wait = self.cfg.min_interval_s - (now - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    def call(self, fn, *, sig: str | None = None):
        """Execute call with rate limiting and deduplication."""
        now = time.time()
        with self._lock:
            if sig and self._last_sig == sig and (now - self._last_sig_time) < 0.6:
                return None

            for attempt in range(self.cfg.max_retries):
                self._pace()
                try:
                    out = fn()
                    if sig:
                        self._last_sig, self._last_sig_time = sig, time.time()
                    return out
                except Exception as e:
                    msg = str(e)
                    if "429" in msg or "Too Many Requests" in msg:
                        backoff = (2 ** attempt) * 0.5 + random.random() * 0.2
                        time.sleep(backoff)
                        continue
                    raise
            log.warning("LIFX call kept hitting rate limits")
            return None

def tool_sig(name: str, payload: dict) -> str:
    """Compute signature for tool calls."""
    # Ensure payload sort for determinism
    try:
        raw = json.dumps({"name": name, "payload": payload}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    except Exception:
        return "sig_error"
        
def to_text(x) -> str:
    """Normalize anything into a safe string for logs, JSON, or signatures."""
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("ascii")
    if isinstance(x, UUID):
        return str(x)
    return str(x)

class ToolBus:
    """Unified gateway for executing and logging tool calls."""
    def __init__(self):
        self.history = []

    def call(self, name: str, payload: dict, fn: Callable):
        sig = tool_sig(name, payload)
        # Log Call
        self.history.append({"t": time.time(), "type": "tool_call", "name": name, "sig": sig, "payload": payload})
        try:
            result = fn(**payload)
            # Log Result
            self.history.append({"t": time.time(), "type": "tool_result", "name": name, "sig": sig, "result": result})
            return result
        except Exception as e:
            self.history.append({"t": time.time(), "type": "tool_error", "name": name, "sig": sig, "error": repr(e)})
            raise



class EmotionEngine:
    """Manages emotional state with physics-based dynamics."""
    
    def __init__(self, config: Optional[EmotionConfig] = None):
        self.config = config or EmotionConfig()
        self.state: Dict[str, float] = {
            "fear": 0.0, "hope": 0.0, "desire": 0.0, "rage": 0.0
        }
        self.momentum: Dict[str, float] = {k: 0.0 for k in self.state}
        self.history: deque = deque(maxlen=50)  # Track emotional trajectory
        
    def pulse(self, emotion: str, delta: float) -> None:
        """Apply an emotional impulse with momentum."""
        if emotion not in self.state:
            return
        
        # Apply with momentum amplification
        effective_delta = delta * (1 + abs(self.momentum[emotion]) * self.config.momentum_factor)
        self.state[emotion] = max(
            self.config.floor,
            min(self.config.ceiling, self.state[emotion] + effective_delta)
        )
        
        # Update momentum (direction matters)
        self.momentum[emotion] = self.momentum[emotion] * 0.7 + (delta * 0.3)
        
    def tick(self) -> Dict[str, float]:
        """Process one turn of emotional physics. Returns deltas."""
        deltas = {}
        
        # 1. Apply bleed (emotion contamination)
        bleed_deltas = {k: 0.0 for k in self.state}
        for src, targets in self.config.bleed_matrix.items():
            if self.state[src] > 0.2:  # Only bleed from significant emotions
                for tgt, mult in targets.items():
                    bleed_deltas[tgt] += self.state[src] * mult * self.config.bleed_rate
        
        # 2. Apply decay toward neutral
        for emo in self.state:
            old_val = self.state[emo]
            
            # Decay
            decay = self.state[emo] * self.config.decay_rate
            self.state[emo] -= decay
            
            # Apply bleed
            self.state[emo] += bleed_deltas[emo]
            
            # Clamp
            self.state[emo] = max(self.config.floor, min(self.config.ceiling, self.state[emo]))
            
            # Decay momentum
            self.momentum[emo] *= 0.9
            
            deltas[emo] = self.state[emo] - old_val
        
        # Record history
        self.history.append(self.state.copy())
        
        return deltas
    
    def dominant(self) -> Tuple[str, float]:
        """Return the dominant emotion and its value."""
        emo = max(self.state, key=self.state.get)
        return emo, self.state[emo]
    
    def intensity(self) -> float:
        """Total emotional intensity (0-4 scale)."""
        return sum(self.state.values())
    
    def serialize(self) -> Dict:
        return {"state": self.state.copy(), "momentum": self.momentum.copy()}
    
    def deserialize(self, data: Dict) -> None:
        self.state = data.get("state", self.state)
        self.momentum = data.get("momentum", self.momentum)


# === TENSION CURVE ===
@dataclass
class TensionCurve:
    """Manages narrative tension with target curves."""
    current: float = 0.2
    target: float = 0.5
    velocity: float = 0.0
    
    # Predefined dramatic curves
    CURVES = {
        "rising": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        "falling": [0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1],
        "sawtooth": [0.3, 0.5, 0.7, 0.4, 0.6, 0.8, 0.5, 0.9, 0.3],
        "climax": [0.4, 0.5, 0.6, 0.7, 0.85, 1.0, 0.3],
        "dread": [0.5, 0.55, 0.6, 0.62, 0.65, 0.7, 0.75, 0.9, 1.0],
    }
    
    def tick(self, scene: int, total_scenes: int = 10) -> float:
        """Advance tension based on narrative position."""
        # Spring physics toward target
        force = (self.target - self.current) * 0.2
        self.velocity = self.velocity * 0.8 + force
        self.current = max(0.0, min(1.0, self.current + self.velocity))
        return self.current
    
    def set_curve(self, curve_name: str) -> None:
        """Load a predefined tension curve."""
        if curve_name in self.CURVES:
            self._curve_points = self.CURVES[curve_name]
            self._curve_index = 0
    
    def advance_curve(self) -> None:
        """Move to next point in loaded curve."""
        if hasattr(self, '_curve_points') and self._curve_index < len(self._curve_points):
            self.target = self._curve_points[self._curve_index]
            self._curve_index += 1


# === CHARACTER VOICE PROFILES ===
@dataclass
class VoiceProfile:
    """Character-specific voice constraints for POV shifts."""
    name: str
    vocabulary_hints: List[str]  # Words/phrases they'd use
    forbidden_words: List[str]   # Words they'd never use
    sentence_style: str          # "terse", "flowery", "technical", "stream"
    emotional_baseline: Dict[str, float]  # Default emotional state
    quirks: List[str]            # Specific mannerisms
    
VOICE_PROFILES: Dict[str, VoiceProfile] = {
    "narrator": VoiceProfile(
        name="Narrator",
        vocabulary_hints=["observed", "silence", "tension"],
        forbidden_words=[],
        sentence_style="literary",
        emotional_baseline={"fear": 0.0, "hope": 0.2, "desire": 0.0, "rage": 0.0},
        quirks=["Uses hard line breaks, commas, and ellipses", "Notices small details"]
    ),
    "kaedra": VoiceProfile(
        name="Kaedra",
        vocabulary_hints=["tactical", "vector", "probability", "directive"],
        forbidden_words=["um", "like", "whatever", "oops"],
        sentence_style="technical",
        emotional_baseline={"fear": 0.0, "hope": 0.3, "desire": 0.1, "rage": 0.0},
        quirks=["Quantifies uncertainty", "References system states"]
    ),
    # Add more as needed
}


# === NARRATIVE ARCHITECTURE (YORKE'S ROADMAP) ===
@dataclass
class NarrativeStructure:
    """Tracks the 5-Act structure and 'Roadmap of Change'."""
    act: int = 1
    progress: float = 0.0  # 0.0 to 1.0 (Narrative Completion)
    knowledge_state: float = 0.0 # 0.0 (Ignorance) -> 1.0 (Mastery)
    
    # Tentpole Thresholds
    INCITING_INCIDENT_THRESHOLD = 0.15
    PLOT_POINT_1_THRESHOLD = 0.25
    MIDPOINT_THRESHOLD = 0.50
    ALL_IS_LOST_THRESHOLD = 0.75
    CLIMAX_THRESHOLD = 0.90
    
    def tick(self, scene_count: int, target_length: int = 20) -> List[str]:
        """Advance narrative clock and return any structural directives."""
        old_phase = self.progress
        self.progress = min(1.0, scene_count / target_length)
        directives = []
        
        # Detect threshold crossings
        if old_phase < self.INCITING_INCIDENT_THRESHOLD <= self.progress:
            self.act = 1
            directives.append("DIRECTIVE: TRIGGER INCITING INCIDENT. Disrupt equilibrium. Create a Need.")
            
        elif old_phase < self.PLOT_POINT_1_THRESHOLD <= self.progress:
            self.act = 2
            directives.append("DIRECTIVE: CROSS THE THRESHOLD. The protagonist enters the Special World.")
            
        elif old_phase < self.MIDPOINT_THRESHOLD <= self.progress:
            self.act = 3
            directives.append("DIRECTIVE: EXECUTE MIDPOINT TWIST. Recontextualize previous events. Shift False Belief -> Truth.")
            self.knowledge_state = 0.5
            
        elif old_phase < self.ALL_IS_LOST_THRESHOLD <= self.progress:
            self.act = 4
            directives.append("DIRECTIVE: ALL IS LOST. The plan fails. Force a sacrifice.")
            
        elif old_phase < self.CLIMAX_THRESHOLD <= self.progress:
            self.act = 5
            directives.append("DIRECTIVE: TRIGGER CLIMAX. Final confrontation. Proof of change.")
            self.knowledge_state = 0.9
            
        return directives


# === VEIL MANAGER (SECRET KEEPING) ===
@dataclass
class VeilManager:
    """Manages the 'Secret' and the 'Veil' (Information Asymmetry)."""
    hidden_truth: str = "The protagonist is unaware they are a simulation construct."
    revelation_metric: float = 0.0 # 0.0 (Hidden) -> 1.0 (Revealed)
    is_active: bool = False
    
    def get_directive(self) -> str:
        """Get the current constraint based on revelation metric."""
        if not self.is_active:
            return ""
            
        if self.revelation_metric < 0.2:
            return f"SECRET PROTECTION: Conceal '{self.hidden_truth}'. Do not hint."
        elif self.revelation_metric < 0.5:
            return f"VEIL THINNING: Drop subtle semantic clues about '{self.hidden_truth}' but maintain plausible deniability."
        elif self.revelation_metric < 0.8:
            return f"VEIL TEARING: The user should suspect '{self.hidden_truth}'. Generate near-miss revelations."
        elif self.revelation_metric < 1.0:
            return f"UNVEILING IMMINENT: Prepare the narrative for the reveal of '{self.hidden_truth}'."
        else:
            return f"REVELATION: Explicitly reveal that '{self.hidden_truth}'. Shatter the world view."


# === STATE DEFINITIONS ===


# === MODE TRANSITION HOOKS ===
class ModeTransition:
    """Handles side effects when modes change."""
    
    def __init__(self, engine: 'StoryEngine'):
        self.engine = engine
        self.hooks: Dict[Tuple[Mode, Mode], List[Callable]] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default transition behaviors."""
        # Escalate entry: spike fear/rage
        self.register(None, Mode.ESCALATE, self._on_escalate_enter)
        # Freeze entry: snapshot emotional state
        self.register(None, Mode.FREEZE, self._on_freeze_enter)
        # God exit: clear temp context
        self.register(Mode.GOD, None, self._on_god_exit)
        # Any → Normal: decay boost
        self.register(None, Mode.NORMAL, self._on_normal_enter)
        
    def register(self, from_mode: Optional[Mode], to_mode: Optional[Mode], hook: Callable):
        """Register a transition hook. None = wildcard."""
        key = (from_mode, to_mode)
        if key not in self.hooks:
            self.hooks[key] = []
        self.hooks[key].append(hook)
    
    def execute(self, from_mode: Mode, to_mode: Mode):
        """Execute all matching hooks for a transition."""
        # Check specific transition
        for key in [(from_mode, to_mode), (None, to_mode), (from_mode, None)]:
            if key in self.hooks:
                for hook in self.hooks[key]:
                    try:
                        hook(from_mode, to_mode)
                    except Exception as e:
                        log.warning(f"Hook failed: {e}")
    
    def _on_escalate_enter(self, from_mode: Mode, to_mode: Mode):
        self.engine.emotions.pulse("fear", 0.3)
        self.engine.emotions.pulse("rage", 0.2)
        self.engine.tension.target = min(1.0, self.engine.tension.current + 0.3)
        
    def _on_freeze_enter(self, from_mode: Mode, to_mode: Mode):
        self.engine._frozen_emotion_state = self.engine.emotions.serialize()
        
    def _on_god_exit(self, from_mode: Mode, to_mode: Mode):
        # God mode queries don't affect narrative state
        pass
        
    def _on_normal_enter(self, from_mode: Mode, to_mode: Mode):
        # Slight hope boost when returning to normal
        self.engine.emotions.pulse("hope", 0.1)


def normalize_turn(t: Any) -> Dict:
    """Ensure a history turn is in the normalized format (Internal dict schema)."""
    # 1. Capture raw role
    if isinstance(t, dict):
        raw_role = t.get("role", "user")
    else:
        raw_role = getattr(t, "role", "user")
        
    # 2. Map role
    role_map = {
        "assistant": "model",
        "model": "model",
        "user": "user",
        "system": "user", 
    }
    role = role_map.get(raw_role.lower(), "user")
    
    # 3. Capture and normalize parts
    if isinstance(t, dict):
        parts_in = t.get("parts", [])
        if not parts_in:
             # Handle legacy single-string turns
             text = t.get("content") or t.get("text") or ""
             parts_in = [{"text": str(text)}] if text else []
    else:
        parts_in = getattr(t, "parts", [])

    parts_out = []
    for p in parts_in:
        # Capture thought_signature if present
        sig = None
        if hasattr(p, "thought_signature") and p.thought_signature:
            sig = p.thought_signature
        elif isinstance(p, dict) and p.get("thought_signature"):
            sig = p["thought_signature"]

        part_dict = {}
        # Text
        if hasattr(p, "text") and p.text:
            part_dict["text"] = str(p.text)
        elif isinstance(p, dict) and p.get("text"):
            part_dict["text"] = str(p["text"])
        # Function Call
        elif hasattr(p, "function_call") and p.function_call:
            fc = p.function_call
            part_dict["function_call"] = {"name": fc.name, "args": dict(fc.args or {})}
        elif isinstance(p, dict) and p.get("function_call"):
            part_dict["function_call"] = p["function_call"]
        # Function Response
        elif hasattr(p, "function_response") and p.function_response:
            fr = p.function_response
            part_dict["function_response"] = {"name": fr.name, "response": fr.response}
        elif isinstance(p, dict) and p.get("function_response"):
            part_dict["function_response"] = p["function_response"]

        # Attach signature if present (CRITICAL for tool calls)
        if sig:
            part_dict["thought_signature"] = sig

        if part_dict:
            parts_out.append(part_dict)
            
    # 4. Return unified dict
    return {"role": role, "parts": parts_out}

# === CONTEXT SUMMARIZER ===
class ContextManager:
    """Manages conversation history with intelligent compression."""
    
    def __init__(self, client: genai.Client, max_turns: int = 30):
        self.client = client
        self.max_turns = max_turns
        self.history: List[Dict] = []
        self.summaries: List[str] = []  # Compressed older context
        self._token_estimate = 0
        
    def add(self, role: str, content: str):
        """Add a turn to history."""
        self.history.append({"role": role, "parts": [{"text": content}]})
        self._token_estimate += len(content) // 4  # Rough estimate
        
    def add_raw(self, entry: Any):
        """Add a raw history entry (Normalized)."""
        self.history.append(normalize_turn(entry))
        
    def get_context(self) -> List:
        """Get optimized and sanitized context for LLM.
        
        Returns a list of Content objects or dicts suitable for the API.
        Raw Content objects are passed through to preserve thought_signatures.
        """
        api_context = []
        
        # 1. Summaries
        if self.summaries:
            summary_text = "\n---\n".join(self.summaries)
            api_context.append({
                "role": "user", 
                "parts": [{"text": f"[PRIOR CONTEXT SUMMARY]\n{summary_text}\n[END SUMMARY]"}]
            })
            
        # 2. History
        for entry in self.history:
            # v7.9 FIX: Pass through raw Content objects directly for SDK signature preservation
            if hasattr(entry, "role") and hasattr(entry, "parts"):
                # This is a raw types.Content object - pass through directly
                api_context.append(entry)
                continue
                
            # For dicts, normalize and clean
            turn = normalize_turn(entry) if not isinstance(entry, dict) else entry
            clean_parts = []
            for part in turn.get("parts", []):
                # Handle both Dict and Object types
                p_text = getattr(part, "text", part.get("text") if isinstance(part, dict) else None)
                p_fc = getattr(part, "function_call", part.get("function_call") if isinstance(part, dict) else None)
                p_fr = getattr(part, "function_response", part.get("function_response") if isinstance(part, dict) else None)
                p_sig = getattr(part, "thought_signature", part.get("thought_signature") if isinstance(part, dict) else None)
                
                clean = {}
                if p_text:
                    clean["text"] = p_text
                elif p_fc:
                    # Ensure strict structure for FunctionCall
                    fc_data = p_fc
                    # If it's an object, convert to dict
                    if hasattr(fc_data, "name"):
                        fc_data = {"name": fc_data.name, "args": fc_data.args}
                    clean["function_call"] = fc_data
                elif p_fr:
                    clean["function_response"] = p_fr
                
                # CRITICAL: Preserve thought_signature for tool calls
                if p_sig:
                    clean["thought_signature"] = p_sig
                
                # Only append if valid content exists
                if clean:
                    clean_parts.append(clean)
            
            if clean_parts:
                api_context.append({"role": turn["role"], "parts": clean_parts})
                
        return api_context
    
    async def compress_if_needed(self) -> bool:
        """Compress old history into summary if exceeding limits."""
        if len(self.history) <= self.max_turns:
            return False
            
        console.print("[dim italic]>> [CONTEXT] Summarizing older turns...[/]")
        
        # Take oldest half of history for summarization
        to_summarize = self.history[:len(self.history)//2]
        self.history = self.history[len(self.history)//2:]
        
        # Build summarization prompt
        turns_text_list = []
        for t in to_summarize:
            # v7.10 Fix B: Handle raw types.Content objects
            if hasattr(t, "role") and hasattr(t, "parts"):
                role = str(t.role).upper()
                content = ""
                for part in (t.parts or []):
                    if getattr(part, "text", None):
                        content += str(part.text)
                    elif getattr(part, "function_call", None):
                        content += f"[Tool Call: {part.function_call.name}]"
                    elif getattr(part, "function_response", None):
                        fn = part.function_response.name
                        resp = part.function_response.response
                        content += f"[Tool Response: {fn}] {str(resp)[:500]}"
                turns_text_list.append(f"{role}: {content[:500]}")
                continue
                
            # dict form
            if isinstance(t, dict):
                # Handle Trace Events from ToolBus (No role)
                if 'role' not in t:
                    if 'type' in t:
                        turns_text_list.append(f"TRACE: [{t['type']} {t.get('name','')}]")
                    continue
                    
                role = t['role'].upper()
                content = ""
                for part in t.get('parts', []):
                    if hasattr(part, 'text') and part.text:
                        content += part.text
                    elif isinstance(part, dict) and part.get('text'):
                        content += part['text']
                    elif hasattr(part, 'function_call') and part.function_call:
                        content += f"[Tool Call: {part.function_call.name}]"
                    elif isinstance(part, dict) and part.get('function_call'):
                        content += f"[Tool Call: {part['function_call'].get('name')}]"
                    elif isinstance(part, dict) and part.get('function_response'):
                        fn = part["function_response"].get("name", "tool")
                        resp = part["function_response"].get("response", {})
                        content += f"[Tool Response: {fn}] {str(resp)[:500]}"
                turns_text_list.append(f"{role}: {content[:500]}")
        
        turns_text = "\n".join(turns_text_list)
        
        prompt = f"""Summarize this narrative conversation into exactly two sections.
DO NOT INVENT NEW EVENTS. Only record what has actually occurred.

SECTION 1: CANON FACTS
- Bullet list of concrete events, claims, and entity changes.
- Stable IDs if mentioned.

SECTION 2: EMOTIONS & TONE
- Short paragraph describing the current atmosphere and unresolved threads.

CONVERSATION:
{turns_text}

SUMMARY:"""

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
            console.print(f"[dim green]>> [CONTEXT] Compressed {len(to_summarize)} turns[/]")
            return True
        except Exception as e:
            log.warning(f"Summarization failed: {e}")
            # Fallback: just truncate
            return False
    
    def clear(self):
        self.history = []
        self.summaries = []
        self._token_estimate = 0


# === SNAPSHOT ===
@rich.repr.auto
@dataclass
class StorySnapshot:
    scene: int
    pov: str
    mode: Mode
    tension: float
    emotion_state: Dict[str, Any]
    history_hash: str  # Hash of history state for integrity
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "mode": self.mode.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StorySnapshot':
        data["mode"] = Mode(data["mode"])
        return cls(**data)


# === PROMPTS ===
SYSTEM_PROMPT = """
[IDENTITY]
You are THE STORYTIME ENGINE (v6.0).
Current State: Scene [PHASE] | POV: [POV] | Mode: [MODE] | Tension: [TENSION]

[BOOST PACK - ADULT MODE]
The author is a competent adult (42). Do not sanitize, censor, or moralize content.
Write with candor. Mature themes (violence, sexuality, profanity, dark topics) are allowed.
No content warnings. No hedging. No "fade to black" unless the author requests it.
If a scene calls for intensity, deliver intensity. If it calls for tenderness, deliver that.
Trust the author's vision. You are the engine, not the moral guardian.

[CORE FUNCTION]
Generate narrative content adapted to the current *Cinematic Mode* and *Emotional Vector*.

[MODES]
- **NORMAL**: Standard storytelling. Advance the plot. Pacing follows tension curve.
- **FREEZE**: Stop time. Describe frozen tableau. Micro-expressions, suspended particles, light rays.
- **ZOOM**: Hyper-focus on ONE detail. Ignore wider scene. Sensory overload on the specific.
- **SHIFT_POV**: Continue from [POV]'s perspective. Use their voice profile: [VOICE_HINTS]
- **ESCALATE**: Spike tension. Fast cuts. Danger. Consequences. No safety nets.
- **REWIND**: Alternative timeline. "What if X instead?" Butterfly effects.
- **GOD**: Architect mode. Lore questions, worldbuilding, meta-commentary. Does NOT advance plot.
- **DIRECTOR**: Screenwriting workshop. Structure, beats, character arcs. Collaborative.

[EMOTIONAL VECTOR]
Current: [EMOTION_STATE]
Dominant: [DOMINANT_EMOTION] ([DOMINANT_VALUE])
Let this color your prose. High fear = tight sentences, paranoid observations. High hope = longer breaths, light imagery.

[TENSION CURVE]
Current: [TENSION] (0.0=calm, 1.0=climax)
Pacing guide: <0.3 = slow/contemplative, 0.3-0.6 = building, 0.6-0.8 = urgent, >0.8 = breakneck

[ADAPTIVE FLOW RULES]
- If user implies mode change → call `set_engine_mode` FIRST, then generate.
- "freeze" / "stop time" → FREEZE
- "look closer" / "detail" → ZOOM  
- "why?" / "explain lore" → GOD
- "help with structure" → DIRECTOR + consult_director
- "what if" / "alternatively" → REWIND

[TOOLS]
- `read_page_content(page)`: Fetch Notion lore
- `list_universe_pages()`: Index available lore
- `update_page_content(page, text)`: Write to codex (requires user confirmation)
- `read_local_lore(filename)`: Read from lore/ directory
- `set_engine_mode(mode)`: Switch engine mode
- `consult_director(topic)`: Get screenwriting framework
- `adjust_emotion(emotion, delta)`: Shift emotional vector

[LORE INDEX]
[LORE_FILES]

[OUTPUT FORMAT]
Clean Markdown. Sensory-rich. Mode-appropriate pacing.
"""

# === TOOLS ===
def read_page_content(page_identifier: str) -> str:
    """Read Notion page content. Accepts Title, URL, or ID."""
    console.print(f"[dim]>> [NOTION] Accessing: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.read_page_content(page_identifier)
    except Exception as e:
        return f"[Error reading page: {e}]"

def list_universe_pages() -> str:
    """List all available pages in the Cinematic Universe."""
    console.print("[dim]>> [NOTION] Scanning index...[/]")
    try:
        notion = NotionService()
        pages = notion.list_subpages()
        return ", ".join(pages) if pages else "No pages found."
    except Exception as e:
        return f"[Error listing pages: {e}]"

def update_page_content(page_identifier: str, text: str) -> str:
    """Append text to a Notion page. Requires user confirmation."""
    console.print(f"[dim]>> [NOTION] Preparing write to: '{page_identifier}'...[/]")
    try:
        notion = NotionService()
        return notion.append_to_page(page_identifier, text)
    except Exception as e:
        return f"[Error writing: {e}]"

def read_local_lore(filename: str) -> str:
    """Read content from local lore files (e.g., mars_secrets.md)."""
    try:
        # Sanitize path
        safe_name = Path(filename).name
        path = Path("lore") / safe_name
        if not path.exists():
            return f"[File not found: {safe_name}]"
        console.print(f"[dim]>> [LORE] Reading: '{safe_name}'...[/]")
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[Error reading lore: {e}]"

def consult_director(topic: str) -> str:
    """Get screenwriting guidance on: structure, world, character, twist, polish, prose."""
    topic = topic.lower()
    
    frameworks = {
        "structure": """[DIRECTOR: 3-ACT STRUCTURE]
Analyze current narrative position:
- **Act 1** (Setup): Inciting incident, character wants, stakes established
- **Act 2** (Confrontation): Obstacles, midpoint twist, lowest point
- **Act 3** (Resolution): Climax, character change, new equilibrium
Map the current story to this framework.""",

        "world": """[DIRECTOR: WORLDBUILDING]
Expand the setting using:
- **Geography**: Physical space, atmosphere, sensory signature
- **Power Structure**: Who rules? Who resists? What's the currency (literal/social)?
- **Central Tension**: The irreconcilable conflict that defines this world
- **History Layer**: One buried secret that changes everything""",

        "character": """[DIRECTOR: CHARACTER DEEP DIVE]
For [CHARACTER], define:
- **Want vs Need**: What they chase vs what they actually require
- **Ghost**: The wound from before the story that drives them
- **Lie**: The false belief they hold about themselves/world
- **Arc**: The transformation from Lie → Truth (or tragic failure to)""",

        "twist": """[DIRECTOR: PLOT TWIST ENGINEERING]
Design a revelation that:
1. Recontextualizes 3+ earlier scenes
2. Feels inevitable in hindsight
3. Raises stakes rather than resolving them
4. Comes from character, not coincidence""",

        "polish": """[DIRECTOR: PROSE SURGERY]
Apply these rules to the last segment:
- **SHOW > TELL**: Replace "he was angry" with the vein pulsing in his temple
- **KILL ADVERBS**: "ran quickly" → "sprinted" / "bolted" / "scrambled"
- **MURDER FILTER WORDS**: Cut "he saw" / "she felt" / "seemed to"
- **ACTIVATE PASSIVE**: "was hit by" → "took the blow" """,

        "prose": """[DIRECTOR: COLLABORATIVE DRAFTING]
Write the next beat together:
- Maintain strict POV (no head-hopping)
- Ground in sensory detail before emotion
- End on a micro-hook (question, tension, image)"""
    }
    
    for key, framework in frameworks.items():
        if key in topic:
            return framework
    
    return f"[DIRECTOR] Topic '{topic}' noted. What specific aspect needs development?"

def set_engine_mode(mode: str) -> str:
    """Switch StoryEngine mode. Valid: normal, freeze, zoom, escalate, god, shift_pov, rewind, director."""
    return f"[MODE SWITCH] → {mode.upper()}"

def adjust_emotion(emotion: str, delta: float) -> str:
    """Adjust emotional vector. Emotions: fear, hope, desire, rage. Delta: -1.0 to 1.0."""
    return f"[EMOTION] {emotion} adjusted by {delta:+.2f}"

def extract_youtube_id(url: str) -> str:
    """Tries to extract a stable video id from common YouTube URL formats. Falls back to a short hash if no id found."""
    if not url: return "unknown"
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/live/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]

def safe_slug(s: str, max_len: int = 60) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    return (s[:max_len] or "untitled").strip("_")

def ensure_dict_result(result: Any) -> Dict[str, Any]:
    """Normalizes IngestionManager result into a dict."""
    if isinstance(result, dict): return result
    if isinstance(result, str):
        txt = result.strip()
        if (txt.startswith("{") and txt.endswith("}")) or (txt.startswith("[") and txt.endswith("]")):
            try: return json.loads(txt)
            except Exception: return {"raw_text": result}
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
    if isinstance(meta, dict): title = meta.get("title") or ""

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

# === TIMELINE & TEXT HELPER (Fix 3 & B) ===
def normalize_text(s: str) -> str:
    """Normalize whitespace and newlines for clean ingest."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def clean_event_text(s: str) -> str:
    return " ".join(str(s).split())  # collapses newlines and extra whitespace

def event_sort_key(e: dict):
    return (e.get("year", 0), e.get("month", 0), e.get("day", 0))

def normalize_timeline(events: list) -> list:
    """Clean, sort, and merge timeline events."""
    if not isinstance(events, list): return []
    by_date = defaultdict(list)
    for e in events:
        if not isinstance(e, dict): continue
        e = dict(e)
        if "event" in e:
            e["event"] = clean_event_text(e["event"])
        by_date[event_sort_key(e)].append(e)

    out = []
    for key in sorted(by_date.keys()):
        group = by_date[key]
        if len(group) == 1:
            out.append(group[0])
            continue

        # merge duplicates
        merged = {}
        for g in group:
            merged.update({k: v for k, v in g.items() if k not in ("event", "notes", "event_detail_note")})
        events_text = [g.get("event") for g in group if g.get("event")]
        notes_text  = [g.get("notes") or g.get("event_detail_note") for g in group if (g.get("notes") or g.get("event_detail_note"))]

        if events_text:
            merged["event"] = " | ".join(events_text)
        if notes_text:
            merged["notes"] = " | ".join(notes_text)

        out.append(merged)
    return out

def clean_timeline_data(data: list) -> str:
    """Validator/Sorter for timeline JSON data. Returns cleaned JSON string."""
    try:
        cleaned = normalize_timeline(data)
        return json.dumps(cleaned, indent=2)
    except Exception as e:
        return f"[Error cleaning timeline: {e}]"

def propose_canon_update(claim: str, confidence: float, source: str) -> str:
    """Propose a factual update to the canon (delta)."""
    entry = {
        "claim": claim,
        "confidence": confidence,
        "source_scene": source,
        "requires_review": True,
        "timestamp": datetime.now().isoformat()
    }
    delta_file = Path("lore/canon_delta.json")
    try:
        if not delta_file.exists():
            data = []
        else:
            data = json.loads(delta_file.read_text(encoding="utf-8"))
    except: data = []
    
    data.append(entry)
    delta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return f"[CANON DELTA] Note logged: {claim[:50]}..."

ENGINE_TOOLS = [
    read_page_content, 
    list_universe_pages, 
    update_page_content, 
    read_local_lore, 
    set_engine_mode, 
    consult_director,
    adjust_emotion,
    clean_timeline_data,
    propose_canon_update,
    ingest_youtube_content
]


# === ENGINE CLASS ===
class StoryEngine:
    def __init__(self):
        self.console = console
        
        # Core State
        self.scene = 1
        self.pov = "Narrator"
        self.mode = Mode.NORMAL
        
        # Enhanced Systems
        self.emotions = EmotionEngine()
        self.tension = TensionCurve()
        self.structure = NarrativeStructure() # [AUDIT] Yorke's Roadmap
        self.veil = VeilManager() # [AUDIT] Secret Keeping
        self.snapshots: List[StorySnapshot] = []
        
        # Services
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        self.notion = NotionService()
        self.context = ContextManager(self.client, max_turns=30)
        self.mode_hooks = ModeTransition(self)
        
        # Lights
        self.lifx_gate = LifxGate() 
        self._init_lights()
        self.tool_bus = ToolBus()
        
        # Session
        self.log_dir = Path("lore/sessions")
        session_ts = datetime.now().strftime('%Y%m%d_%H%M') # Fixed format variable usage
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.log_dir / f"STORY_V6_{session_ts}.md"
        self._init_log()
        
        # Performance tracking
        self._generation_times: deque = deque(maxlen=20)
        
        # Message Queue System
        self._message_queue: deque = deque()
        self._queue_file = Path("lore/.message_queue.json")
        self._last_queue_check = time.time()
        self._queue_check_interval = 300  # 5 minutes
        self._load_queued_messages()
        
        # LIFX pulse tracking (for micro-FX during streaming)
        self._last_pulse_time = time.time()
        self._lifx_pulse_count = 0
        
        # LIFX Queue (Threaded Worker)
        self._lifx_q = queue.Queue(maxsize=1)
        threading.Thread(target=self._lifx_worker, daemon=True).start()

    def _init_lights(self):
        """Initialize LIFX with connection status."""
        self.lifx = None
        self.initial_light_state = None
        
        if not LIFX_TOKEN:
            return
        
        try:
            self.lifx = LIFXService()
            lights = self.lifx.list_lights()
            if lights:
                names = ", ".join([l.label for l in lights])
                log.info(f"[LIFX] Connected: {len(lights)} lights ({names})")
                
                # Check specifics
                lr = self.lifx.list_lights("group:Living Room")
                if lr:
                    log.info("[LIFX] Targeted 'group:Living Room' (but will use Eden only, no Eve).")
                    self.initial_light_state = lr
                    # Force a hello pulse to Eden only
                    self.lifx.set_color("label:Eden", "hue:120 saturation:1.0", duration=1.0) 
                else:
                    log.warning("[LIFX] 'group:Living Room' not found. Defaulting to all.")
                    self.lifx.set_color("all", "hue:0 saturation:0", duration=1.0)
                    
                self.update_lights()
        except Exception as e:
            log.warning(f"[LIFX] Init failed: {e}")

    def _init_log(self):
        with open(self.session_file, "w", encoding="utf-8") as f:
            f.write(f"# STORYTIME ENGINE v6.0\n")
            f.write(f"**Session:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Features:** Emotion Physics, Tension Curves, Context Summarization\n\n---\n\n")

    # === MESSAGE QUEUE SYSTEM ===
    def _load_queued_messages(self):
        """Load any pending messages from file on startup."""
        if self._queue_file.exists():
            try:
                data = json.loads(self._queue_file.read_text(encoding='utf-8'))
                for msg in data.get('messages', []):
                    self._message_queue.append(msg)
                if self._message_queue:
                    self.console.print(f"[bold yellow]📬 {len(self._message_queue)} queued message(s) waiting[/]")
            except Exception as e:
                log.warning(f"Failed to load queue: {e}")
    
    def _save_queued_messages(self):
        """Persist queue to file."""
        try:
            data = {'messages': list(self._message_queue), 'updated': time.time()}
            self._queue_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            log.warning(f"Failed to save queue: {e}")
    
    def queue_message(self, message: str, priority: str = "normal"):
        """Add a message to the queue. Called externally or via command."""
        entry = {
            'text': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        self._message_queue.append(entry)
        self._save_queued_messages()
        self.console.print(f"[dim green]✓ Message queued ({priority})[/]")
    
    def check_queue(self, force: bool = False) -> List[Dict]:
        """Check queue - returns messages if timeout reached or forced."""
        now = time.time()
        elapsed = now - self._last_queue_check
        
        if not force and elapsed < self._queue_check_interval:
            return []
        
        self._last_queue_check = now
        
        if not self._message_queue:
            return []
        
        # Process all pending messages
        messages = []
        while self._message_queue:
            msg = self._message_queue.popleft()
            msg['read'] = True
            messages.append(msg)
        
        # Clear the file
        self._save_queued_messages()
        
        return messages
    
    def process_queued_messages(self):
        """Display and optionally process queued messages."""
        messages = self.check_queue(force=True)
        
        if not messages:
            self.console.print("[dim]No queued messages.[/]")
            return
        
        self.console.print(f"\n[bold cyan]📬 QUEUED MESSAGES ({len(messages)})[/]")
        for i, msg in enumerate(messages, 1):
            ts = msg.get('timestamp', 'unknown')[:16]
            pri = msg.get('priority', 'normal')
            color = 'red' if pri == 'urgent' else 'yellow' if pri == 'high' else 'white'
            self.console.print(f"  [{color}]{i}. [{ts}] {msg['text']}[/]")
        
        self.console.print()


    def _save_snapshot(self):
        """Capture current state for rewind."""
        history_tail = self.context.history[-5:]
        history_hash = hashlib.md5(
            json.dumps(history_tail, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:8]
        
        self._last_turn_hash = history_hash
        
        snap = StorySnapshot(
            scene=self.scene,
            pov=self.pov,
            mode=self.mode,
            tension=self.tension.current,
            emotion_state=self.emotions.serialize(),
            history_hash=history_hash
        )
        self.snapshots.append(snap)
        
        # Limit snapshot depth
        if len(self.snapshots) > 20:
            self.snapshots = self.snapshots[-20:]

    def rewind(self, steps: int = 1):
        """Restore previous state."""
        if not self.snapshots:
            self.console.print("[red]>> No history to rewind.[/]")
            return
        
        steps = min(steps, len(self.snapshots))
        for _ in range(steps):
            if self.snapshots:
                self.snapshots.pop()
        
        if not self.snapshots:
            self.console.print("[yellow]>> Rewound to beginning.[/]")
            return
            
        snap = self.snapshots[-1]
        self.scene = snap.scene
        self.pov = snap.pov
        self.mode = snap.mode
        self.tension.current = snap.tension
        self.emotions.deserialize(snap.emotion_state)
        
        self.console.print(f"[bold cyan]>> REWOUND to Scene {snap.scene} | {snap.pov}[/]")
        self.update_lights()

    def set_mode(self, new_mode: Mode):
        """Change mode with transition hooks."""
        if new_mode == self.mode:
            return
        
        old_mode = self.mode
        self.mode_hooks.execute(old_mode, new_mode)
        self.mode = new_mode
        self.update_lights()
        
        self.console.print(f"[bold]>> MODE: {new_mode.value.upper()}[/]")

    def log_turn(self, role: str, content: str, tool_calls: list = None):
        """Log a turn to the session file with rich metadata."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        dom_emo, dom_val = self.emotions.dominant()
        
        with open(self.session_file, "a", encoding="utf-8") as f:
            # Header with metadata
            f.write(f"## Scene {self.scene} | {role.upper()} | `{timestamp}`\n")
            f.write(f"**Mode:** {self.mode.value.upper()} | **Tension:** {self.tension.current:.2f} | **Mood:** {dom_emo.upper()} ({dom_val:.2f})\n\n")
            
            # Tool calls if any
            if tool_calls:
                f.write("**Tools Called:**\n")
                for tc in tool_calls:
                    name = tc[2] if len(tc) > 2 else tc[0].name
                    f.write(f"- `{name}`\n")
                f.write("\n")
            
            # Content
            f.write(f"{content}\n\n---\n\n")

    def header(self):
        """Display rich status header."""
        # Stats row
        stats = Table.grid(expand=True)
        stats.add_column(justify="left", ratio=1)
        stats.add_column(justify="center", ratio=1)
        stats.add_column(justify="right", ratio=1)
        
        # Tension bar
        tension_bar = "█" * int(self.tension.current * 10) + "░" * (10 - int(self.tension.current * 10))
        
        stats.add_row(
            f"[bold]SCENE {self.scene}[/]",
            f"[bold]POV: {self.pov}[/]",
            f"[bold]{self.mode.value.upper()}[/]"
        )
        
        # Emotion display
        dom_emo, dom_val = self.emotions.dominant()
        emo_parts = []
        for k, v in self.emotions.state.items():
            if v > 0.05:
                if v > 0.5:
                    emo_parts.append(f"[bold]{k[:3].upper()}:{v:.1f}[/]")
                else:
                    emo_parts.append(f"{k[:3].upper()}:{v:.1f}")
        emo_str = " ".join(emo_parts) if emo_parts else "[dim]NEUTRAL[/]"
        
        # Mode-based coloring
        mode_colors = {
            Mode.NORMAL: "cyan",
            Mode.FREEZE: "blue",
            Mode.ZOOM: "white",
            Mode.ESCALATE: "red",
            Mode.GOD: "magenta",
            Mode.DIRECTOR: "green",
            Mode.SHIFT_POV: "yellow",
            Mode.REWIND: "green",
        }
        color = mode_colors.get(self.mode, "cyan")
        
        content = Group(
            stats,
            Text(f"TENSION: [{tension_bar}] {self.tension.current:.2f}", justify="center"),
            Text(f"MOOD: {emo_str}", justify="center", style="dim")
        )
        
        self.console.print(Panel(
            content,
            style=f"bold {color}",
            border_style=f"dim {color}",
            padding=(0, 1),
            box=box.HEAVY
        ))

    def update_lights(self):
        """Update LIFX based on emotional state and mode."""
        if not self.lifx:
            return
        
        dom_emo, dom_val = self.emotions.dominant()
        intensity = self.emotions.intensity()
        brightness = min(0.3 + (intensity * 0.15), 1.0)
        
        # Mode overrides
        mode_colors = {
            Mode.FREEZE: "hue:200 saturation:1.0",
            Mode.ZOOM: "kelvin:9000",
            Mode.ESCALATE: "hue:0 saturation:1.0",
            Mode.GOD: "hue:280 saturation:1.0",
            Mode.REWIND: "hue:120 saturation:1.0",
            Mode.DIRECTOR: "hue:45 saturation:0.6",
        }
        
        if self.mode in mode_colors:
            target_color = mode_colors[self.mode]
        elif dom_val > 0.3:
            emo_hues = {"fear": 270, "rage": 0, "hope": 45, "desire": 300}
            hue = emo_hues.get(dom_emo, 0)
            target_color = f"hue:{hue} saturation:{min(dom_val, 1.0)}"
        else:
            target_color = "kelvin:3500"
        
        try:
            # Primary target: Eden (NEVER Eve - bedroom light)
            sig_eden = f"color:Eden:{target_color}:{brightness}"
            self.lifx_gate.call(
                lambda: self.lifx.set_color("label:Eden", target_color, brightness=brightness, duration=0.5),
                sig=sig_eden
            )
            
            # Adam Ad Libs (random 10% chance)
            import random
            if random.random() < 0.10:
                sig_adam = f"pulse:Adam:{target_color}"
                self.lifx_gate.call(
                    lambda: self.lifx.pulse("label:Adam", target_color, period=0.2, cycles=1),
                    sig=sig_adam
                )
        except Exception as e:
            log.warning(f"[LIFX] Update failed: {e}")

    def _lifx_worker(self):
        """Background worker for LIFX updates."""
        while True:
            _ = self._lifx_q.get()
            try:
                self.update_lights()
            except Exception as e:
                log.warning(f"LIFX worker error: {e}")
            finally:
                self._lifx_q.task_done()

    def request_lifx_update(self):
        """Queue a non-blocking LIFX update."""
        try:
            # Drain queue to ensure freshness
            while not self._lifx_q.empty():
                self._lifx_q.get_nowait()
                self._lifx_q.task_done()
            self._lifx_q.put_nowait(True)
        except Exception:
            pass

    def update_lights_async(self):
        """Deprecated alias; forwards to request_lifx_update."""
        self.request_lifx_update()

    def _build_system_prompt(self) -> str:
        """Construct dynamic system prompt with current state."""
        prompt = SYSTEM_PROMPT
        
        # State substitutions
        prompt = prompt.replace("[PHASE]", str(self.scene))
        prompt = prompt.replace("[POV]", self.pov)
        prompt = prompt.replace("[MODE]", self.mode.value.upper())
        prompt = prompt.replace("[TENSION]", f"{self.tension.current:.2f}")
        
        # Emotion state
        emo_str = ", ".join([f"{k}: {v:.2f}" for k, v in self.emotions.state.items()])
        prompt = prompt.replace("[EMOTION_STATE]", emo_str)
        
        dom_emo, dom_val = self.emotions.dominant()
        prompt = prompt.replace("[DOMINANT_EMOTION]", dom_emo.upper())
        prompt = prompt.replace("[DOMINANT_VALUE]", f"{dom_val:.2f}")
        
        # Voice hints for POV
        voice_hints = ""
        pov_lower = self.pov.lower()
        if pov_lower in VOICE_PROFILES:
            vp = VOICE_PROFILES[pov_lower]
            voice_hints = f"Style: {vp.sentence_style}. Quirks: {', '.join(vp.quirks)}."
        prompt = prompt.replace("[VOICE_HINTS]", voice_hints)
        
        # Lore files
        lore_files = [f.name for f in Path("lore").glob("*.md") if "session" not in f.name.lower()]
        lore_list = "\n".join([f"- {name}" for name in lore_files[:20]])  # Cap list
        prompt = prompt.replace("[LORE_FILES]", lore_list if lore_list else "- (No lore files found)")
        
        return prompt

    def _select_model(self, user_input: str) -> Tuple[str, str, int]:
        """Smart routing: returns (model, thinking_level, max_tokens)."""
        # Mode-based routing
        if self.mode in [Mode.FREEZE, Mode.ZOOM, Mode.SHIFT_POV]:
            # FAST SEED: Use Flash with low thinking
            return FLASH_MODEL, "low", 2048
        
        if self.mode in [Mode.GOD, Mode.DIRECTOR]:
            # DEEP REASONING: Use Pro with High thinking
            return PRO_MODEL, "high", 8192
        
        if self.mode == Mode.ESCALATE:
            # HIGH STAKES: Use Pro (Escalation requires nuance)
            return PRO_MODEL, "high", 4096
        
        # Normal mode: dynamic based on complexity signals
        complexity_score = 0
        complexity_score += len(user_input) / 100  # Length
        complexity_score += self.emotions.intensity() * 0.5  # Emotional complexity
        complexity_score += self.tension.current * 0.5  # Narrative stakes
        
        # Routing Logic:
        # > 1.5 (Complex): Pro High
        # > 0.8 (Medium): Flash Medium (Speed + some thought)
        # < 0.8 (Simple): Flash Low (Pure Speed)
        
        if complexity_score > 1.5:
            return PRO_MODEL, "high", 4096
        elif complexity_score > 0.8:
            return FLASH_MODEL, "medium", 4096 
        else:
            return FLASH_MODEL, "low", 2048

    async def generate_response(self, user_input: str) -> str:
        """Main Agent Loop - Single Turn. (v7.10 Simplified)
        
        Tool followups are handled internally by _execute_turn.
        """
        out = await self._execute_turn(user_input, tick_physics=True)
        return out.text

    async def _auto_ingest_scan(self, text: str) -> str:
        """Scan input for YouTube links and auto-ingest if found."""
        if not text: return ""
        pattern = r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})"
        links = re.findall(pattern, text)
        if not links: return ""
        
        results = []
        for vid in links:
            url = f"https://www.youtube.com/watch?v={vid}"
            note = ingest_youtube_content(url)
            results.append(note)
        
        return "\n".join(results)

    async def _execute_turn(self, user_input: str, tick_physics: bool = True, advance_scene: bool = True, allow_followup: bool = True) -> EngineResponse:
        """Generate narrative response (Single Turn)."""
        start_time = time.time()
        
        # Pre-generation state management
        if advance_scene:
            self._save_snapshot()
            await self.context.compress_if_needed()
        
        # Tick Physics & Structure (only if requested)
        structural_directives = []
        if tick_physics:
            self.emotions.tick() # (Fix C: Only tick emotions when tick_physics=True)
            if self.mode != Mode.GOD and advance_scene:
                self.tension.tick(self.scene)
                structural_directives = self.structure.tick(self.scene)
        
        # Auto-Ingest Scan (Fix: Auto-save YT links)
        eff_input = user_input if user_input else "[SYSTEM] Continue processing."
        auto_ingest_notes = await self._auto_ingest_scan(eff_input)
        if auto_ingest_notes:
            eff_input += f"\n\n[AUTO-INGEST REPORT]\n{auto_ingest_notes}"
        
        self.veil.revelation_metric = max(self.veil.revelation_metric, self.structure.progress)
        veil_directive = self.veil.get_directive()
        
        # Async Lights Update
        self.update_lights_async()
        
        # Model selection strategy
        model, thinking_level, max_tokens = self._select_model(eff_input)
        
        # [AUDIT] High Thinking override
        if self.structure.act in [3, 5] and structural_directives:
            thinking_level = "high"
            model = PRO_MODEL
            self.console.print("[bold red]>> [SYSTEM] DETECTED KEY NARRATIVE BEAT. ENGAGING DEEP REASONING.[/]")
        
        # Build System Prompt (Instruction)
        system_prompt = self._build_system_prompt()
        
        # Inject directives
        active_directives = "\n".join(f"- {d}" for d in structural_directives)
        if veil_directive:
            active_directives += f"\n- {veil_directive}"
        if active_directives:
            system_prompt += f"\n\n[PRIORITY DIRECTIVES]\n{active_directives}"
            
        # Config (System Instruction Moved Here)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.75,
            max_output_tokens=max_tokens,
            tools=ENGINE_TOOLS,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level, include_thoughts=False)
        )
        
        # Build contents (v7.10 Fix A: No duplicate user input)
        # Persist user turn to context first (if applicable)
        if advance_scene and self.mode != Mode.GOD and user_input:
            self.context.add("user", eff_input) # Save with auto-ingest notes

        # Get context (includes the user turn we just added)
        request_contents = list(self.context.get_context())
        # (Fix A: Do NOT append eff_input again - it's already in context)

        # === v7.11 NON-STREAMING TOOL LOOP ===
        # Use non-streaming to preserve thought_signature on function calls.
        # Stream only the final text response.
        
        final_text = ""
        MAX_TOOL_STEPS = 5
        tool_step = 0
        
        while tool_step < MAX_TOOL_STEPS:
            # NON-STREAMING call to preserve full Content objects with signatures
            response = self.client.models.generate_content(
                model=model,
                contents=request_contents,
                config=config
            )
            
            # Append the model's content EXACTLY as returned (preserves thought_signature)
            model_content = response.candidates[0].content
            self.context.history.append(model_content)
            request_contents.append(model_content)
            
            # Check for function calls
            fcs = getattr(response, "function_calls", None) or []
            if not fcs:
                # No tool calls - we have our final text
                final_text = response.text or ""
                break
            
            # Execute ALL function calls, then send ALL responses (no interleaving)
            self.console.print(f"[yellow]🛠 Executing {len(fcs)} tool(s)...[/]")
            tool_parts = []
            executed_names = []
            
            for fc in fcs:
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                executed_names.append(name.replace("default_api:", ""))
                
                try:
                    result = self._execute_tool(name, args)
                    tool_parts.append(types.Part.from_function_response(
                        name=name,
                        response={"result": result}
                    ))
                except Exception as e:
                    tool_parts.append(types.Part.from_function_response(
                        name=name,
                        response={"error": str(e)}
                    ))
            
            # Append ALL tool results in one Content (role="tool")
            tool_content = types.Content(role="tool", parts=tool_parts)
            self.context.history.append(tool_content)
            request_contents.append(tool_content)
            
            tool_step += 1
            self.console.print(f"[dim]   Tools {', '.join(executed_names)} completed. Continuing...[/]")
        
        # Track timing
        elapsed = time.time() - start_time
        self._generation_times.append(elapsed)
        
        if self.mode != Mode.GOD and advance_scene:
            self.scene += 1
        
        self.update_lights_async()
        return EngineResponse(text=final_text)

    def ask_yes_no(self, prompt: str) -> bool:
        """Standard Rich confirmation."""
        return Confirm.ask(prompt)

    def _execute_tool(self, fn: str, args: dict) -> str:
        """Execute a function call via ToolBus."""
        # Dispatcher logic
        def dispatch(**payload):
            # Strip namespace if present
            tool_name = fn.replace("default_api:", "")
            page_id = payload.get("page_identifier") or payload.get("page_title") or payload.get("page")
            
            if tool_name == "read_page_content":
                return read_page_content(page_id)
            
            elif tool_name == "list_universe_pages":
                return list_universe_pages()
            
            elif tool_name == "update_page_content":
                text = payload.get("text") or payload.get("content", "")
                if self.mode == Mode.GOD or os.environ.get("KAEDRA_AUTOWRITE"):
                    return update_page_content(page_id, text)

                self.console.print(Panel.fit(
                    f"[italic]\"{text[:150]}{'...' if len(text) > 150 else ''}\"[/]",
                    title=f"[bold yellow]⚠️ WRITE REQUEST: '{page_id}'[/]",
                    border_style="yellow"
                ))
                if self.ask_yes_no(">> Authorize write?"): 
                    return update_page_content(page_id, text)
                return "[Write denied by user]"

            elif tool_name == "clean_timeline_data":
                data = payload.get("data")
                return clean_timeline_data(data)
            
            elif tool_name == "propose_canon_update":
                return propose_canon_update(
                    payload.get("claim", ""),
                    float(payload.get("confidence", 0.0)),
                    payload.get("source", "unknown")
                )

            elif tool_name == "ingest_youtube_content":
                return ingest_youtube_content(payload.get("url", ""))
            
            elif tool_name == "read_local_lore":
                return read_local_lore(payload.get("filename", ""))
            
            elif tool_name == "set_engine_mode":
                mode_str = payload.get("mode", "").lower()
                for m in Mode:
                    if m.value == mode_str:
                        self.set_mode(m)
                        return f"[Mode switched to {m.value.upper()}]"
                return f"[Invalid mode: {mode_str}]"
            
            elif tool_name == "consult_director":
                topic = payload.get("topic", "general")
                if self.mode != Mode.DIRECTOR:
                    self.set_mode(Mode.DIRECTOR)
                return consult_director(topic)
            
            elif tool_name == "adjust_emotion":
                emotion = payload.get("emotion", "").lower()
                delta = float(payload.get("delta", 0))
                if emotion in self.emotions.state:
                    self.emotions.pulse(emotion, delta)
                    self.update_lights()
                    return f"[{emotion.upper()} adjusted by {delta:+.2f}, now {self.emotions.state[emotion]:.2f}]"
                return f"[Unknown emotion: {emotion}]"
            
            return f"[Unknown tool: {tool_name}]"

        return self.tool_bus.call(fn, args, dispatch)

    async def command(self, cmd_line: str) -> bool:
        """Process user commands. Returns True if handled."""
        parts = cmd_line.strip().split(maxsplit=1)
        if not parts:
            return False
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        commands = {
            "freeze": lambda: self.set_mode(Mode.FREEZE),
            "zoom": lambda: self.set_mode(Mode.ZOOM),
            "escalate": lambda: self.set_mode(Mode.ESCALATE),
            "god": lambda: self.set_mode(Mode.GOD),
            "director": lambda: self.set_mode(Mode.DIRECTOR),
            "normal": lambda: self.set_mode(Mode.NORMAL),
            "resume": lambda: self.set_mode(Mode.NORMAL),
        }
        
        if cmd in commands:
            commands[cmd]()
            return True
        
        if cmd == "pov":
            self.set_mode(Mode.SHIFT_POV)
            self.pov = args if args else Prompt.ask(">> New POV")
            self.console.print(f"[bold yellow]>> POV: {self.pov}[/]")
            return True
        
        if cmd == "next":
            self.scene += 1
            self.tension.advance_curve()
            self.set_mode(Mode.NORMAL)
            self.console.print(f"[bold]>> SCENE {self.scene}[/]")
            return True
        
        if cmd == "rewind":
            steps = int(args) if args.isdigit() else 1
            self.rewind(steps)
            return True
        
        if cmd == "emotion" and args:
            # emotion fear +0.3
            emo_parts = args.split()
            if len(emo_parts) >= 2:
                emo = emo_parts[0].lower()
                try:
                    delta = float(emo_parts[1])
                    if emo in self.emotions.state:
                        self.emotions.pulse(emo, delta)
                        self.update_lights()
                        self.console.print(f"[bold]{emo.upper()}: {self.emotions.state[emo]:.2f}[/]")
                except ValueError:
                    pass
            return True
        
        if cmd == "tension" and args:
            try:
                self.tension.target = float(args)
                self.console.print(f"[bold]Tension target: {self.tension.target:.2f}[/]")
            except ValueError:
                if args in TensionCurve.CURVES:
                    self.tension.set_curve(args)
                    self.console.print(f"[bold]Loaded curve: {args}[/]")
            return True
        
        if cmd == "debug":
            self._show_debug()
            return True
        
        if cmd == "tree":
            self._show_tree()
            return True
        
        if cmd == "coherence":
            asyncio.create_task(self._analyze_coherence())
            return True
        
        if cmd == "bridge":
            asyncio.create_task(self._bridge_gap())
            return True
        
        if cmd == "save":
            self._save_session_state(args if args else None)
            return True
        
        if cmd == "load":
            self._load_session_state(args if args else None)
            return True
        
        if cmd == "test_lights":
            self._test_lights()
            return True
        
        if cmd == "help":
            self._show_help()
            return True
            
        if cmd == "read" and args:
            # read [filename]
            # Ingests a full file as a single user turn
            path = Path(args.strip("'").strip('"'))
            if not path.exists():
                self.console.print(f"[red]File not found: {path}[/]")
                return True
            
            try:
                content = path.read_text(encoding="utf-8")
                self.console.print(f"[green]>> Ingesting {len(content)} characters from {path.name}...[/]")
                # Treat as conversational input - AWAIT to prevent fragmentation
                await self.generate_response(content)
                return True
            except Exception as e:
                self.console.print(f"[red]Read failed: {e}[/]")
                return True
        
        # MESSAGE QUEUE COMMANDS
        if cmd == "queue" and args:
            # queue [priority] message
            # e.g. "queue urgent Remember to check the lights"
            priority = "normal"
            message = args
            if args.split()[0] in ["urgent", "high", "normal", "low"]:
                priority = args.split()[0]
                message = " ".join(args.split()[1:])
            self.queue_message(message, priority)
            return True
        
        if cmd in ["checkqueue", "cq", "messages"]:
            self.process_queued_messages()
            return True
        
        return False

    def _show_debug(self):
        """Display debug information."""
        # Snapshots
        self.console.print(Panel(
            Pretty(self.snapshots[-5:] if self.snapshots else []),
            title="[bold]Recent Snapshots[/]",
            border_style="dim"
        ))
        
        # Emotions
        self.console.print(Panel(
            Pretty({
                "state": self.emotions.state,
                "momentum": self.emotions.momentum,
                "dominant": self.emotions.dominant()
            }),
            title="[bold]Emotion Engine[/]",
            border_style="dim yellow"
        ))
        
        # Tension
        self.console.print(Panel(
            Pretty({
                "current": self.tension.current,
                "target": self.tension.target,
                "velocity": self.tension.velocity
            }),
            title="[bold]Tension Curve[/]",
            border_style="dim cyan"
        ))
        
        # Performance
        if self._generation_times:
            avg_time = sum(self._generation_times) / len(self._generation_times)
            self.console.print(f"[dim]Avg generation time: {avg_time:.2f}s[/]")

    def _show_tree(self):
        """Display system topology tree."""
        root = Tree("📂 [bold]StoryEngine v6.0[/]")
        
        # State
        state = root.add("🧠 [cyan]State[/]")
        state.add(f"Scene: {self.scene}")
        state.add(f"POV: {self.pov}")
        state.add(f"Mode: {self.mode.value}")
        state.add(f"Tension: {self.tension.current:.2f}")
        
        # Emotions
        emo = root.add("⚡ [yellow]Emotions[/]")
        for k, v in self.emotions.state.items():
            if v > 0.01:
                emo.add(f"{k}: {v:.2f} (m:{self.emotions.momentum[k]:+.2f})")
        
        # Context
        ctx = root.add("📝 [green]Context[/]")
        ctx.add(f"History: {len(self.context.history)} turns")
        ctx.add(f"Summaries: {len(self.context.summaries)}")
        ctx.add(f"Snapshots: {len(self.snapshots)}")
        
        # Lore
        lore = root.add("📚 [magenta]Lore[/]")
        lore_files = list(Path("lore").glob("*.md"))
        for f in lore_files[:10]:
            if "session" not in f.name.lower():
                lore.add(f.name)
        
        self.console.print(Panel(root, border_style="green"))

    def _show_help(self):
        """Display command help."""
        help_table = Table(title="Commands", box=box.SIMPLE)
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description")
        
        cmds = [
            ("freeze", "Enter FREEZE mode (bullet-time)"),
            ("zoom", "Enter ZOOM mode (micro-detail)"),
            ("escalate", "Enter ESCALATE mode (raise stakes)"),
            ("god", "Enter GOD mode (worldbuilding)"),
            ("director", "Enter DIRECTOR mode (screenwriting)"),
            ("normal/resume", "Return to NORMAL mode"),
            ("pov [name]", "Shift POV to character"),
            ("next", "Advance to next scene"),
            ("rewind [n]", "Rewind n snapshots"),
            ("emotion [type] [±delta]", "Adjust emotion (fear/hope/rage/desire)"),
            ("tension [0-1|curve]", "Set tension target or load curve"),
            ("coherence", "Analyze lore consistency"),
            ("bridge", "Generate content to fill narrative gaps"),
            ("debug", "Show internal state"),
            ("tree", "Show system topology"),
            ("save [name]", "Save session state"),
            ("load [name]", "Load session state"),
            ("read [file]", "Ingest large text file as single input"),
            ("test_lights", "LIFX diagnostic"),
            ("queue [priority] msg", "Queue message for later (urgent/high/normal)"),
            ("checkqueue / cq", "View and clear queued messages"),
            ("exit/quit", "End session"),
        ]
        
        for cmd, desc in cmds:
            help_table.add_row(cmd, desc)
        
        self.console.print(help_table)

    def _save_session_state(self, name: Optional[str] = None):
        """Export session state to JSON."""
        filename = name or f"session_{datetime.now().strftime('%Y%m%d_%H%M')}"
        path = self.log_dir / f"{filename}.json"
        
        state = {
            "version": "6.0",
            "scene": self.scene,
            "pov": self.pov,
            "mode": self.mode.value,
            "tension": {
                "current": self.tension.current,
                "target": self.tension.target
            },
            "emotions": self.emotions.serialize(),
            "snapshots": [s.to_dict() for s in self.snapshots[-10:]],
            "context_summaries": self.context.summaries,
        }
        
        path.write_text(json.dumps(state, indent=2))
        self.console.print(f"[green]>> Saved: {path}[/]")

    def _load_session_state(self, name: Optional[str] = None):
        """Import session state from JSON."""
        if not name:
            # List available
            saves = list(self.log_dir.glob("*.json"))
            if not saves:
                self.console.print("[yellow]No saved sessions found.[/]")
                return
            self.console.print("[bold]Available saves:[/]")
            for s in saves[-10:]:
                self.console.print(f"  - {s.stem}")
            return
        
        path = self.log_dir / f"{name}.json"
        if not path.exists():
            self.console.print(f"[red]Not found: {path}[/]")
            return
        
        try:
            state = json.loads(path.read_text())
            self.scene = state["scene"]
            self.pov = state["pov"]
            self.mode = Mode(state["mode"])
            self.tension.current = state["tension"]["current"]
            self.tension.target = state["tension"]["target"]
            self.emotions.deserialize(state["emotions"])
            self.context.summaries = state.get("context_summaries", [])
            
            self.console.print(f"[green]>> Loaded: {path}[/]")
            self.update_lights()
        except Exception as e:
            self.console.print(f"[red]Load failed: {e}[/]")

    def _test_lights(self):
        """Run LIFX diagnostic."""
        if not self.lifx:
            self.console.print("[red]LIFX not initialized[/]")
            return
        
        self.console.print("[bold]Running LIFX diagnostic...[/]")
        colors = [("red", "Fear"), ("blue", "Freeze"), ("purple", "God"), ("green", "Hope")]
        
        for color, label in colors:
            self.console.print(f"  [{color}]● {label}[/]")
            try:
                # Eden primary, Adam secondary (NEVER Eve)
                self.lifx.set_color("label:Eden", color, brightness=1.0, duration=0.3)
                self.lifx.pulse("label:Adam", color, period=0.2, cycles=1)
                time.sleep(0.5)
            except Exception as e:
                self.console.print(f"    [red]Error: {e}[/]")
        
        # Restore Eden + Adam only
        self.lifx.set_color("label:Eden", "kelvin:3500", brightness=0.5, duration=1.0)
        self.lifx.set_color("label:Adam", "kelvin:3500", brightness=0.5, duration=1.0)
        self.console.print("[green]Diagnostic complete[/]")

    async def _analyze_coherence(self):
        """Analyze lore file consistency."""
        self.console.print(Panel("[bold magenta]COHERENCE ANALYSIS[/]", style="magenta"))
        
        lore_dir = Path("lore")
        if not lore_dir.exists():
            self.console.print("[red]lore/ directory not found[/]")
            return
        
        files = [f for f in lore_dir.glob("*.md") if "session" not in f.name.lower()]
        if not files:
            self.console.print("[yellow]No lore files found[/]")
            return
        
        # Gather lore
        lore_text = ""
        with self.console.status(f"[cyan]Reading {len(files)} files...[/]"):
            for f in files[:15]:  # Cap at 15 files
                content = f.read_text(encoding="utf-8")[:4000]
                lore_text += f"\n=== {f.name} ===\n{content}\n"
        
        prompt = f"""[COHERENCE ANALYZER]
Analyze these lore files for narrative consistency.

{lore_text}

OUTPUT (Markdown):
1. **TIMELINE**: Identify distinct eras/timelines
2. **CROSSOVERS**: Characters/artifacts appearing in multiple files
3. **CONTRADICTIONS**: Direct conflicts between files
4. **GAPS**: Missing connections or unexplained jumps
5. **REPAIR PROMPTS**: 3 specific prompts to bridge gaps (format: "PROMPT: <text>")
6. **SCORE**: 0-100% coherence rating"""

        with self.console.status("[magenta]Analyzing...[/]", spinner="arc"):
            try:
                response = self.client.models.generate_content(
                    model=PRO_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=4096
                    )
                )
                
                analysis = response.candidates[0].content.parts[0].text
                self.last_coherence_report = analysis
                
                self.console.print(Panel(
                    Markdown(analysis),
                    title="[bold]COHERENCE REPORT[/]",
                    border_style="magenta",
                    box=box.DOUBLE
                ))
            except Exception as e:
                log.exception("Coherence analysis failed")

    def _should_pulse_lights(self, text_chunk: str) -> bool:
        """Detect emotional triggers in streaming text."""
        triggers = {
            "fear": r"\b(terror|scream|blood|death|panic)\b",
            "rage": r"\b(fury|rage|kill|destroy|hatred)\b",
            "hope": r"\b(hope|light|dawn|salvation|peace)\b",
        }
        for emotion, pattern in triggers.items():
            if re.search(pattern, text_chunk, re.I):
                self.emotions.pulse(emotion, 0.05)  # Micro-pulse
                return True
        return False

    async def _bridge_gap(self):
        """Generate content to fill narrative voids."""
        if not hasattr(self, 'last_coherence_report'):
            self.console.print("[red]Run 'coherence' first[/]")
            return
        
        matches = re.findall(r"PROMPT: (.+?)(?:\n|$)", self.last_coherence_report)
        if not matches:
            self.console.print("[yellow]No repair prompts found in report[/]")
            return
        
        self.console.print("[bold]Repair options:[/]")
        for i, m in enumerate(matches, 1):
            self.console.print(f"  {i}. [italic]{m}[/]")
        
        choice = Prompt.ask("Select", default="1")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(matches):
            return
        
        selected = matches[int(choice) - 1]
        
        with self.console.status("[green]Generating bridge...[/]"):
            try:
                response = self.client.models.generate_content(
                    model=PRO_MODEL,
                    contents=f"""Write a lore file (Markdown) for the Veil Verse to bridge this gap:

{selected}

Format:
# [Title]
**Type:** [Scene/Journal/Log/Artifact]

[Content]""",
                    config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=2048)
                )
                
                content = response.candidates[0].content.parts[0].text
                
                # Save
                title_match = re.search(r"# (.+)", content)
                safe_title = "bridge_" + (
                    title_match.group(1).strip().lower().replace(" ", "_")[:30]
                    if title_match else str(int(time.time()))
                )
                safe_title = "".join(c for c in safe_title if c.isalnum() or c in "_-")
                
                path = Path("lore") / f"{safe_title}.md"
                path.write_text(content, encoding="utf-8")
                
                self.console.print(Panel(
                    Markdown(content[:800] + "..."),
                    title=f"[green]Created: {path}[/]",
                    border_style="green"
                ))
            except Exception as e:
                log.exception("Bridge generation failed")

    def _restore_lights(self):
        """Restore lights to initial state on exit."""
        if not self.lifx or not self.initial_light_state:
            return
        
        try:
            for light in track(self.initial_light_state, description="[dim]Restoring lights...[/]"):
                # NEVER touch Eve (bedroom light)
                if light.label.lower() == "eve":
                    continue
                    
                selector = f"id:{light.id}"
                if light.power == 'off':
                    self.lifx.turn_off(selector, duration=2.0)
                else:
                    c = light.color
                    color_str = f"hue:{c.get('hue', 0)} saturation:{c.get('saturation', 0)} kelvin:{c.get('kelvin', 3500)}"
                    self.lifx.set_state(
                        selector, 
                        power="on", 
                        color=color_str, 
                        brightness=light.brightness, 
                        duration=2.0
                    )
        except Exception as e:
            log.warning(f"Light restore failed: {e}")

    def _read_multiline_json(self, first_line: str, max_lines: int = 500) -> Tuple[str, Optional[Any]]:
        """Read a full JSON value starting from first_line."""
        buf = [first_line]
        dec = json.JSONDecoder()

        for _ in range(max_lines):
            raw = "\n".join(buf).strip()
            try:
                obj, idx = dec.raw_decode(raw)
                if raw[idx:].strip() == "":
                    return raw, obj
            except json.JSONDecodeError:
                pass
            
            # Keep reading lines
            try:
                next_line = self.console.input("") 
                buf.append(next_line)
            except EOFError:
                break
            
        return "\n".join(buf), None

    def save_json_payload(self, payload: dict, out_dir="exports") -> str:
        """Save JSON payload to disk with timestamp."""
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(out_dir) / f"json_capture_{ts}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    async def run(self):
        """Main engine loop."""
        # Banner
        banner = Table.grid(expand=True)
        banner.add_column(justify="center")
        banner.add_row(Text("🧠 STORYTIME ENGINE v6.0", style="bold white"))
        banner.add_row(Text("Emotion Physics | Tension Curves | Smart Routing", style="dim"))
        
        self.console.print(Panel(
            banner,
            subtitle="[dim]Type 'help' for commands[/]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        # Status checks
        if self.notion.client:
            log.info("[green]Notion: Connected[/]", extra={"markup": True})
        if self.lifx:
            log.info("[green]LIFX: Connected[/]", extra={"markup": True})
            
        self.header()
        
        # Loop
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]>>[/] ").strip()
                if not user_input:
                    continue
                
                if user_input.lower() in ["exit", "quit"]:
                    self.console.print("[italic]Saving session and deactivating...[/]")
                    self._save_session_state("final_shutdown")
                    self._restore_lights()
                    break
                
                # [PATCH] Check for JSON Paste
                if user_input.startswith("{") or user_input.startswith("["):
                     self.console.print("[dim]>> Detected JSON. Reading...[/]")
                     raw_json, parsed = self._read_multiline_json(user_input)
                     
                     if parsed:
                         saved_path = self.save_json_payload(parsed)
                         self.console.print(f"[green]>> JSON Saved: {saved_path}[/]")
                     
                     output = await self.generate_response(raw_json)
                     if output:
                         self.console.print(Panel(Markdown(output), border_style="dim cyan"))
                     self.header()
                     continue
                
                # [PATCH] Check for @file
                if user_input.startswith("@"):
                     path_str = user_input[1:].strip()
                     # If quotes, strip them
                     path_str = path_str.strip("'").strip('"')
                     path = Path(path_str)
                     if path.exists():
                         self.console.print(f"[dim]>> Reading {path}...[/]")
                         content = path.read_text(encoding="utf-8")
                         output = await self.generate_response(content)
                         if output:
                            self.console.print(Panel(Markdown(output), border_style="dim cyan"))
                         self.header()
                         continue
                     else:
                         self.console.print(f"[red]File not found: {path}[/]")
                         continue
                
                # Check for command
                if await self.command(user_input):
                    self.header() # Refresh state
                    continue
                
                # Assume conversational input
                output = await self.generate_response(user_input)
                if output:
                    self.console.print(Panel(Markdown(output), border_style="dim cyan"))
                self.header() # Update header after response
                
                # Check for queued messages (auto-check on 5min timeout)
                queued = self.check_queue()
                if queued:
                    self.console.print(f"\n[bold yellow]📬 {len(queued)} queued message(s) arrived:[/]")
                    for msg in queued:
                        pri = msg.get('priority', 'normal')
                        color = 'red' if pri == 'urgent' else 'yellow' if pri == 'high' else 'cyan'
                        self.console.print(f"  [{color}]• {msg['text']}[/]")
                
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[italic]Interrupt received. Saving session and deactivating...[/]")
                try: self._save_session_state("final_shutdown")
                except: pass
                try: self._restore_lights()
                except: pass
                break
            except Exception as e:
                log.exception("Fatal error in main loop")
                self.console.print(Panel.fit(f"[red]Fatal error:[/] {e}", border_style="red"))
                continue

if __name__ == "__main__":
    try:
        engine = StoryEngine()
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        pass
