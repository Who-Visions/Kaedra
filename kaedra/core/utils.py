import io
import wave
import re
import json
from typing import Optional

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

def extract_all_metadata(response: str) -> dict:
    """
    Unified extractor for all technical tags.
    Returns {
        'transcription': str,
        'light_simple': str,
        'light_json': list,
        'exec_cmd': str,
        'clean_text': str
    }
    """
    result = {
        'transcription': "",
        'light_simple': None,
        'light_json': None,
        'exec_cmd': None,
        'clean_text': response
    }
    
    # 1. Extract [Heard: "..."]
    heard_match = re.search(r'\[Heard:\s*(.*?)\]', result['clean_text'], re.IGNORECASE | re.DOTALL)
    if heard_match:
        raw = heard_match.group(1).strip().strip('"').strip("'")
        result['transcription'] = raw
        result['clean_text'] = re.sub(r'\[Heard:.*?\]', '', result['clean_text'], flags=re.DOTALL)

    # 2. Extract [EXEC: ...]
    exec_match = re.search(r'\[EXEC:\s*(.*?)\]', result['clean_text'], re.IGNORECASE | re.DOTALL)
    if exec_match:
        result['exec_cmd'] = exec_match.group(1).strip()
        result['clean_text'] = re.sub(r'\[EXEC:.*?\]', '', result['clean_text'], flags=re.DOTALL)

    # 3. Extract [LIGHT: ...] or JSON actions
    simple_action, json_actions, cleaned = extract_light_command(result['clean_text'])
    result['light_simple'] = simple_action
    result['light_json'] = json_actions
    result['clean_text'] = cleaned

    # Final cleanup: Remove any remaining [...] or markdown code blocks
    result['clean_text'] = re.sub(r'```.*?```', '', result['clean_text'], flags=re.DOTALL)
    result['clean_text'] = re.sub(r'\[.*?\]', '', result['clean_text'], flags=re.DOTALL)
    result['clean_text'] = result['clean_text'].strip()
    
    return result

def extract_light_command(response: str) -> tuple[Optional[str], Optional[list], str]:
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
            
            # Note: validate_light_action needs to be defined or imported
            # For this utility we'll leave it as a placeholder or import it
            from kaedra.core.google_tools import validate_light_action # Assuming it exists there
            
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
    Execute a light command.
    Returns True if command was executed, False otherwise.
    """
    try:
        parts = action.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in ["on", "turn on"]:
            lifx.turn_on()
        elif cmd in ["off", "turn off"]:
            lifx.turn_off()
        elif cmd == "toggle":
            lifx.toggle()
        elif cmd == "color" and args:
            color = " ".join(args)
            lifx.set_color("all", color)
        elif cmd == "dim" and args:
            try:
                percent = int(args[0].replace("%", ""))
                lifx.dim("all", percent)
            except ValueError: pass
        elif cmd == "brightness" and args:
            try:
                level = float(args[0])
                lifx.set_brightness("all", level)
            except ValueError: pass
        elif cmd == "brighter":
            lifx.brighter()
        elif cmd == "dimmer":
            lifx.dimmer()
        elif cmd == "warmer":
            lifx.warmer()
        elif cmd == "cooler":
            lifx.cooler()
        elif cmd == "mode" and args:
            mode = args[0]
            if mode == "movie": lifx.movie_mode()
            elif mode == "focus": lifx.focus_mode()
            elif mode == "relax": lifx.relax_mode()
            elif mode == "party": lifx.party_mode()
            elif mode == "photo": lifx.photo_mode()
            elif mode == "chill": lifx.chill_mode()
            elif mode == "work": lifx.work_mode()
            elif mode == "christmas": lifx.christmas_mode()
            elif mode in ["ember", "warm"]: lifx.warm_ember()
        elif cmd == "bedroom":
            sub_cmd = args[0] if args else "on"
            if sub_cmd == "off": lifx.turn_off(lifx.BEDROOM)
            else: lifx.turn_on(lifx.BEDROOM)
        elif cmd in ["living", "livingroom"] or (cmd == "living" and args and args[0] == "room"):
            sub_args = args[1:] if args and args[0] == "room" else args
            sub_cmd = sub_args[0] if sub_args else "on"
            if sub_cmd == "off": lifx.turn_off(lifx.LIVING_ROOM)
            else: lifx.turn_on(lifx.LIVING_ROOM)
        elif cmd == "breathe" and args:
            lifx.breathe("all", " ".join(args))
        elif cmd == "pulse" and args:
            lifx.pulse("all", " ".join(args))
        elif cmd == "sunrise":
            lifx.sunrise("all", int(args[0]) if args else 300)
        elif cmd == "sunset":
            lifx.sunset("all", int(args[0]) if args else 300)
        elif cmd == "effects" and args and args[0] == "off":
            lifx.effects_off()
        else:
            return False
        return True
    except Exception:
        return False

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
