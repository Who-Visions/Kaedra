"""
KAEDRA v1.0 - Utility Functions
Common helpers for audio processing, tag extraction, and CLI command execution.
"""

import io
import json
import re
import wave
from typing import Optional, Tuple, Dict, Any, List

def create_wav_buffer(audio_data: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM audio in WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)  # pylint: disable=no-member
        wf.setsampwidth(2)  # pylint: disable=no-member
        wf.setframerate(sample_rate)  # pylint: disable=no-member
        wf.writeframes(audio_data)  # pylint: disable=no-member
    return buf.getvalue()

def estimate_speech_duration(text: str, wps: float = 2.8) -> float:
    """Estimate TTS playback duration."""
    words = len(text.split())
    return max(1.0, min((words / wps) + 0.8, 15.0))

def extract_all_metadata(response: str) -> Dict[str, Any]:
    """
    Unified extractor for all technical tags within an agent response.
    
    Returns:
        Dict containing transcription, light commands, notion logs, 
        and the cleaned text for TTS.
    """
    result = {
        'transcription': "",
        'light_simple': None,
        'light_json': None,
        'notion_log': None,
        'notion_action': None,
        'exec_cmd': None,
        'clean_text': response
    }

    _extract_heard_tag(result)
    _extract_exec_tag(result)
    _extract_json_blocks(result)
    
    # Final light extraction and cleanup
    simple, json_acts, cleaned = extract_light_command(result['clean_text'])
    result.update({
        'light_simple': simple,
        'light_json': json_acts,
        'clean_text': cleaned
    })

    # Cleanup remaining tags/code
    result['clean_text'] = re.sub(r'```.*?```', '', result['clean_text'], flags=re.DOTALL)
    result['clean_text'] = re.sub(r'\[.*?\]', '', result['clean_text'], flags=re.DOTALL)
    result['clean_text'] = result['clean_text'].strip()

    return result

def _extract_heard_tag(result: Dict[str, Any]):
    """Extract [Heard: "..."] tags."""
    pattern = r'\[Heard:\s*(.*?)\]'
    match = re.search(pattern, result['clean_text'], re.IGNORECASE | re.DOTALL)
    if match:
        result['transcription'] = match.group(1).strip().strip('"').strip("'")
        cleaned = re.sub(pattern, '', result['clean_text'], flags=re.IGNORECASE | re.DOTALL)
        result['clean_text'] = cleaned

def _extract_exec_tag(result: Dict[str, Any]):
    """Extract [EXEC: ...] tags."""
    pattern = r'\[EXEC:\s*(.*?)\]'
    match = re.search(pattern, result['clean_text'], re.IGNORECASE | re.DOTALL)
    if match:
        result['exec_cmd'] = match.group(1).strip()
        cleaned = re.sub(pattern, '', result['clean_text'], flags=re.IGNORECASE | re.DOTALL)
        result['clean_text'] = cleaned

def _extract_json_blocks(result: Dict[str, Any]):
    """Extract and parse JSON content from markdown or bare blocks."""
    # Pattern for JSON blocks containing specific keys
    keys = r"actions|notion_log|notion_action"
    json_pat = rf'```json\s*({{.*?}})\s*```|({{+(?:"(?:{keys})"):\s*.*?}}+)'
    
    match = re.search(json_pat, result['clean_text'], re.DOTALL)
    if match:
        try:
            content = match.group(1) or match.group(2)
            data = json.loads(content)
            if "notion_log" in data:
                result['notion_log'] = data["notion_log"]
            elif "notion_action" in data:
                result['notion_action'] = data["notion_action"]
            
            # Remove from clean text
            result['clean_text'] = re.sub(json_pat, '', result['clean_text'], flags=re.DOTALL)
        except (json.JSONDecodeError, TypeError, KeyError, AttributeError):
            pass

def extract_light_command(response: str) -> Tuple[Optional[str], Optional[List], str]:
    """
    Extract light commands from response.
    Returns (simple_action, json_actions, cleaned_response).
    """
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

            # Use the locally defined validate_light_action
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
        except Exception:
            pass

    # Try simple [LIGHT: ...] tags
    simple_match = re.search(r'\[LIGHT:\s*(.*?)\]', response, re.IGNORECASE)
    if simple_match:
        action = simple_match.group(1).strip()
        cleaned = re.sub(r'\[LIGHT:.*?\]', '', cleaned, flags=re.DOTALL).strip()
        return action, None, cleaned

    return None, None, cleaned


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
    Execute a light command using a dispatch table to reduce branches.
    Returns True if command was successfully routed, False otherwise.
    """
    parts = action.split()
    if not parts:
        return False
    cmd = parts[0].lower()
    args = parts[1:]

    # Dispatch Table for simple commands
    dispatch = {
        "on": lifx.turn_on,
        "turn on": lifx.turn_on,
        "off": lifx.turn_off,
        "turn off": lifx.turn_off,
        "toggle": lifx.toggle,
        "brighter": lifx.brighter,
        "dimmer": lifx.dimmer,
        "warmer": lifx.warmer,
        "cooler": lifx.cooler,
        "effects_off": lifx.effects_off,
    }

    if cmd in dispatch:
        try:
            dispatch[cmd]()
            return True
        except (AttributeError, RuntimeError, ValueError):
            return False

    # Argument-based commands
    return _handle_arg_commands(lifx, cmd, args)

def _handle_arg_commands(lifx, cmd: str, args: List[str]) -> bool:
    """Handle light commands that require arguments."""
    try:
        if cmd == "color" and args:
            lifx.set_color("all", " ".join(args))
        elif cmd == "dim" and args:
            lifx.dim("all", int(args[0].replace("%", "")))
        elif cmd == "brightness" and args:
            lifx.set_brightness("all", float(args[0]))
        elif cmd == "mode" and args:
            _execute_mode(lifx, args[0])
        elif cmd == "bedroom":
            _execute_room(lifx, lifx.BEDROOM, args)
        elif cmd in ["living", "livingroom"]:
            _execute_room(lifx, lifx.LIVING_ROOM, args)
        elif cmd in ["breathe", "pulse"] and args:
            func = getattr(lifx, cmd)
            func("all", " ".join(args))
        elif cmd in ["sunrise", "sunset"]:
            func = getattr(lifx, cmd)
            func("all", int(args[0]) if args else 300)
        else:
            return False
        return True
    except (ValueError, AttributeError, RuntimeError, IndexError):
        return False

def _execute_mode(lifx, mode: str):
    """Execute a specific named lighting mode."""
    modes = {
        "movie": lifx.movie_mode, "focus": lifx.focus_mode,
        "relax": lifx.relax_mode, "party": lifx.party_mode,
        "photo": lifx.photo_mode, "chill": lifx.chill_mode,
        "work": lifx.work_mode, "christmas": lifx.christmas_mode,
        "ember": lifx.warm_ember, "warm": lifx.warm_ember
    }
    if mode in modes:
        modes[mode]()

def _execute_room(lifx, room_id, args: List[str]):
    """Execute power command for a specific room."""
    sub = args[0] if args else "on"
    if sub == "off":
        lifx.turn_off(room_id)
    else:
        lifx.turn_on(room_id)

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
