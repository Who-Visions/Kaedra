import argparse
import asyncio
import io
import wave
import time
import json
import re
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from enum import Enum

import vertexai
from vertexai.generative_models import GenerativeModel, Part

from kaedra.core.config import PROJECT_ID, LIFX_TOKEN
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.agents.kaedra import KAEDRA_PROFILE

# Optional: LIFX integration
try:
    from kaedra.services.lifx import LIFXService
    LIFX_AVAILABLE = bool(LIFX_TOKEN)
except ImportError:
    LIFX_AVAILABLE = False



# ═══════════════════════════════════════════════════════════════════════════════
# RICH DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich import box

class KaedraDashboard:
    def __init__(self):
        self.console = Console()
        self.status = "INITIALIZING"
        self.mic_status = "OFF"
        self.active_lights = []
        self.last_latency = 0.0
        self.last_tokens = 0
        self.total_cost = 0.0

    def set_status(self, status: str, color: str = "white"):
        self.status = f"[{color}]{status}[/{color}]"

    def set_mic(self, status: str):
        self.mic_status = status

    def set_lights(self, lights: list):
        self.active_lights = lights

    def update_stats(self, latency: float, tokens: int, cost: float):
        self.last_latency = latency
        self.last_tokens = tokens
        self.total_cost = cost

    def start_stream(self, role: str, color: str = "magenta"):
        self.console.print(f"[{color}]{role}:[/{color}] ", end="")

    def print_stream(self, text: str, color: str = "magenta"):
        self.console.print(f"[{color}]{text}[/{color}]", end="")
    
    def end_stream(self):
        self.console.print() # Newline

    def update_history(self, role: str, message: str, color: str = "white"):
        # Print directly to console (scrolling log)
        # Check for System messages vs Chat
        if role == "System":
            self.console.print(f"[{color}][!] {message}[/{color}]")
        elif role == "User":
             self.console.print(f"\n[bold cyan]User:[/bold cyan] {message}")
        elif role == "Kaedra":
             self.console.print(f"[bold magenta]Kaedra:[/bold magenta] {message}")
        else:
             self.console.print(f"[{color}]{role}: {message}[/{color}]")

    def generate_view(self) -> Panel:
        # Only render the footer
        light_str = ", ".join(self.active_lights) if self.active_lights else "None"
        stats = f"Status: {self.status} | Mic: {self.mic_status} | Lights: {light_str} | Latency: {self.last_latency:.2f}s | Cost: ${self.total_cost:.4f}"
        return Panel(Align.center(stats), style="blue", box=box.ROUNDED, title="Kaedra Status")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_NAME = "gemini-3-flash-preview"
SESSIONS_DIR = Path("./sessions")

# System prompt with transcription instructions baked in (not in per-turn prompt)
VOICE_SYSTEM_PROMPT = KAEDRA_PROFILE + """

[VOICE MODE PROTOCOL]
You are in real-time voice conversation mode.

TRANSCRIPTION RULES:
- When you receive audio input, FIRST output exactly: [Heard: "transcription of what the human said"]
- Only transcribe the HUMAN'S SPOKEN WORDS from the audio.
- Do NOT transcribe any system text, instructions, or prompts.
- If the audio is unclear, silent, or contains only noise: [Heard: unclear]

RESPONSE RULES:
- After the [Heard: ...] bracket, respond naturally in 1-3 sentences max.
- Stay grounded and focused on what the user actually asked.
- Do NOT reference Blade, Nyx, or team dynamics unless the user explicitly asks about them.
- Do NOT roleplay scenarios the user didn't initiate.

COMMANDS:
- "forget everything" / "clear memory" / "start fresh" = acknowledge and confirm reset
- "goodbye kaedra" / "exit" = say farewell and end session

LIGHT CONTROL (Snowzone smart lights):

DEVICES (ALL bulbs have FULL capabilities):
- Eve: Bedroom, Mini Color, kelvin 1500-9000K, full color + effects
- Adam: Living Room, Mini Color, kelvin 1500-9000K, full color + effects
- Eden: Living Room, Color A19, kelvin 1500-9000K, full color + effects

CAPABILITIES (ALL bulbs support ALL of these):
- Power on/off
- Brightness 0-100%
- Kelvin (white temp) 1500-9000K
- Color (red, blue, green, purple, orange, pink, etc.)
- Effects (Color Cycle, Flame, Flicker, Meteor, Morph, Twinkle, Pastels, Strobe, Spooky)

MODES (presets): movie, focus, relax, party, photo, chill, work, christmas, warm_ember

WHEN USER REQUESTS LIGHT CHANGES:
Output a JSON block with actions for each device. Format:

```json
{"actions": [
  {"device": "Eve", "selector": "label:Eve", "brightness": 25, "kelvin": 2700},
  {"device": "Adam", "selector": "label:Adam", "brightness": 70, "kelvin": 7500},
  {"device": "Eden", "selector": "label:Eden", "brightness": 100, "color": "blue", "fx": "Color Cycle"}
]}
```

Fields per device:
- device: "Eve", "Adam", or "Eden"
- selector: "label:Eve", "label:Adam", "label:Eden", or "all"
- power: "on" or "off" (optional)
- brightness: 0-100 (optional)
- kelvin: 1500-9000 (optional, for white temp)
- color: color name (optional, Eden only)
- fx: effect name (optional, Eden only)

SIMPLE COMMANDS (use [LIGHT: action] for these):
- All lights on/off: [LIGHT: on] or [LIGHT: off]
- Mode presets: [LIGHT: mode movie], [LIGHT: mode chill], etc.
- Relative: [LIGHT: brighter], [LIGHT: dimmer], [LIGHT: warmer], [LIGHT: cooler]
"""


class SessionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    COOLDOWN = "cooldown"


@dataclass
class ConversationTurn:
    turn_id: int
    timestamp: str
    user_audio_kb: float
    user_audio_seconds: float
    transcription: str
    response: str
    inference_time: float
    tokens_used: int = 0


@dataclass
class SessionStats:
    start_time: float = field(default_factory=time.time)
    total_turns: int = 0
    successful_turns: int = 0
    total_tokens: int = 0
    total_inference_time: float = 0
    total_audio_seconds: float = 0
    hallucinations_caught: int = 0
    feedback_rejected: int = 0
    errors: int = 0

    def summary(self) -> str:
        duration = time.time() - self.start_time
        avg_inference = self.total_inference_time / max(1, self.successful_turns)
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    SESSION SUMMARY                           ║
╠══════════════════════════════════════════════════════════════╣
║  Duration:          {duration/60:.1f} minutes
║  Total Attempts:    {self.total_turns}
║  Successful Turns:  {self.successful_turns}
║  Hallucinations:    {self.hallucinations_caught} caught
║  Feedback Rejected: {self.feedback_rejected}
║  Total Audio:       {self.total_audio_seconds:.1f}s processed
║  Avg Inference:     {avg_inference:.2f}s per turn
║  Est. Tokens:       ~{self.total_tokens:,}
║  Est. Cost:         ${(self.total_tokens / 1_000_000) * 1.75:.4f}
║  Errors:            {self.errors}
╚══════════════════════════════════════════════════════════════╝"""


@dataclass
class AudioConfig:
    wake_threshold: int = 500
    silence_threshold: int = 400
    silence_duration: float = 0.6
    max_record_seconds: float = 30.0
    post_speech_cooldown: float = 3.0  # Ignore mic for N seconds after TTS
    feedback_rms_threshold: int = 3000  # RMS above this right after TTS = feedback


@dataclass
class SessionConfig:
    max_history_turns: int = 10
    save_transcripts: bool = True
    tts_variant: str = "flash-lite"
    retry_attempts: int = 3
    retry_delay: float = 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def create_wav_buffer(audio_data: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM audio in WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)
    return buf.getvalue()


def estimate_speech_duration(text: str, wps: float = 2.8) -> float:
    """Estimate TTS playback duration."""
    words = len(text.split())
    return max(1.0, min((words / wps) + 0.8, 15.0))


def extract_transcription(response: str) -> tuple[str, str]:
    """Extract [Heard: "..."] from response."""
    import re
    match = re.search(r'\[Heard:\s*["\']?([^"\'\]]*)["\']?\]', response, re.IGNORECASE)
    if match:
        transcription = match.group(1).strip()
        cleaned = re.sub(r'\[Heard:[^\]]*\]\s*', '', response).strip()
        return transcription, cleaned
    return "", response


def check_reset_intent(text: str) -> bool:
    """Check if user requested memory reset."""
    reset_phrases = [
        "forget everything", "clear memory", "start fresh", "start over",
        "reset", "new conversation", "forget that", "clear history"
    ]
    return any(phrase in text.lower() for phrase in reset_phrases)


def check_exit_intent(text: str) -> bool:
    """Check if user wants to exit."""
    exit_phrases = ["goodbye kaedra", "exit", "quit", "shut down", "stop listening"]
    return any(phrase in text.lower() for phrase in exit_phrases)


def is_prompt_leak(transcription: str) -> bool:
    """Detect if she transcribed the instruction instead of user speech."""
    leak_indicators = [
        "listen carefully",
        "transcribe what you heard",
        "respond naturally",
        "first transcribe",
        "in brackets"
    ]
    return any(indicator in transcription.lower() for indicator in leak_indicators)


def extract_light_command(response: str) -> tuple[Optional[str], Optional[list], str]:
    """
    Extract light commands from response.
    Returns (simple_action, json_actions, cleaned_response).
    
    Supports:
    1. Simple tags: [LIGHT: on], [LIGHT: mode movie]
    2. JSON actions: {"actions": [...]}
    """
    import re
    
    # Device name to selector map
    DEVICE_MAP = {
        "eve": "label:Eve",
        "adam": "label:Adam", 
        "eden": "label:Eden",
        "all": "all",
        "bedroom": "label:Eve",
        "living room": "group:Living Room",
        "living_room": "group:Living Room"
    }
    
    cleaned = response
    
    # Try to extract JSON actions first
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
    if not json_match:
        json_match = re.search(r'(\{"actions":\s*\[.*?\]\})', response, re.DOTALL)
    
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            actions = data.get("actions", [])
            
            # Validate and normalize each action
            validated_actions = []
            for action in actions:
                validated = validate_light_action(action, DEVICE_MAP)
                if validated:
                    validated_actions.append(validated)
            
            # Clean JSON from response
            cleaned = re.sub(r'```json\s*\{.*?\}\s*```', '', response, flags=re.DOTALL).strip()
            cleaned = re.sub(r'\{"actions":\s*\[.*?\]\}', '', cleaned, flags=re.DOTALL).strip()
            
            if validated_actions:
                return None, validated_actions, cleaned
        except json.JSONDecodeError:
            pass  # Fall through to simple tag parsing
    
    # Try simple [LIGHT: action] tag
    match = re.search(r'\[LIGHT:\s*([^\]]+)\]', response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        cleaned = re.sub(r'\[LIGHT:[^\]]*\]\s*', '', response).strip()
        return action, None, cleaned
    
    return None, None, response


def validate_light_action(action: dict, device_map: dict) -> Optional[dict]:
    """
    Validate and normalize a light action.
    Returns validated action dict or None if invalid.
    """
    validated = {}
    
    # Resolve device name to selector
    device = action.get("device", "").lower()
    selector = action.get("selector", "")
    
    if device in device_map:
        validated["selector"] = device_map[device]
    elif selector:
        validated["selector"] = selector
    else:
        validated["selector"] = "all"
    
    # Power
    if "power" in action:
        validated["power"] = "on" if action["power"] in ["on", True, 1] else "off"
    
    # Brightness: clamp 0-100, normalize to 0-1 if needed
    if "brightness" in action:
        bri = action["brightness"]
        if isinstance(bri, (int, float)):
            if bri > 1:  # Assume percent
                bri = max(0, min(100, bri)) / 100
            else:
                bri = max(0.0, min(1.0, bri))
            validated["brightness"] = bri
    
    # Kelvin: clamp 1500-9000
    if "kelvin" in action:
        kelvin = action["kelvin"]
        if isinstance(kelvin, (int, float)):
            validated["kelvin"] = max(1500, min(9000, int(kelvin)))
    
    # Color (string passthrough)
    if "color" in action:
        validated["color"] = str(action["color"])
    
    # Effects (string passthrough)
    if "fx" in action:
        validated["fx"] = str(action["fx"])
    
    return validated if validated else None


def execute_light_command(lifx, action: str) -> bool:
    """
    Execute a light command.
    Returns True if command was executed, False otherwise.
    """
    try:
        parts = action.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in ["on", "turn on"]:
            lifx.turn_on()
            print("[💡] Lights ON")
        elif cmd in ["off", "turn off"]:
            lifx.turn_off()
            print("[💡] Lights OFF")
        elif cmd == "toggle":
            lifx.toggle()
            print("[💡] Lights TOGGLED")
        elif cmd == "color" and args:
            color = " ".join(args)
            lifx.set_color("all", color)
            print(f"[💡] Color: {color}")
        elif cmd == "dim" and args:
            try:
                percent = int(args[0].replace("%", ""))
                lifx.dim("all", percent)
                print(f"[💡] Brightness: {percent}%")
            except ValueError:
                pass
        elif cmd == "brightness" and args:
            try:
                level = float(args[0])
                lifx.set_brightness("all", level)
                print(f"[💡] Brightness: {level}")
            except ValueError:
                pass
        elif cmd == "brighter":
            lifx.brighter()
            print("[💡] Brighter")
        elif cmd == "dimmer":
            lifx.dimmer()
            print("[💡] Dimmer")
        elif cmd == "warmer":
            lifx.warmer()
            print("[💡] Warmer")
        elif cmd == "cooler":
            lifx.cooler()
            print("[💡] Cooler")
        elif cmd == "mode" and args:
            mode = args[0]
            if mode == "movie":
                lifx.movie_mode()
                print("[💡] Movie mode")
            elif mode == "focus":
                lifx.focus_mode()
                print("[💡] Focus mode")
            elif mode == "relax":
                lifx.relax_mode()
                print("[💡] Relax mode")
            elif mode == "party":
                lifx.party_mode()
                print("[💡] Party mode")
            elif mode == "photo":
                lifx.photo_mode()
                print("[💡] Photo mode")
            elif mode == "chill":
                lifx.chill_mode()
                print("[💡] Chill mode")
            elif mode == "work":
                lifx.work_mode()
                print("[💡] Work mode")
            elif mode == "christmas":
                lifx.christmas_mode()
                print("[💡] Christmas mode")
            elif mode in ["ember", "warm"]:
                lifx.warm_ember()
                print("[💡] Warm ember mode")
        # Room selectors
        elif cmd == "bedroom":
            sub_cmd = args[0] if args else "on"
            if sub_cmd == "off":
                lifx.turn_off(lifx.BEDROOM)
            else:
                lifx.turn_on(lifx.BEDROOM)
            print(f"[💡] Bedroom: {sub_cmd}")
        elif cmd in ["living", "livingroom"] or (cmd == "living" and args and args[0] == "room"):
            sub_args = args[1:] if args and args[0] == "room" else args
            sub_cmd = sub_args[0] if sub_args else "on"
            if sub_cmd == "off":
                lifx.turn_off(lifx.LIVING_ROOM)
            else:
                lifx.turn_on(lifx.LIVING_ROOM)
            print(f"[💡] Living room: {sub_cmd}")
        elif cmd == "breathe" and args:
            color = " ".join(args)
            lifx.breathe("all", color)
            print(f"[💡] Breathe: {color}")
        elif cmd == "pulse" and args:
            color = " ".join(args)
            lifx.pulse("all", color)
            print(f"[💡] Pulse: {color}")
        elif cmd == "sunrise":
            duration = int(args[0]) if args else 300
            lifx.sunrise("all", duration)
            print(f"[💡] Sunrise: {duration}s")
        elif cmd == "sunset":
            duration = int(args[0]) if args else 300
            lifx.sunset("all", duration)
            print(f"[💡] Sunset: {duration}s")
        elif cmd == "effects" and args and args[0] == "off":
            lifx.effects_off()
            print("[💡] Effects OFF")
        else:
            print(f"[💡] Unknown light command: {action}")
            return False
        
        return True
    except Exception as e:
        print(f"[!] Light command error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationManager:
    """Handles history, pruning, and persistence."""

    def __init__(self, model: GenerativeModel, config: SessionConfig):
        self.model = model
        self.config = config
        self.chat = model.start_chat(history=[])
        self.turns: list[ConversationTurn] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def reset(self):
        """Clear history and start fresh."""
        self.chat = self.model.start_chat(history=[])
        self.turns = []

    def rollback(self, to_size: int):
        """Rollback history to a previous size."""
        if len(self.chat.history) > to_size:
            self.chat = self.model.start_chat(history=list(self.chat.history[:to_size]))

    def prune_history(self):
        """Trim history to max_history_turns (exchanges, not entries)."""
        max_entries = self.config.max_history_turns * 2
        if len(self.chat.history) > max_entries:
            trimmed = list(self.chat.history[-max_entries:])
            self.chat = self.model.start_chat(history=trimmed)
            return True
        return False

    def add_turn(self, turn: ConversationTurn):
        self.turns.append(turn)

    def save_transcript(self):
        """Save conversation to JSON."""
        if not self.config.save_transcripts or not self.turns:
            return None

        SESSIONS_DIR.mkdir(exist_ok=True)
        filepath = SESSIONS_DIR / f"kaedra_session_{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "turns": [
                {
                    "id": t.turn_id,
                    "time": t.timestamp,
                    "user": t.transcription,
                    "kaedra": t.response,
                    "inference_ms": int(t.inference_time * 1000)
                }
                for t in self.turns
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return filepath

    @property
    def history_size(self) -> int:
        return len(self.chat.history)


# ═══════════════════════════════════════════════════════════════════════════════
# VOICE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class KaedraVoiceEngine:
    """Main voice conversation engine."""

    def __init__(
        self,
        mic: MicrophoneService,
        tts: TTSService,
        conversation: ConversationManager,
        audio_config: AudioConfig,
        session_config: SessionConfig,
        lifx: Optional["LIFXService"] = None
    ):
        self.mic = mic
        self.tts = tts
        self.conversation = conversation
        self.audio_config = audio_config
        self.session_config = session_config
        self.lifx = lifx
        self.stats = SessionStats()
        self.state = SessionState.IDLE
        self._should_stop = False
        self._last_tts_end_time: float = 0
        self.dashboard = KaedraDashboard()

    async def run(self):
        """Main conversation loop."""
        self.dashboard.console.print(self._banner()) 

        with Live(self.dashboard.generate_view(), refresh_per_second=10, console=self.dashboard.console) as live:
            self.live = live
            self.dashboard.set_status("Listening...", "green")
            self.live.update(self.dashboard.generate_view())
            
            try:
                while not self._should_stop:
                    self.live.update(self.dashboard.generate_view())
                    await self._conversation_turn()
            except KeyboardInterrupt:
                pass
            finally:
                await self._shutdown()

    async def _conversation_turn(self):
        """Execute one full conversation turn (Streaming)."""
        self.stats.total_turns += 1
        turn_id = self.stats.total_turns

        # 1. LISTEN (with cooldown check)
        self.state = SessionState.IDLE
        pruned = self.conversation.prune_history()
        
        self.dashboard.set_status(f"Listening", "green")
        if pruned:
            self.dashboard.set_status("Listening (Pruned)", "green")
        self.live.update(self.dashboard.generate_view())

        # Wait for speech
        self.mic.wait_for_speech(threshold=self.audio_config.wake_threshold)
        
        # Check cooldown
        time_since_tts = time.time() - self._last_tts_end_time
        if time_since_tts < self.audio_config.post_speech_cooldown:
            self.dashboard.set_status(f"Cooldown ({time_since_tts:.1f}s)", "yellow")
            self.live.update(self.dashboard.generate_view())
            self.stats.feedback_rejected += 1
            await asyncio.sleep(self.audio_config.post_speech_cooldown - time_since_tts)
            return

        self.state = SessionState.LISTENING
        self.dashboard.set_status("Recording...", "red")
        self.live.update(self.dashboard.generate_view())

        audio_data = self.mic.listen_until_silence(
            silence_threshold=self.audio_config.silence_threshold,
            silence_duration=self.audio_config.silence_duration
        )

        audio_kb = len(audio_data) / 1024
        audio_seconds = len(audio_data) / (self.mic.sample_rate * 2)
        self.stats.total_audio_seconds += audio_seconds
        
        self.dashboard.set_mic(f"{audio_seconds:.1f}s")
        self.live.update(self.dashboard.generate_view())

        if audio_seconds > 30:
            self.dashboard.update_history("System", f"Recording too long ({audio_seconds:.1f}s)", "yellow")
            return

        # 2. STREAMING INFERENCE
        self.state = SessionState.PROCESSING
        self.dashboard.set_status("Streaming...", "cyan")
        self.live.update(self.dashboard.generate_view())
        
        wav_data = create_wav_buffer(audio_data, self.mic.sample_rate)
        history_before = self.conversation.history_size
        
        try:
            audio_part = Part.from_data(wav_data, mime_type="audio/wav")
            stream = await self.conversation.chat.send_message_async([audio_part], stream=True)
            
            # Streaming State
            preamble_buffer = ""
            response_buffer = ""
            in_preamble = True
            turn_aborted = False
            
            # Latency Tracking
            t0 = time.time()
            first_token_time = 0.0
            
            self.dashboard.start_stream("Kaedra")
            
            async for chunk in stream:
                text = chunk.text
                if not text: continue
                
                if first_token_time == 0:
                     first_token_time = time.time() - t0
                     self.dashboard.last_latency = first_token_time

                if in_preamble:
                    preamble_buffer += text
                    if "]" in preamble_buffer:
                        in_preamble = False
                        transcription, rest = extract_transcription(preamble_buffer)
                        self.dashboard.update_history("User", transcription, "dim white")
                        
                        # Check Intents immediately
                        if check_exit_intent(transcription):
                            turn_aborted = True
                            await self._speak_and_wait("Aight Dave, I'm out. Kaedra out.")
                            self._should_stop = True
                            break
                        if check_reset_intent(transcription):
                            turn_aborted = True
                            self.conversation.reset()
                            await self._speak_and_wait("Memory wiped.")
                            break
                        if is_prompt_leak(transcription):
                            turn_aborted = True
                            self.dashboard.update_history("System", "Prompt leak detected", "red")
                            break

                        # Process leftover text (Start of response)
                        if rest:
                            self.dashboard.start_stream("Kaedra")
                            self.dashboard.print_stream(rest)
                            response_buffer += rest
                else:
                    self.dashboard.print_stream(text)
                    response_buffer += text
                    
                    # Check safe split (Avoid splitting JSON/Tags)
                    balanced = (response_buffer.count("{") == response_buffer.count("}") and 
                                response_buffer.count("[") == response_buffer.count("]"))
                                
                    if balanced and (re.search(r'[.!?]\s', response_buffer) or re.search(r'[.!?]$', response_buffer)):
                        sentences = re.split(r'(?<=[.!?])\s+', response_buffer)
                        # Keep last chunk if potentially incomplete
                        if len(sentences) > 1:
                            to_speak = sentences[:-1]
                            response_buffer = sentences[-1]
                            
                            for s in to_speak:
                                if not s.strip(): continue
                                # Check for lights
                                simple, json_acts, clean = extract_light_command(s)
                                
                                # SPEAK Clean Text
                                if clean.strip():
                                    await asyncio.to_thread(self.tts.speak, clean)
                                
                                # EXECUTE Lights
                                if self.lifx and (simple or json_acts):
                                    async def bg_lights(j, k):
                                        try:
                                             if k: 
                                                 await asyncio.to_thread(execute_light_command, self.lifx, k)
                                                 self.dashboard.set_lights([k])
                                             if j: 
                                                 await asyncio.to_thread(self.lifx.set_states, j)
                                                 d = [a.get("selector", "?").replace("label:", "") for a in j]
                                                 self.dashboard.set_lights(d)
                                             self.live.update(self.dashboard.generate_view())
                                        except: pass
                                    asyncio.create_task(bg_lights(json_acts, simple))
            
            self.dashboard.end_stream()
            
            if turn_aborted: return

            # Process remaining buffer
            if response_buffer.strip():
                simple, json_acts, clean = extract_light_command(response_buffer)
                if clean.strip():
                    await asyncio.to_thread(self.tts.speak, clean)
                if self.lifx and (simple or json_acts):
                     # ... execute lights ...
                     pass # (Simplified for buffer tail)
            
            # Wait for playback queue to empty
            await self._speak_and_wait("")
            
            # Log turn (Approximate)
            turn = ConversationTurn(
                turn_id=f"stream-{int(time.time())}",
                timestamp=datetime.now().isoformat(),
                user_audio_kb=audio_kb,
                user_audio_seconds=audio_seconds,
                transcription=transcription if 'transcription' in locals() else "unknown",
                response="[Streamed]",
                inference_time=time.time() - t0,
                tokens_used=0 # Streaming doesn't return usage easily
            )
            self.conversation.add_turn(turn)

        except Exception as e:
            self.dashboard.update_history("System", f"Stream Error: {e}", "red")
            self.live.update(self.dashboard.generate_view())

        # Wait for speech
        self.mic.wait_for_speech(threshold=self.audio_config.wake_threshold)
        
        # Check if this is feedback (speech detected too soon after TTS)
        time_since_tts = time.time() - self._last_tts_end_time
        if time_since_tts < self.audio_config.post_speech_cooldown:
            self.dashboard.set_status(f"Cooldown ({time_since_tts:.1f}s)", "yellow")
            self.live.update(self.dashboard.generate_view())
            
            self.stats.feedback_rejected += 1
            await asyncio.sleep(self.audio_config.post_speech_cooldown - time_since_tts)
            return

        self.state = SessionState.LISTENING
        self.dashboard.set_status("Recording...", "red")
        self.live.update(self.dashboard.generate_view())

        audio_data = self.mic.listen_until_silence(
            silence_threshold=self.audio_config.silence_threshold,
            silence_duration=self.audio_config.silence_duration
        )

        audio_kb = len(audio_data) / 1024
        audio_seconds = len(audio_data) / (self.mic.sample_rate * 2)
        self.stats.total_audio_seconds += audio_seconds

        self.dashboard.set_mic(f"{audio_seconds:.1f}s")
        self.live.update(self.dashboard.generate_view())

        # Reject suspiciously long recordings (likely feedback loop)
        if audio_seconds > 30:
            self.dashboard.update_history("System", f"Recording too long ({audio_seconds:.1f}s) - ignored", "yellow")
            self.live.update(self.dashboard.generate_view())
            self.stats.feedback_rejected += 1
            return

        # 2. PROCESS
        self.state = SessionState.PROCESSING
        self.dashboard.set_status("Thinking...", "cyan")
        self.live.update(self.dashboard.generate_view())
        
        wav_data = create_wav_buffer(audio_data, self.mic.sample_rate)

        # Capture history size BEFORE inference (for rollback)
        history_before = self.conversation.history_size

        response_text, inference_time, tokens = await self._inference_with_retry(wav_data)

        if response_text is None:
            self.dashboard.update_history("System", "Inference Failed", "red")
            self.live.update(self.dashboard.generate_view())
            self.stats.errors += 1
            self.conversation.rollback(history_before)
            return

        # Extract transcription
        transcription, clean_response = extract_transcription(response_text)

        self.dashboard.update_history("User", transcription or 'unclear', "dim white")
        self.live.update(self.dashboard.generate_view())

        # ════════════════════════════════════════════════════════════════
        # VALIDATION CHECKS
        # ════════════════════════════════════════════════════════════════

        # Check 1: Prompt leak detection
        # Check 1: Prompt leak detection
        if is_prompt_leak(transcription):
            self.dashboard.update_history("System", "Prompt leak detected", "red")
            self.live.update(self.dashboard.generate_view())
            self.conversation.rollback(history_before)
            await self._speak_fallback("I ain't catch that. Say it again for me.")
            return

        # Check 2: Hallucination (unclear but long response)
        if transcription.lower() in ["unclear", ""] and len(clean_response) > 100:
            self.dashboard.update_history("System", "Hallucination detected", "red")
            self.live.update(self.dashboard.generate_view())
            self.stats.hallucinations_caught += 1
            self.conversation.rollback(history_before)
            await self._speak_fallback("I ain't catch that. Say it again for me.")
            return

        # Check 3: Genuinely unclear (short response is fine)
        if transcription.lower() in ["unclear", ""]:
            self.dashboard.update_history("System", "Audio unclear", "yellow")
            self.live.update(self.dashboard.generate_view())
            self.conversation.rollback(history_before)
            await self._speak_fallback("I ain't catch that. Say it again for me.")
            return

        # ════════════════════════════════════════════════════════════════
        # VALID TURN - proceed
        # ════════════════════════════════════════════════════════════════

        self.stats.total_inference_time += inference_time
        self.stats.total_tokens += tokens
        self.stats.successful_turns += 1

        # Extract light commands if present
        simple_action, json_actions, clean_response = extract_light_command(clean_response)
        
        self.dashboard.update_history("Kaedra", clean_response, "magenta")
        cost = (tokens / 1_000_000) * 0.10
        self.dashboard.update_stats(inference_time, tokens, self.dashboard.total_cost + cost)
        self.live.update(self.dashboard.generate_view())
        
        # Execute light commands if LIFX is available
        if self.lifx and (json_actions or simple_action):
            # Execute lights in background to avoid blocking TTS
            async def run_lights_bg():
                try:
                    if json_actions:
                        await asyncio.to_thread(self.lifx.set_states, json_actions)
                        devices = [a.get("selector", "?").replace("label:", "") for a in json_actions]
                        self.dashboard.set_lights(devices)
                    elif simple_action:
                        await asyncio.to_thread(execute_light_command, self.lifx, simple_action)
                        self.dashboard.set_lights([simple_action])
                    
                    self.live.update(self.dashboard.generate_view())
                except Exception as e:
                    self.dashboard.update_history("System", f"Light Error: {e}", "red")

            asyncio.create_task(run_lights_bg())

        # Check intents
        if check_exit_intent(transcription):
            print("[*] 👋 Exit intent detected")
            self._should_stop = True
            await self._speak_and_wait("Aight Dave, I'm out. Kaedra out.")
            return

        if check_reset_intent(transcription):
            print("[*] 🔄 Memory reset triggered")
            self.conversation.reset()
            await self._speak_and_wait("Bet. Memory wiped. We startin' fresh.")
            return

        # Log turn
        turn = ConversationTurn(
            turn_id=turn_id,
            timestamp=datetime.now().isoformat(),
            user_audio_kb=audio_kb,
            user_audio_seconds=audio_seconds,
            transcription=transcription,
            response=clean_response,
            inference_time=inference_time,
            tokens_used=tokens
        )
        self.conversation.add_turn(turn)

        # 3. SPEAK
        await self._speak_and_wait(clean_response)

    async def _inference_with_retry(self, wav_data: bytes) -> tuple[Optional[str], float, int]:
        """Send to Gemini with retry logic."""
        audio_part = Part.from_data(wav_data, mime_type="audio/wav")

        for attempt in range(self.session_config.retry_attempts):
            try:
                start = time.time()
                # Inject current time so Kaedra knows the real time
                current_time = datetime.now().strftime("%I:%M %p EST on %B %d, %Y")
                response = await self.conversation.chat.send_message_async([
                    audio_part,
                    f"[USER_AUDIO] Current time: {current_time}"
                ])
                inference_time = time.time() - start

                text_tokens = len(response.text) // 4
                audio_tokens = 1500
                tokens = text_tokens + audio_tokens

                return response.text.strip(), inference_time, tokens

            except Exception as e:
                print(f"[!] Attempt {attempt + 1} failed: {e}")
                if attempt < self.session_config.retry_attempts - 1:
                    await asyncio.sleep(self.session_config.retry_delay * (attempt + 1))

        return None, 0, 0

    async def _speak_fallback(self, text: str):
        """Speak a fallback message (doesn't update last_tts_end_time aggressively)."""
        self.dashboard.set_status("Speaking (Fallback)...", "green")
        self.live.update(self.dashboard.generate_view())
        await asyncio.to_thread(self.tts.speak, text)
        self._last_tts_end_time = time.time()
        await asyncio.sleep(1.5)

    async def _speak_and_wait(self, text: str):
        """Speak response and wait for playback to finish."""
        self.state = SessionState.SPEAKING
        self.dashboard.set_status("Speaking...", "green")
        self.live.update(self.dashboard.generate_view())
        
        # Speak (Non-blocking queue add)
        if text:
            await asyncio.to_thread(self.tts.speak, text)
        
        self.state = SessionState.COOLDOWN
        self.dashboard.set_status("Speaking (Queue)...", "yellow")
        self.live.update(self.dashboard.generate_view())

        # Poll for completion
        while self.tts.is_speaking():
            await asyncio.sleep(0.1)
        
        self.state = SessionState.IDLE
        self.dashboard.set_status("Idle", "dim white")
        self.live.update(self.dashboard.generate_view())

    async def _shutdown(self):
        """Graceful shutdown."""
        # Use console.print to print above/after Live display
        self.dashboard.console.print("\n[*] 🛑 Shutting down...")

        filepath = self.conversation.save_transcript()
        if filepath:
            self.dashboard.console.print(f"[*] 💾 Transcript saved: {filepath}")

        self.dashboard.console.print(self.stats.summary())

    def _banner(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════════╗
║              KAEDRA VOICE ENGINE v2.1                        ║
╠══════════════════════════════════════════════════════════════╣
║  Model:      {MODEL_NAME:<45}║
║  TTS:        {self.session_config.tts_variant.upper():<45}║
║  Mic:        Index {self.mic.device_index} (Chat Mix){' '*27}║
║  History:    {self.session_config.max_history_turns} turns max{' '*33}║
║  Cooldown:   {self.audio_config.post_speech_cooldown}s post-TTS{' '*32}║
╠══════════════════════════════════════════════════════════════╣
║  Commands:   "forget everything" - reset memory              ║
║              "goodbye kaedra" - exit                         ║
║              Ctrl+C - force quit                             ║
╚══════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(description="Kaedra Voice Engine v2.1")
    parser.add_argument("--tts", choices=["pro", "flash", "flash-lite"], default="flash-lite")
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--wake-threshold", type=int, default=500)
    parser.add_argument("--silence-threshold", type=int, default=400)
    parser.add_argument("--silence-duration", type=float, default=0.6)
    parser.add_argument("--cooldown", type=float, default=3.0, help="Post-TTS cooldown seconds")
    parser.add_argument("--mic", type=str, default="Chat Mix", help="Mic device name filter (e.g. 'Realtek', 'Chat Mix', 'Wave')")
    parser.add_argument("--no-save", dest="save_transcripts", action="store_false", default=True)
    args = parser.parse_args()

    audio_config = AudioConfig(
        wake_threshold=args.wake_threshold,
        silence_threshold=args.silence_threshold,
        silence_duration=args.silence_duration,
        post_speech_cooldown=args.cooldown
    )

    session_config = SessionConfig(
        max_history_turns=args.max_turns,
        tts_variant=args.tts,
        save_transcripts=args.save_transcripts
    )

    print(f"[*] Initializing (Project: {PROJECT_ID})...")

    try:
        mic = MicrophoneService(device_name_filter=args.mic)
        tts = TTSService(model_variant=args.tts)
        
        # Initialize LIFX if token is available
        lifx = None
        if LIFX_AVAILABLE:
            try:
                lifx = LIFXService()
                lights = lifx.list_lights()
                print(f"[💡] LIFX connected: {len(lights)} light(s)")
            except Exception as e:
                print(f"[!] LIFX unavailable: {e}")
                lifx = None
        else:
            print("[*] LIFX not configured (set LIFX_TOKEN env var)")

        vertexai.init(project=PROJECT_ID, location="global")
        model = GenerativeModel(MODEL_NAME, system_instruction=VOICE_SYSTEM_PROMPT)

        conversation = ConversationManager(model, session_config)

        engine = KaedraVoiceEngine(
            mic=mic,
            tts=tts,
            conversation=conversation,
            audio_config=audio_config,
            session_config=session_config,
            lifx=lifx
        )

        await engine.run()

    except Exception as e:
        print(f"[!] Fatal: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
