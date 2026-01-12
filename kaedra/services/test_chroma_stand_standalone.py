"""
Razer Chroma SDK REST API Skill for Dav1d
Controls RGB lighting on Razer devices via the Chroma SDK.

API Reference: https://assets.razerzone.com/dev_portal/REST/html/index.html

Requirements:
- Razer Synapse 3 with Chroma Connect enabled
- Chroma SDK running locally (default port 54235)
"""

import requests
import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# CONFIGURATION
# ============================================================================

CHROMA_SDK_URL = "http://localhost:54235/razer/chromasdk"
CHROMA_SDK_HTTPS = "https://chromasdk.io:54236/razer/chromasdk"
DEFAULT_TIMEOUT = 15  # SDK connection timeout in seconds
HEARTBEAT_INTERVAL = 1  # Recommended: 1 second


# ============================================================================
# EFFECT TYPES
# ============================================================================

class Effect(Enum):
    NONE = "CHROMA_NONE"
    STATIC = "CHROMA_STATIC"
    CUSTOM = "CHROMA_CUSTOM"
    CUSTOM2 = "CHROMA_CUSTOM2"
    CUSTOM_KEY = "CHROMA_CUSTOM_KEY"
    BREATHING = "CHROMA_BREATHING"
    WAVE = "CHROMA_WAVE"
    SPECTRUM_CYCLING = "CHROMA_SPECTRUMCYCLING"
    REACTIVE = "CHROMA_REACTIVE"
    BLINKING = "CHROMA_BLINKING"


# Wave directions
class WaveDirection(Enum):
    LEFT_TO_RIGHT = 1
    RIGHT_TO_LEFT = 2


class Device(Enum):
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    HEADSET = "headset"
    MOUSEPAD = "mousepad"
    KEYPAD = "keypad"
    CHROMALINK = "chromalink"


# Grid/LED sizes for each device
class GridSize:
    """Device grid and LED sizes for custom effects."""
    CHROMALINK_LEDS = 5
    HEADSET_LEDS = 5
    KEYBOARD_ROWS = 6
    KEYBOARD_COLS = 22
    KEYBOARD_V2_ROWS = 8
    KEYBOARD_V2_COLS = 24
    KEYPAD_ROWS = 4
    KEYPAD_COLS = 5
    MOUSE_ROWS = 9
    MOUSE_COLS = 7
    MOUSEPAD_LEDS = 15
    MOUSEPAD_V2_LEDS = 20


# ============================================================================
# COLOR UTILITIES
# ============================================================================

def rgb_to_bgr(r: int, g: int, b: int) -> int:
    """Convert RGB to BGR integer format for Chroma SDK."""
    return (b << 16) | (g << 8) | r


def hex_to_bgr(hex_color: str) -> int:
    """Convert hex color (#RRGGBB) to BGR integer."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return rgb_to_bgr(r, g, b)


# Common colors in BGR format
class Colors:
    RED = rgb_to_bgr(255, 0, 0)      # 255
    GREEN = rgb_to_bgr(0, 255, 0)    # 65280
    BLUE = rgb_to_bgr(0, 0, 255)     # 16711680
    YELLOW = rgb_to_bgr(255, 255, 0) # 65535
    CYAN = rgb_to_bgr(0, 255, 255)   # 16776960
    MAGENTA = rgb_to_bgr(255, 0, 255)# 16711935
    WHITE = rgb_to_bgr(255, 255, 255)# 16777215
    BLACK = 0
    ORANGE = rgb_to_bgr(255, 165, 0) # 42495
    PURPLE = rgb_to_bgr(128, 0, 128) # 8388736


# ============================================================================
# CHROMA SESSION MANAGER
# ============================================================================

@dataclass
class ChromaSession:
    """Active Chroma SDK session."""
    session_id: int
    uri: str
    active: bool = True
    _heartbeat_thread: Optional[threading.Thread] = None


class RazerChroma:
    """
    Razer Chroma SDK client for controlling RGB lighting.

    Usage:
        chroma = RazerChroma()
        chroma.connect()
        chroma.set_static_color(Device.KEYBOARD, Colors.RED)
        chroma.disconnect()
    """

    def __init__(self, app_name: str = "Kaedra Story Engine"):
        self.app_name = app_name
        self.session: Optional[ChromaSession] = None
        self._heartbeat_active = False
        self._drive_active = False

        # Target states for each endpoint to be pushed by the drive loop
        self._target_state = {
            "keyboard": {"effect": "CHROMA_NONE"},
            "mouse": {"effect": "CHROMA_NONE"},
            "mousepad": {"effect": "CHROMA_NONE"},
            "headset": {"effect": "CHROMA_NONE"},
            "keypad": {"effect": "CHROMA_NONE"},
            "chromalink": {"effect": "CHROMA_NONE"}
        }
        self._state_lock = threading.Lock()

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def connect(self) -> Dict:
        """
        Initialize connection to Chroma SDK.
        Must be called before any effects.

        Returns:
            Dict with session info or error
        """
        payload = {
            "title": self.app_name,
            "description": "AI-powered RGB control via Dav1d",
            "author": {
                "name": "Dav1d Brain",
                "contact": "https://github.com/Who-Visions/Dav1d"
            },
            "device_supported": [d.value for d in Device],
            "category": "application"
        }

        try:
            # Try localhost first
            response = requests.post(CHROMA_SDK_URL, json=payload, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if "sessionid" in data and "uri" in data:
                    self.session = ChromaSession(
                        session_id=data["sessionid"],
                        uri=data["uri"]
                    )
                    # Wait for session port to be ready (SDK quirk)
                    time.sleep(2)
                    self._start_heartbeat()
                    self._start_drive_loop()
                    return {
                        "success": True,
                        "session_id": self.session.session_id,
                        "uri": self.session.uri
                    }

            return {"success": False, "error": f"SDK response: {response.text}"}

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Chroma SDK not running. Ensure Razer Synapse 3 is installed with Chroma Connect enabled."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def disconnect(self) -> Dict:
        """
        Uninitialize and close the Chroma SDK session.
        Turns off all devices before disconnecting to prevent stuck lights.
        Should be called when done to free resources.
        """
        if not self.session:
            return {"success": False, "error": "Not connected"}

        self._stop_heartbeat()
        self._stop_drive_loop()

        try:
            # Turn off all devices before disconnecting
            payload = {"effect": "CHROMA_NONE"}
            for ep in ["chromalink", "mousepad", "headset", "mouse"]:
                try:
                    requests.put(f"{self.session.uri}/{ep}", json=payload, timeout=2)
                except:
                    pass

            response = requests.delete(self.session.uri, timeout=5)
            self.session = None
            return {"success": True, "result": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _start_heartbeat(self):
        """Start background heartbeat to keep connection alive."""
        self._heartbeat_active = True

        def heartbeat_loop():
            while self._heartbeat_active and self.session:
                try:
                    requests.put(f"{self.session.uri}/heartbeat", timeout=2)
                except:
                    pass
                time.sleep(HEARTBEAT_INTERVAL)

        thread = threading.Thread(target=heartbeat_loop, daemon=True)
        thread.start()
        self.session._heartbeat_thread = thread

    def _stop_heartbeat(self):
        """Stop the heartbeat thread."""
        self._heartbeat_active = False

    def _start_drive_loop(self):
        """Start background drive loop to continuously push states."""
        self._drive_active = True

        def drive_loop():
            while self._drive_active and self.session:
                with self._state_lock:
                    current_targets = dict(self._target_state)

                for endpoint, payload in current_targets.items():
                    if not self._drive_active: break
                    try:
                        requests.put(f"{self.session.uri}/{endpoint}", json=payload, timeout=0.2)
                    except:
                        pass

                time.sleep(0.1) # 10Hz

        thread = threading.Thread(target=drive_loop, daemon=True)
        thread.start()

    def _stop_drive_loop(self):
        """Stop the drive loop."""
        self._drive_active = False

    def get_sdk_version(self) -> Dict:
        """Get the Chroma SDK version installed on the system."""
        try:
            response = requests.get(CHROMA_SDK_URL, timeout=5)
            return {"success": True, "version": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # DEVICE EFFECTS
    # ========================================================================

    def _send_effect(self, device: Device, payload: Dict) -> Dict:
        """Update target state for a specific device."""
        if not self.session:
            return {"success": False, "error": "Not connected. Call connect() first."}

        with self._state_lock:
            self._target_state[device.value] = payload

        return {"success": True, "message": f"Target state updated for {device.value}"}

    def set_static_color(self, device: Device, color: int) -> Dict:
        """
        Set a static color on a device via target state.
        """
        if device == Device.CHROMALINK:
            # Stand requires CUSTOM mapped to 5 LEDs for reliability
            payload = {
                "effect": "CHROMA_CUSTOM",
                "param": [color] * 5
            }
        else:
            payload = {
                "effect": Effect.STATIC.value,
                "param": {"color": color}
            }
        return self._send_effect(device, payload)

    def turn_off(self, device: Device) -> Dict:
        """Turn off lighting on a device."""
        payload = {"effect": Effect.NONE.value}
        return self._send_effect(device, payload)

    def set_all_static(self, color: int) -> Dict:
        """Set static color on ALL connected Chroma devices.

        Targets chromalink, mousepad, and headset endpoints for full coverage
        including Base Station and other accessories.
        """
        payload = {
            "effect": Effect.STATIC.value,
            "param": {"color": color}
        }
        results = {}
        for device in [Device.CHROMALINK, Device.MOUSEPAD, Device.HEADSET, Device.MOUSE]:
            results[device.value] = self._send_effect(device, payload)
        return results

    def turn_off_all(self) -> Dict:
        """Turn off ALL connected Chroma devices.

        Targets chromalink, mousepad, and headset endpoints for full coverage.
        """
        payload = {"effect": Effect.NONE.value}
        results = {}
        for device in [Device.CHROMALINK, Device.MOUSEPAD, Device.HEADSET, Device.MOUSE]:
            results[device.value] = self._send_effect(device, payload)
        return results

    def pulse(self, r: int = 255, g: int = 0, b: int = 0, cycles: int = 3, speed: float = 0.05) -> None:
        """
        Software-based pulse effect that cycles brightness using STATIC.
        Works reliably on ALL devices (hardware breathing effects don't work via REST API).

        Args:
            r, g, b: RGB color values (0-255)
            cycles: Number of pulse cycles
            speed: Delay between brightness steps (lower = faster)
        """
        if not self.session:
            return

        endpoints = ["chromalink", "mousepad", "headset", "mouse", "keyboard"]

        for _ in range(cycles):
            # Fade up
            for brightness in range(0, 256, 25):
                factor = brightness / 255
                color = rgb_to_bgr(int(r * factor), int(g * factor), int(b * factor))
                effect = {"effect": "CHROMA_STATIC", "param": {"color": color}}
                for ep in endpoints:
                    try:
                        requests.put(f"{self.session.uri}/{ep}", json=effect, timeout=1)
                    except:
                        pass
                time.sleep(speed)

            # Fade down
            for brightness in range(255, -1, -25):
                factor = brightness / 255
                color = rgb_to_bgr(int(r * factor), int(g * factor), int(b * factor))
                effect = {"effect": "CHROMA_STATIC", "param": {"color": color}}
                for ep in endpoints:
                    try:
                        requests.put(f"{self.session.uri}/{ep}", json=effect, timeout=1)
                    except:
                        pass
                time.sleep(speed)

            # Keep session alive
            try:
                requests.put(f"{self.session.uri}/heartbeat", timeout=2)
            except:
                pass

    def spectrum_cycle(self, duration: float = 10.0, speed: float = 0.1) -> None:
        """
        Software-based rainbow spectrum effect that cycles through all hues.
        Works reliably on ALL devices.

        Args:
            duration: How long to run the effect (seconds)
            speed: Delay between color steps (lower = faster)
        """
        if not self.session:
            return

        import colorsys
        endpoints = ["chromalink", "mousepad", "headset", "mouse", "keyboard"]

        steps = int(duration / speed)
        for i in range(steps):
            hue = (i * 3.6) % 360
            r, g, b = colorsys.hsv_to_rgb(hue / 360, 1.0, 1.0)
            color = rgb_to_bgr(int(r * 255), int(g * 255), int(b * 255))
            effect = {"effect": "CHROMA_STATIC", "param": {"color": color}}

            for ep in endpoints:
                try:
                    requests.put(f"{self.session.uri}/{ep}", json=effect, timeout=1)
                except:
                    pass

            time.sleep(speed)

            if i % 30 == 0:
                try:
                    requests.put(f"{self.session.uri}/heartbeat", timeout=2)
                except:
                    pass

    def wave(self, r: int = 255, g: int = 0, b: int = 0, duration: float = 10.0, speed: float = 0.2) -> None:
        """
        Software-based wave effect that simulates brightness movement.
        Works reliably on ALL devices.

        Args:
            r, g, b: Base RGB color (0-255)
            duration: How long to run the effect (seconds)
            speed: Delay between wave steps (lower = faster)
        """
        if not self.session:
            return

        endpoints = ["chromalink", "mousepad", "headset", "mouse", "keyboard"]
        cycles = int(duration / (speed * 10))

        for _ in range(cycles):
            for phase in range(10):
                # Create wave pattern with one endpoint brighter
                for i, ep in enumerate(endpoints):
                    # Brightness peaks at current phase position
                    factor = 1.0 if (phase % 4) == i else 0.2
                    color = rgb_to_bgr(int(r * factor), int(g * factor), int(b * factor))
                    effect = {"effect": "CHROMA_STATIC", "param": {"color": color}}
                    try:
                        requests.put(f"{self.session.uri}/{ep}", json=effect, timeout=1)
                    except:
                        pass
                time.sleep(speed)

            try:
                requests.put(f"{self.session.uri}/heartbeat", timeout=2)
            except:
                pass

    def audio_visualize(self, duration: float = 30.0, device_index: int = 12) -> None:
        """
        Audio-reactive lighting that responds to system audio levels.
        Colors: quiet=blue, medium=green, loud=red

        Requires pycaw and comtypes: pip install pycaw comtypes

        Args:
            duration: How long to run the visualizer (seconds)
            device_index: Windows audio endpoint index (default 12 for Wave Link)
        """
        if not self.session:
            return

        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            import comtypes.client
            from pycaw.pycaw import IMMDeviceEnumerator, EDataFlow, IAudioMeterInformation
        except ImportError:
            print("Audio visualizer requires pycaw: pip install pycaw comtypes")
            return

        # Get audio meter for specified device
        enumerator = comtypes.client.CreateObject(
            '{BCDE0395-E52F-467C-8E3D-C4579291692E}',
            clsctx=CLSCTX_ALL,
            interface=IMMDeviceEnumerator
        )
        collection = enumerator.EnumAudioEndpoints(EDataFlow.eRender.value, 1)
        device = collection.Item(device_index)
        interface = device.Activate(IAudioMeterInformation._iid_, CLSCTX_ALL, None)
        meter = cast(interface, POINTER(IAudioMeterInformation))

        endpoints = ["chromalink", "mousepad", "headset", "mouse", "keyboard"]
        iterations = int(duration / 0.1)

        for i in range(iterations):
            peak = meter.GetPeakValue()
            intensity = min(255, int(peak * 300))

            # Color mapping: quiet=blue, medium=green, loud=red
            if peak < 0.3:
                r, g, b = 0, int(intensity * 0.5), intensity
            elif peak < 0.6:
                r, g, b = int(intensity * 0.5), intensity, 0
            else:
                r, g, b = intensity, int(intensity * 0.3), 0

            color = rgb_to_bgr(max(15, r), max(15, g), max(15, b))
            effect = {"effect": "CHROMA_STATIC", "param": {"color": color}}

            for ep in endpoints:
                try:
                    requests.put(f"{self.session.uri}/{ep}", json=effect, timeout=0.3)
                except:
                    pass

            time.sleep(0.1)

            if i % 25 == 0:
                try:
                    requests.put(f"{self.session.uri}/heartbeat", timeout=2)
                except:
                    pass

    def fire(self, duration: float = 10.0) -> None:
        """
        Software-based fire effect with flickering flames.
        Uses CHROMA_CUSTOM for per-key keyboard flames and STATIC for other devices.
        Verified working on all 7 devices including BlackWidow Elite.

        Args:
            duration: How long to run the effect (seconds)
        """
        if not self.session:
            return

        import random

        # Fire colors: orange, red, yellow variations
        fire_colors = [
            rgb_to_bgr(255, 50, 0),    # Orange-red
            rgb_to_bgr(255, 100, 0),   # Orange
            rgb_to_bgr(255, 150, 20),  # Yellow-orange
            rgb_to_bgr(200, 30, 0),    # Dark red
            rgb_to_bgr(255, 80, 0),    # Bright orange
            rgb_to_bgr(180, 40, 0),    # Ember
            rgb_to_bgr(255, 200, 50),  # Yellow flame tip
        ]

        endpoints = ["chromalink", "mousepad", "headset", "mouse"]
        frames = int(duration / 0.1)

        for frame in range(frames):
            # Create random fire pattern for 6x22 keyboard grid
            grid = []
            for row in range(6):
                row_colors = []
                for col in range(22):
                    # Bottom rows brighter, top rows dimmer
                    intensity = (5 - row) / 5
                    if random.random() < intensity:
                        color = random.choice(fire_colors)
                    else:
                        color = rgb_to_bgr(int(100 * random.random()), int(20 * random.random()), 0)
                    row_colors.append(color)
                grid.append(row_colors)

            # Send to keyboard with CUSTOM
            try:
                requests.put(f"{self.session.uri}/keyboard",
                           json={"effect": "CHROMA_CUSTOM", "param": grid}, timeout=1)
            except:
                pass

            # Send fire color to other devices
            fire_color = random.choice(fire_colors)
            for ep in endpoints:
                try:
                    requests.put(f"{self.session.uri}/{ep}",
                               json={"effect": "CHROMA_STATIC", "param": {"color": fire_color}}, timeout=0.5)
                except:
                    pass

            time.sleep(0.1)

            if frame % 20 == 0:
                try:
                    requests.put(f"{self.session.uri}/heartbeat", timeout=2)
                except:
                    pass

    def starlight(self, duration: float = 10.0) -> None:
        """
        Software-based starlight effect with twinkling stars.
        Random keys fade in and out like twinkling stars on dark background.
        Verified working on all 7 devices.

        Args:
            duration: How long to run the effect (seconds)
        """
        if not self.session:
            return

        import random

        star_colors = [
            rgb_to_bgr(255, 255, 255),   # White
            rgb_to_bgr(200, 220, 255),   # Light blue
            rgb_to_bgr(255, 250, 220),   # Pale yellow
        ]
        bg_color = rgb_to_bgr(10, 5, 20)  # Dark purple

        stars = {}  # (row, col) -> (brightness, delta)
        endpoints = ["chromalink", "mousepad", "headset", "mouse"]
        frames = int(duration / 0.1)

        for frame in range(frames):
            # Spawn new stars randomly
            if random.random() < 0.15:
                row, col = random.randint(0, 5), random.randint(0, 21)
                if (row, col) not in stars:
                    stars[(row, col)] = (0, random.uniform(0.1, 0.3))

            grid = [[bg_color]*22 for _ in range(6)]

            to_remove = []
            for (row, col), (brightness, delta) in stars.items():
                brightness += delta
                if brightness >= 1.0:
                    brightness, delta = 1.0, -abs(delta)
                elif brightness <= 0:
                    to_remove.append((row, col))
                    continue
                stars[(row, col)] = (brightness, delta)

                base = random.choice(star_colors)
                r = int(((base >> 0) & 0xFF) * brightness)
                g = int(((base >> 8) & 0xFF) * brightness)
                b = int(((base >> 16) & 0xFF) * brightness)
                grid[row][col] = rgb_to_bgr(r, g, b)

            for key in to_remove:
                del stars[key]

            try:
                requests.put(f"{self.session.uri}/keyboard",
                           json={"effect": "CHROMA_CUSTOM", "param": grid}, timeout=1)
            except:
                pass

            twinkle = random.choice(star_colors) if random.random() < 0.2 else bg_color
            for ep in endpoints:
                try:
                    requests.put(f"{self.session.uri}/{ep}",
                               json={"effect": "CHROMA_STATIC", "param": {"color": twinkle}}, timeout=0.5)
                except:
                    pass

            time.sleep(0.1)
            if frame % 20 == 0:
                try:
                    requests.put(f"{self.session.uri}/heartbeat", timeout=2)
                except:
                    pass

    # ========================================================================
    # DYNAMIC EFFECTS (Note: Hardware effects don't work via REST API)
    # ========================================================================

    def set_breathing(self, color1: int, color2: int = None) -> Dict:
        """
        Set breathing effect on all devices.

        Args:
            color1: Primary BGR color
            color2: Optional secondary color for dual-color breathing
        """
        if color2 is not None:
            # Two-color breathing
            payload = {
                "effect": Effect.BREATHING.value,
                "param": {
                    "color1": color1,
                    "color2": color2,
                    "type": 2  # Two colors
                }
            }
        else:
            # Single color breathing
            payload = {
                "effect": Effect.BREATHING.value,
                "param": {
                    "color1": color1,
                    "type": 1  # One color
                }
            }
        return self._send_effect(Device.MOUSEPAD, payload)

    def set_wave(self, direction: int = 1) -> Dict:
        """
        Set wave effect on all devices.

        Args:
            direction: 1 = left to right, 2 = right to left
        """
        payload = {
            "effect": Effect.WAVE.value,
            "param": {
                "direction": direction
            }
        }
        return self._send_effect(Device.MOUSEPAD, payload)

    def set_spectrum_cycling(self) -> Dict:
        """Set spectrum cycling (rainbow) effect on all devices."""
        payload = {"effect": Effect.SPECTRUM_CYCLING.value}
        return self._send_effect(Device.MOUSEPAD, payload)

    def set_reactive(self, color: int, duration: int = 2) -> Dict:
        """
        Set reactive effect (lights up on keypress).

        Args:
            color: BGR color
            duration: 1=short, 2=medium, 3=long
        """
        payload = {
            "effect": Effect.REACTIVE.value,
            "param": {
                "color": color,
                "duration": duration
            }
        }
        return self._send_effect(Device.MOUSEPAD, payload)
    # ========================================================================
    # KEYBOARD SPECIFIC EFFECTS
    # ========================================================================

    def set_keyboard_custom(self, color_grid: List[List[int]]) -> Dict:
        """
        Set custom colors on keyboard.
        Grid is 6 rows x 22 columns of BGR color values.

        Args:
            color_grid: 6x22 matrix of BGR colors
        """
        if len(color_grid) != 6:
            return {"success": False, "error": "Keyboard grid must have 6 rows"}

        payload = {
            "effect": Effect.CUSTOM.value,
            "param": color_grid
        }
        return self._send_effect(Device.KEYBOARD, payload)

    def set_keyboard_wave(self, color1: int, color2: int) -> Dict:
        """Create a simple two-color wave pattern on keyboard."""
        grid = []
        for row in range(6):
            row_colors = []
            for col in range(22):
                row_colors.append(color1 if (row + col) % 2 == 0 else color2)
            grid.append(row_colors)
        return self.set_keyboard_custom(grid)

    # ========================================================================
    # MOUSE SPECIFIC EFFECTS
    # ========================================================================

    def set_mouse_custom(self, color_grid: List[List[int]]) -> Dict:
        """
        Set custom colors on mouse.
        Grid is 9 rows x 7 columns of BGR color values.

        Args:
            color_grid: 9x7 matrix of BGR colors
        """
        if len(color_grid) != 9:
            return {"success": False, "error": "Mouse grid must have 9 rows"}

        payload = {
            "effect": Effect.CUSTOM2.value,
            "param": color_grid
        }
        return self._send_effect(Device.MOUSE, payload)

    def _get_scan_code_map(self) -> Dict:
        """Get robust scan code map for Razer keyboard (F-keys, Nav, Numpad)."""
        return {
            # F-Keys
            59: [(0, 3)], 60: [(0, 4)], 61: [(0, 5)], 62: [(0, 6)],
            63: [(0, 7)], 64: [(0, 8)], 65: [(0, 9)], 66: [(0, 10)],
            67: [(0, 11)], 68: [(0, 12)], 87: [(0, 13)], 88: [(0, 14)],
            1: [(0, 0)], # Esc

            # Nav Block (Extended keys)
            82 + 256: [(1, 15)], 71 + 256: [(1, 16)], 73 + 256: [(1, 17)], # Ins, Home, PgUp
            83 + 256: [(2, 15)], 79 + 256: [(2, 16)], 81 + 256: [(2, 17)], # Del, End, PgDn

            # Raw codes for Nav collision fallback
            71: [(2, 18)], 72: [(2, 19)], 73: [(2, 20)],

            # Numpad (Raw codes)
            75: [(3, 18)], 76: [(3, 19)], 77: [(3, 20)],
            79: [(4, 18)], 80: [(4, 19)], 81: [(4, 20)],
            82: [(5, 18), (5, 19)], # Num 0 (Wide)
            83: [(5, 20)], 74: [(1, 21)], 78: [(2, 21), (3, 21)],
            55: [(1, 20)], 53: [(1, 19)], 69: [(1, 18)],

            # Enter (Both)
            28: [(3, 14), (4, 21), (5, 21)],

            # Arrows (Extended)
            72 + 256: [(4, 16), (4, 17)], 75 + 256: [(5, 15)],
            80 + 256: [(5, 16), (5, 17)], 77 + 256: [(5, 18)],
        }

    def _get_key_map(self) -> Dict:
        """Get fallback key map for standard keys (A-Z, Numbers)."""
        return {
            # Row 1
            '`': [(1, 1)], '1': [(1, 2)], '2': [(1, 3)], '3': [(1, 4)], '4': [(1, 5)],
            '5': [(1, 6)], '6': [(1, 7)], '7': [(1, 8)], '8': [(1, 9)], '9': [(1, 10)],
            '0': [(1, 11)], '-': [(1, 12)], '=': [(1, 13)],
            'backspace': [(1, 14), (1, 15)],

            # Row 2
            'tab': [(2, 1)], 'q': [(2, 2)], 'w': [(2, 3)], 'e': [(2, 4)], 'r': [(2, 5)],
            't': [(2, 6)], 'y': [(2, 7)], 'u': [(2, 8)], 'i': [(2, 9)], 'o': [(2, 10)],
            'p': [(2, 11)], '[': [(2, 12)], ']': [(2, 13)], '\\': [(2, 14)],

            # Row 3
            'caps lock': [(3, 1)], 'a': [(3, 2)], 's': [(3, 3)], 'd': [(3, 4)], 'f': [(3, 5)],
            'g': [(3, 6)], 'h': [(3, 7)], 'j': [(3, 8)], 'k': [(3, 9)], 'l': [(3, 10)],
            ';': [(3, 11)], "'": [(3, 12)], 'enter': [(3, 14), (4, 21), (5, 21)],

            # Row 4
            'shift': [(4, 1), (4, 2)], 'z': [(4, 3)], 'x': [(4, 4)], 'c': [(4, 5)],
            'v': [(4, 6)], 'b': [(4, 7)], 'n': [(4, 8)], 'm': [(4, 9)], ',': [(4, 10)],
            '.': [(4, 11)], '/': [(4, 12)], 'right shift': [(4, 14), (4, 15)],

            # Row 5
            'ctrl': [(5, 1)], 'left windows': [(5, 2)], 'alt': [(5, 3)],
            'space': [(5, 6), (5, 7), (5, 8)], 'right alt': [(5, 11)], 'right ctrl': [(5, 14)],
        }

    def _get_cells_for_key(self, event, scan_map, key_map) -> Optional[List[tuple]]:
        """Resolve key event to grid cells using scan codes first."""
        scan = event.scan_code
        if (scan + 256) in scan_map: return scan_map[scan + 256]
        if scan in scan_map: return scan_map[scan]

        key = event.name.lower()
        if key in key_map: return key_map[key]
        return None

    def reactive(self, duration: float = 60.0) -> None:
        """Software-based Reactive effect (lights up on keypress)."""
        if not self.session: return
        try: import keyboard
        except ImportError: print("Keyboard lib missing"); return

        scan_map = self._get_scan_code_map()
        key_map = self._get_key_map()
        active_keys = {}
        lock = threading.Lock()

        def on_press(e):
            cells = self._get_cells_for_key(e, scan_map, key_map)
            if cells:
                with lock:
                    for c in cells: active_keys[c] = 1.0

        keyboard.on_press(on_press)

        end_time = time.time() + duration
        try:
            while time.time() < end_time:
                grid = [[rgb_to_bgr(20, 10, 30)]*22 for _ in range(6)]
                with lock:
                    to_remove = []
                    for coord, brightness in list(active_keys.items()):
                        if brightness > 0:
                            r, c = coord
                            color = rgb_to_bgr(0, int(255*brightness), int(100*brightness))
                            if 0 <= r < 6 and 0 <= c < 22: grid[r][c] = color
                            active_keys[coord] -= 0.08
                        else:
                            to_remove.append(coord)
                    for k in to_remove: del active_keys[k]

                try: requests.put(f"{self.session.uri}/keyboard", json={"effect": "CHROMA_CUSTOM", "param": grid}, timeout=0.1)
                except: pass

                if active_keys:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_STATIC", "param": {"color": rgb_to_bgr(0, 255, 100)}}, timeout=0.1)
                    except: pass

                time.sleep(0.05)
                if int(time.time()) % 2 == 0:
                    try: requests.put(f"{self.session.uri}/heartbeat", timeout=1)
                    except: pass
        finally:
            keyboard.unhook_all()

    def ripple(self, duration: float = 60.0) -> None:
        """
        Software-based Ripple effect (radial wave from keypress).
        Requires 'keyboard' library.
        """
        if not self.session: return
        try:
            import keyboard
            import math
            import random
        except ImportError: print("Missing libs"); return

        scan_map = self._get_scan_code_map()
        key_map = self._get_key_map()
        ripples = []
        lock = threading.Lock()

        SPEED = 15.0
        THICKNESS = 2.0
        FADE_DIST = 15.0

        def on_press(e):
            cells = self._get_cells_for_key(e, scan_map, key_map)
            if cells:
                # Average center
                r = sum(c[0] for c in cells)/len(cells)
                c = sum(c[1] for c in cells)/len(cells)

                # Random color
                rgb = (random.randint(50,255), random.randint(50,255), random.randint(50,255))

                with lock:
                    ripples.append({"origin": (r, c), "start": time.time(), "color": rgb})

        keyboard.on_press(on_press)

        end_time = time.time() + duration
        try:
            while time.time() < end_time:
                now = time.time()
                # Use RGB grid for mixing
                grid_rgb = [[(0,0,0) for _ in range(22)] for _ in range(6)]

                with lock:
                    active_ripples = []
                    for rip in ripples:
                        dt = now - rip["start"]
                        radius = dt * SPEED

                        if radius - THICKNESS < FADE_DIST + 5:
                            active_ripples.append(rip)
                            rip_col = rip["color"]

                            # Bounding box optimization
                            min_r = max(0, int(rip["origin"][0] - radius - THICKNESS))
                            max_r = min(6, int(rip["origin"][0] + radius + THICKNESS + 1))
                            min_c = max(0, int(rip["origin"][1] - radius - THICKNESS))
                            max_c = min(22, int(rip["origin"][1] + radius + THICKNESS + 1))

                            for r in range(min_r, max_r):
                                for c in range(min_c, max_c):
                                    dr, dc = r - rip["origin"][0], c - rip["origin"][1]
                                    dist = math.sqrt(dr*dr + dc*dc)
                                    diff = abs(dist - radius)

                                    if diff < THICKNESS:
                                        bri = (1.0 - (diff/THICKNESS)) * max(0, 1.0 - (dist/FADE_DIST))
                                        if bri > 0:
                                            curr = grid_rgb[r][c]
                                            grid_rgb[r][c] = (
                                                min(255, curr[0] + int(rip_col[0]*bri)),
                                                min(255, curr[1] + int(rip_col[1]*bri)),
                                                min(255, curr[2] + int(rip_col[2]*bri))
                                            )
                    ripples = active_ripples

                # Render to BGR
                final_grid = []
                for r in range(6):
                    row = []
                    for c in range(22):
                        rgb = grid_rgb[r][c]
                        row.append(rgb_to_bgr(rgb[0], rgb[1], rgb[2]))
                    final_grid.append(row)

                try: requests.put(f"{self.session.uri}/keyboard", json={"effect": "CHROMA_CUSTOM", "param": final_grid}, timeout=0.1)
                except: pass

                if ripples:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_STATIC", "param": {"color": rgb_to_bgr(0, 50, 100)}}, timeout=0.1)
                    except: pass

                time.sleep(0.05)
                if int(time.time()) % 2 == 0:
                    try: requests.put(f"{self.session.uri}/heartbeat", timeout=1)
                    except: pass
        finally:
            keyboard.unhook_all()

    def matrix(self, duration: float = 60.0) -> None:
        """
        Software-based Matrix Rain effect (Falling green trails).
        """
        if not self.session: return
        try:
            import random
            import keyboard
        except ImportError: return

        COLS = 22
        ROWS = 6
        drops = [] # {col, row, speed, tail_len}
        lock = threading.Lock()

        def spawn_drop():
            return {
                "col": random.randint(0, COLS - 1),
                "row": -random.uniform(0, 3),
                "speed": random.uniform(8.0, 15.0),
                "tail_len": random.randint(3, 8)
            }

        # Initial spawn
        for _ in range(10): drops.append(spawn_drop())

        end_time = time.time() + duration
        last_time = time.time()

        # Hook keyboard (if needed for exit, or share?)
        # Let's just run loop
        try:
            while time.time() < end_time:
                now = time.time()
                dt = now - last_time
                last_time = now

                # Logic
                grid = [[(0,0,0) for _ in range(COLS)] for _ in range(ROWS)]

                with lock:
                    active_drops = []
                    if random.random() < 0.3: drops.append(spawn_drop())

                    for drop in drops:
                        drop["row"] += drop["speed"] * dt
                        head_row = int(drop["row"])
                        col = drop["col"]

                        for i in range(drop["tail_len"]):
                            r_pos = head_row - i
                            if 0 <= r_pos < ROWS:
                                if i == 0: color = (200, 255, 200) # Head
                                else:
                                    fade = 1.0 - (i / drop["tail_len"])
                                    color = (0, int(255 * fade), 0)

                                curr = grid[r_pos][col]
                                grid[r_pos][col] = (
                                    max(curr[0], color[0]),
                                    max(curr[1], color[1]),
                                    max(curr[2], color[2])
                                )

                        if drop["row"] - drop["tail_len"] < ROWS:
                            active_drops.append(drop)
                    drops = active_drops

                # Render
                final_grid = []
                for r in range(ROWS):
                    row_vals = []
                    for c in range(COLS):
                        rgb = grid[r][c]
                        row_vals.append(rgb_to_bgr(rgb[0], rgb[1], rgb[2]))
                    final_grid.append(row_vals)

                try: requests.put(f"{self.session.uri}/keyboard", json={"effect": "CHROMA_CUSTOM", "param": final_grid}, timeout=0.1)
                except: pass

                # Mouse glitch
                if random.random() < 0.1:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_STATIC", "param": {"color": rgb_to_bgr(0, 255, 0)}}, timeout=0.1)
                    except: pass
                else:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_NONE"}, timeout=0.1)
                    except: pass

                time.sleep(0.05)
                if int(time.time()) % 2 == 0:
                    try: requests.put(f"{self.session.uri}/heartbeat", timeout=1)
                    except: pass
        finally:
            pass # No keyboard hook to clean up for pure animation
    def theme_dav1d(self, loop: bool = False) -> None:
        """
        Dav1d Theme: Blue Matrix Rain + Purple/Neon Key Interaction.
        - Background: Blue Matrix Rain (Cold trails)
        - Key Press: Purple Reactive Glow + Neon Ripple
        """
        if not self.session: return
        try:
            import random
            import keyboard
            import math
        except ImportError: return

        lock = threading.Lock()

        # State
        COLS = 22; ROWS = 6
        drops = []
        ripples = []
        reactive_keys = {} # (r,c) -> brightness

        # --- LOGIC HELPERS ---
        def spawn_drop():
            return {
                "col": random.randint(0, COLS - 1),
                "row": -random.uniform(0, 3),
                "speed": random.uniform(4.0, 10.0), # Slower, colder
                "tail_len": random.randint(4, 10)
            }

        def get_neon_color():
            # Bright neon colors
            colors = [
                (255, 0, 255), # Magenta
                (0, 255, 255), # Cyan
                (255, 255, 0), # Yellow
                (255, 50, 50), # Red-ish
                (0, 255, 100), # Green-ish
            ]
            return random.choice(colors)

        # Init drops
        for _ in range(12): drops.append(spawn_drop())

        # Maps
        scan_map = self._get_scan_code_map()
        key_map = self._get_key_map()

        # Input Handler
        def on_press(e):
            cells = self._get_cells_for_key(e, scan_map, key_map)
            if cells:
                # Calc average for ripple
                r_avg = sum(c[0] for c in cells)/len(cells)
                c_avg = sum(c[1] for c in cells)/len(cells)

                with lock:
                    # Add Purple Reactive (Static Glow)
                    for c in cells:
                        reactive_keys[c] = 1.0

                    # Add Neon Ripple
                    ripples.append({
                        "origin": (r_avg, c_avg),
                        "start": time.time(),
                        "color": get_neon_color()
                    })

        keyboard.on_press(on_press)

        # Main Loop
        last_time = time.time()

        # Ripple Constants
        R_SPEED = 18.0
        R_THICK = 1.5
        R_FADE = 12.0

        try:
            while True:
                # If not looping forever (e.g. testing), break on ESC
                if not loop and keyboard.is_pressed('esc'): break
                # If main thread dies (when running as daemon), we should stop?
                # Rely on daemon thread to be killed by OS/Python.

                now = time.time()
                dt = now - last_time
                last_time = now
                if dt > 0.1: dt = 0.1 # Clamp lag

                # Composition Gird (RGB)
                grid_rgb = [[(0,0,0) for _ in range(COLS)] for _ in range(ROWS)]

                with lock:
                    # 1. Update Matrix (Blue)
                    active_drops = []
                    if random.random() < 0.2: drops.append(spawn_drop())
                    for drop in drops:
                        drop["row"] += drop["speed"] * dt
                        head = int(drop["row"])
                        col = drop["col"]
                        for i in range(drop["tail_len"]):
                            r_pos = head - i
                            if 0 <= r_pos < ROWS:
                                fade = 1.0 - (i/drop["tail_len"])
                                bri = int(255 * fade)
                                # Cold Blue: (20, 100, 255) max
                                b_val = int(255 * fade)
                                g_val = int(100 * fade)
                                color = (0, g_val, b_val)
                                if i == 0: color = (180, 220, 255) # Head White-Blue

                                # Add to grid
                                c_g = grid_rgb[r_pos][col]
                                grid_rgb[r_pos][col] = (
                                    max(c_g[0], color[0]),
                                    max(c_g[1], color[1]),
                                    max(c_g[2], color[2]) # Keep strongest
                                )
                        if drop["row"] - drop["tail_len"] < ROWS: active_drops.append(drop)
                    drops = active_drops

                    # 2. Update Reactive (Purple) & Ripple (Neon)
                    active_keys_clean = {}
                    for coord, bri in reactive_keys.items():
                        if bri > 0.01:
                            # Purple: (160, 32, 240)
                            color = (int(160*bri), int(32*bri), int(240*bri))
                            r, c = coord
                            if 0<=r<ROWS and 0<=c<COLS:
                                c_g = grid_rgb[r][c]
                                grid_rgb[r][c] = (
                                    min(255, c_g[0] + color[0]),
                                    min(255, c_g[1] + color[1]),
                                    min(255, c_g[2] + color[2])
                                )
                            active_keys_clean[coord] = bri - (3.0 * dt) # Fast fade
                    reactive_keys = active_keys_clean

                    active_rips = []
                    for rip in ripples:
                        age = now - rip["start"]
                        radius = age * R_SPEED

                        if radius - R_THICK < R_FADE + 2:
                            active_rips.append(rip)
                            # Render Ring
                             # Bounding box
                            min_r = max(0, int(rip["origin"][0] - radius - R_THICK))
                            max_r = min(6, int(rip["origin"][0] + radius + R_THICK + 1))
                            min_c = max(0, int(rip["origin"][1] - radius - R_THICK))
                            max_c = min(22, int(rip["origin"][1] + radius + R_THICK + 1))

                            rip_c = rip["color"]

                            for r in range(min_r, max_r):
                                for c in range(min_c, max_c):
                                    dr, dc = r - rip["origin"][0], c - rip["origin"][1]
                                    dist = math.sqrt(dr*dr + dc*dc)
                                    diff = abs(dist - radius)

                                    if diff < R_THICK:
                                        bri = (1.0 - (diff/R_THICK)) * max(0, 1.0 - (dist/R_FADE))
                                        if bri > 0:
                                            c_g = grid_rgb[r][c]
                                            # Additive
                                            grid_rgb[r][c] = (
                                                min(255, c_g[0] + int(rip_c[0]*bri)),
                                                min(255, c_g[1] + int(rip_c[1]*bri)),
                                                min(255, c_g[2] + int(rip_c[2]*bri))
                                            )
                    ripples = active_rips

                # Render Final
                final_grid = []
                for r in range(ROWS):
                    row_vals = []
                    for c in range(COLS):
                        rgb = grid_rgb[r][c]
                        row_vals.append(rgb_to_bgr(rgb[0], rgb[1], rgb[2]))
                    final_grid.append(row_vals)

                try: requests.put(f"{self.session.uri}/keyboard", json={"effect": "CHROMA_CUSTOM", "param": final_grid}, timeout=0.05)
                except: pass

                # Mouse: Pulse Blue
                if int(now * 2) % 2 == 0:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_STATIC", "param": {"color": rgb_to_bgr(0, 0, 150)}}, timeout=0.05)
                    except: pass
                else:
                    try: requests.put(f"{self.session.uri}/mouse", json={"effect": "CHROMA_NONE"}, timeout=0.05)
                    except: pass

                time.sleep(0.04)
                if int(time.time()) % 2 == 0:
                    try: requests.put(f"{self.session.uri}/heartbeat", timeout=1)
                    except: pass
        finally:
            keyboard.unhook_all()

# ============================================================================
# CONVENIENCE FUNCTIONS FOR DAV1D TOOLS
# ============================================================================

# Global instance for persistent connection
_chroma_client: Optional[RazerChroma] = None


def get_chroma_client() -> RazerChroma:
    """Get or create the global Chroma client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = RazerChroma()
    return _chroma_client


def chroma_set_color(color: str, device: str = "all") -> Dict:
    """
    Set RGB color on Razer devices. Dav1d tool function.

    Args:
        color: Color name (red, green, blue, yellow, cyan, magenta, white, orange, purple)
               or hex code (#RRGGBB)
        device: Device name (keyboard, mouse, headset, mousepad, keypad, chromalink, all)

    Returns:
        Dict with success status
    """
    client = get_chroma_client()

    # Connect if not already connected
    if not client.session:
        connect_result = client.connect()
        if not connect_result["success"]:
            return connect_result

    # Parse color
    color_map = {
        "red": Colors.RED,
        "green": Colors.GREEN,
        "blue": Colors.BLUE,
        "yellow": Colors.YELLOW,
        "cyan": Colors.CYAN,
        "magenta": Colors.MAGENTA,
        "white": Colors.WHITE,
        "black": Colors.BLACK,
        "orange": Colors.ORANGE,
        "purple": Colors.PURPLE,
    }

    if color.startswith("#"):
        bgr_color = hex_to_bgr(color)
    elif color.lower() in color_map:
        bgr_color = color_map[color.lower()]
    else:
        return {"success": False, "error": f"Unknown color: {color}. Use color name or #RRGGBB hex."}

    # Apply to device(s)
    device = device.lower()
    if device == "all":
        return client.set_all_static(bgr_color)
    else:
        try:
            device_enum = Device(device)
            return client.set_static_color(device_enum, bgr_color)
        except ValueError:
            return {"success": False, "error": f"Unknown device: {device}. Options: keyboard, mouse, headset, mousepad, keypad, chromalink, all"}


def chroma_off(device: str = "all") -> Dict:
    """
    Turn off RGB lighting on Razer devices.

    Args:
        device: Device name or 'all'
    """
    client = get_chroma_client()

    if not client.session:
        return {"success": True, "message": "Already off (not connected)"}

    device = device.lower()
    if device == "all":
        return client.turn_off_all()
    else:
        try:
            device_enum = Device(device)
            return client.turn_off(device_enum)
        except ValueError:
            return {"success": False, "error": f"Unknown device: {device}"}


def chroma_disconnect() -> Dict:
    """Disconnect from Chroma SDK and free resources."""
    client = get_chroma_client()
    return client.disconnect()


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("🎮 Razer Chroma SDK - ACTIVE DRIVE TEST")
    print("=" * 40)
    print("This test uses a 10Hz drive loop to keep the stand active.")

    chroma = RazerChroma()

    # Connect
    print("\n📡 Connecting...")
    result = chroma.connect()
    print(f"Connect: {result}")

    if result.get("success"):
        # Test Loop
        print("\n🌈 STARTING PERSISTENT COLOR CYCLE (30 Seconds)")
        print("!!! LOOK AT THE STAND BASE !!!")

        try:
            # 1. RED
            print("-> Driving RED (10 seconds)...")
            chroma.set_all_static(Colors.RED)
            time.sleep(10)

            # 2. GREEN
            print("-> Driving GREEN (10 seconds)...")
            chroma.set_all_static(Colors.GREEN)
            time.sleep(10)

            # 3. BLUE
            print("-> Driving BLUE (10 seconds)...")
            chroma.set_all_static(Colors.BLUE)
            time.sleep(10)

        except KeyboardInterrupt:
            print("\nInterrupted by user.")

        # Final State: WHITE before Exit
        print("\n⚪ Final state: WHITE (3 seconds)...")
        chroma.set_all_static(Colors.WHITE)
        time.sleep(3)

        # Disconnect
        print("\n🔌 Disconnecting...")
        chroma.disconnect()
        print("Done!")
    else:
        print("Failed to connect. Is Razer Synapse running?")
