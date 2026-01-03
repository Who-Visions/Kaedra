"""
Razer Chroma REST Service
Allows Kaedra to control Razer peripherals via local REST API.

API Docs: https://assets.razerzone.com/dev_portal/REST/html/index.html
"""
import requests
import time
import threading
import json
import random
import colorsys
from typing import Callable, Optional, Dict, Any

import logging
log = logging.getLogger("kaedra")

class RazerService:
    """
    Control Razer Chroma devices via local REST API.
    Requires Razer Synapse with 'Chroma Connect' enabled.
    """
    
    DEFAULT_URI = "http://localhost:54235/razer/chromasdk"
    
    def __init__(self):
        self.uri: Optional[str] = None
        self.session_id: Optional[int] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False
        self.session = requests.Session()
        
        # Define base pallet for common colors (BGR format for Razer)
        self.COLORS = {
            "red": 0x0000FF,
            "green": 0x00FF00,
            "blue": 0xFF0000,
            "white": 0xFFFFFF,
            "black": 0x000000,
            "orange": 0x00A5FF, # approx
            "purple": 0x800080,
            "cyan": 0xFFFF00,
            "yellow": 0x00FFFF,
            "pink": 0xCBC0FF,
            "magenta": 0xFF00FF
        }

    def connect(self) -> bool:
        """Handshake with Razer Synapse to get session URI."""
        payload = {
            "title": "Kaedra Story Engine",
            "description": "AI Narrative Lighting Control",
            "author": {"name": "Who Visions", "contact": "dave@whovisions.com"},
            "device_supported": ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink"],
            "category": "application"
        }
        
        try:
            resp = requests.post(self.DEFAULT_URI, json=payload, timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                self.uri = data.get("uri")
                self.session_id = data.get("sessionid")
                
                if self.uri:
                    log.info(f"Razer Chroma connected: {self.uri}")
                    self._start_heartbeat()
                    
                    # Visual Confirmation: Flash Green
                    self.set_static("green")
                    threading.Timer(1.0, self.restore).start()
                    
                    return True
            else:
                log.warning(f"Razer connect failed: {resp.status_code}")
                
        except Exception as e:
            # Common if Synapse isn't running
            log.warning(f"Razer Chroma handshake error: {e}") 
            pass
            
        return False

    def _start_heartbeat(self):
        """Keep connection alive (required every 15s, we do 5s)."""
        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        while self._running and self.uri:
            try:
                self.session.put(f"{self.uri}/heartbeat", timeout=2)
                time.sleep(1.0) # 1s tick per manufacturer guidance
            except:
                # Connection likely lost
                pass

    def close(self):
        """Clean disconnect."""
        self._running = False
        self.stop_effect()
        if self.uri:
            try:
                self.session.delete(self.uri, timeout=1)
            except:
                pass
        self.uri = None
        # Don't close session, might reconnect? Actually fine to keep open.

    def _send(self, endpoint: str, method: str = "PUT", json_data: Dict = None) -> Dict:
        """Send raw request to session URI."""
        if not self.uri:
            return {}
        try:
            url = f"{self.uri}/{endpoint}"
            r = self.session.request(method, url, json=json_data, timeout=0.5)
            # Short timeout for effects to prevent blocking
            return r.json() if r.text else {}
        except:
            return {}

    # ═══════════════════════════════════════════════════════════════════════════
    # EFFECTS
    # ═══════════════════════════════════════════════════════════════════════════

    def set_static(self, color_name: str):
        """Set all devices to a static color."""
        color = self.COLORS.get(color_name.lower(), 0xFFFFFF)
        
        # 'CHROMA_STATIC' effect
        payload = {"effect": "CHROMA_STATIC", "param": {"color": color}}
        
        # Broadcast to main devices
        self._send("keyboard", json_data=payload)
        self._send("mouse", json_data=payload)
        self._send("mousepad", json_data=payload)
        self._send("headset", json_data=payload)
        self._send("chromalink", json_data=payload)

    def set_color_hex(self, hex_val: int):
        """Set static color by hex integer (0xBBGGRR)."""
        payload = {"effect": "CHROMA_STATIC", "param": {"color": hex_val}}
        self._send("keyboard", json_data=payload)
        self._send("mouse", json_data=payload)

    def set_fire(self):
        """Simulate fire effect (Orange/Red static or breathing)."""
        self.breathe("orange", "red")

    def breathe(self, color1: str, color2: str = None):
        """Breathing effect."""
        c1 = self.COLORS.get(color1.lower(), 0xFFFFFF)
        
        if color2:
            c2 = self.COLORS.get(color2.lower(), 0x000000)
            # CHROMA_BREATHING type 2 (Two colors)
            payload = {"effect": "CHROMA_BREATHING", "param": {"color": c1, "color2": c2, "type": 2}}
        else:
            payload = {"effect": "CHROMA_BREATHING", "param": {"color": c1, "color2": 0x000000, "type": 2}}

        self._send("keyboard", json_data=payload)
        self._send("mouse", json_data=payload)
        self._send("mousepad", json_data=payload)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHROMA LINK (3rd Party Devices - 5 Virtual LEDs)
    # ═══════════════════════════════════════════════════════════════════════════
    
    CHROMALINK_LEDS = 5

    def set_chromalink_static(self, color_name: str):
        """Set all 5 ChromaLink LEDs to a static color."""
        color = self.COLORS.get(color_name.lower(), 0xFFFFFF)
        payload = {"effect": "CHROMA_STATIC", "param": {"color": color}}
        self._send("chromalink", json_data=payload)

    def set_chromalink_zones(self, zone_colors: list):
        """
        Set individual colors for each of the 5 ChromaLink LEDs.
        zone_colors: List of 5 color ints (BGR format).
        Example: [0x0000FF, 0x00FF00, 0xFF0000, 0x00A5FF, 0xFFFFFF]
        """
        if len(zone_colors) != self.CHROMALINK_LEDS:
            log.warning(f"ChromaLink requires exactly {self.CHROMALINK_LEDS} colors, got {len(zone_colors)}")
            return
        
        # CHROMA_CUSTOM for chromalink expects a 1D array of 5 colors
        payload = {"effect": "CHROMA_CUSTOM", "param": zone_colors}
        resp = self._send("chromalink", json_data=payload)
        if resp.get("result") == 0:
            pass 
        else:
            log.warning(f"ChromaLink update failed: {resp}")

    def set_chromalink_fire(self):
        """Set ChromaLink to fire-like colors (useful for room ambiance)."""
        # 5 zones: [Primary, Secondary, Accent1, Accent2, Accent3]
        fire_zones = [
            0x0000AA,  # LED 0: Dim Red
            0x0055FF,  # LED 1: Orange
            0x00AAFF,  # LED 2: Bright Orange/Yellow
            0x0055FF,  # LED 3: Orange
            0x0000AA,  # LED 4: Dim Red
        ]
        self.set_chromalink_zones(fire_zones)

    # Grid Dimensions (Blade 15 / BlackWidow)
    COLOR_ROWS = 8
    COLOR_COLS = 24
    KEY_ROWS = 6
    KEY_COLS = 22
    
    ROWS = COLOR_ROWS
    COLS = COLOR_COLS

    def set_custom(self, grid):
        """
        Apply a 6x22 color grid to the keyboard.
        grid: List[List[int]] - 6 rows of 22 cols (int colors).
        """
        if not self.uri: return
        
        if len(grid) != self.COLOR_ROWS or (grid and len(grid[0]) != self.COLOR_COLS):
            # log.warning(f"Grid size mismatch: expected {self.COLOR_ROWS}x{self.COLOR_COLS}")
            return
        
        payload = {
            "effect": "CHROMA_CUSTOM2",
            "param": {
                "color": grid,
                "key": [[0] * self.KEY_COLS for _ in range(self.KEY_ROWS)]
            }
        }
        self._send("keyboard", json_data=payload)

    # ═══════════════════════════════════════════════════════════════════════════
    # ANIMATIONS & HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return lo if x < lo else hi if x > hi else x

    @staticmethod
    def _bgr_int_from_hsv(h: float, s: float, v: float) -> int:
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        rr = int(RazerService._clamp(r) * 255)
        gg = int(RazerService._clamp(g) * 255)
        bb = int(RazerService._clamp(b) * 255)
        # BGR packed int: 0x00BBGGRR
        return (bb << 16) | (gg << 8) | rr

    @staticmethod
    def _named_hue(color_name: str) -> float:
        name = (color_name or "").strip().lower()
        return {
            "red": 0.00, "orange": 0.08, "yellow": 0.16, "green": 0.33,
            "cyan": 0.50, "blue": 0.66, "purple": 0.78, "magenta": 0.86,
            "pink": 0.92, "white": 0.00, "black": 0.00,
        }.get(name, 0.66)

    def _start_effect(self, runner: Callable[[], None]) -> None:
        if not hasattr(self, '_effect_lock'):
             self._effect_lock = threading.RLock()
             self._effect_stop = threading.Event()
             
        with self._effect_lock:
            self.stop_effect()
            self._effect_stop.clear()
            self._effect_thread = threading.Thread(target=runner, daemon=True)
            self._effect_thread.start()

    def stop_effect(self):
        """Stop active animation."""
        if not hasattr(self, '_effect_lock'): return
        
        with self._effect_lock:
            self._effect_stop.set()
            t = getattr(self, '_effect_thread', None)
            self._effect_thread = None
            
        if t and t.is_alive():
            t.join(timeout=0.2)
        
        self.restore()

    def restore(self):
        """Reset to None (let Synapse take over) or Default White."""
        if not self.uri: return
        for device in ["keyboard", "mouse", "headset", "mousepad", "keypad", "chromalink", "headsetstand"]:
             try:
                 self.session.delete(f"{self.uri}/{device}", timeout=1)
             except: pass

    def broadcast_static(self, color_int: int):
        """Public alias for _broadcast_static."""
        self._broadcast_static(color_int)

    def _broadcast_static(self, color_int: int):
        """Send static color to non-keyboard devices."""
        payload = {"effect": "CHROMA_STATIC", "param": {"color": int(color_int)}}
        # Skip keyboard as it uses CHROMA_CUSTOM
        for device in ["mouse", "headset", "mousepad", "keypad", "chromalink", "headsetstand"]:
            self._send(device, json_data=payload)

    # ═══════════════════════════════════════════════════════════════════════════
    # SPECIFIC EFFECTS
    # ═══════════════════════════════════════════════════════════════════════════

    def start_fire_effect(self):
        """Original fire effect wrapper."""
        self.stop_effect()
        # Fire Theme: Deep Red, Orange, Yellow
        DIM_RED = 0x000055
        RED = 0x0000FF
        ORANGE = 0x00A5FF
        YELLOW = 0x00FFFF
        
        def runner():
            import random
            while not self._effect_stop.is_set():
                grid = [[DIM_RED for _ in range(self.COLS)] for _ in range(self.ROWS)]
                for r in range(2, 6):
                    for c in range(self.COLS):
                        chance = random.random()
                        if chance > 0.90: grid[r][c] = YELLOW
                        elif chance > 0.70: grid[r][c] = ORANGE
                        elif chance > 0.50: grid[r][c] = RED
                
                try:
                    self.set_custom(grid)
                    time.sleep(0.1)
                except: break

        self._start_effect(runner)

    def start_wave_effect(self, color_name: str = "cyan", period: float = 2.5, brightness: float = 0.6, fps: int = 30):
        import math
        hue = self._named_hue(color_name)
        width, height = self.COLOR_COLS, self.COLOR_ROWS
        base_color_int = self._bgr_int_from_hsv(hue, 1.0, brightness)

        def runner():
            t0 = time.time()
            dt = 1.0 / max(1, fps)
            frame_count = 0
            
            # Initial set for peripherals
            self._broadcast_static(base_color_int)
            
            while not self._effect_stop.is_set():
                t = time.time() - t0
                grid = []
                phase = (t / max(0.05, period)) * 2.0 * math.pi
                for y in range(height):
                    row = []
                    for x in range(width):
                        wave = (1.0 + math.sin(phase - (x / width) * 2.0 * math.pi)) * 0.5
                        v = self._clamp(0.05 + brightness * wave)
                        row.append(self._bgr_int_from_hsv(hue, 1.0, v))
                    grid.append(row)
                self.set_custom(grid)
                
                # Peripherals: Just keep them static base color (already set), 
                # or maybe pulse them gently? Static is safer for wave.
                # Re-broadcast occasionally in case of packet loss
                if frame_count % 30 == 0:
                     self._broadcast_static(base_color_int)
                
                frame_count += 1
                time.sleep(dt)

        self._start_effect(runner)

    def start_rainbow_cycle(self, period: float = 4.0, brightness: float = 0.55, fps: int = 30):
        width, height = self.COLOR_COLS, self.COLOR_ROWS

        def runner():
            t0 = time.time()
            dt = 1.0 / max(1, fps)
            frame_count = 0
            while not self._effect_stop.is_set():
                t = time.time() - t0
                base = (t / max(0.05, period)) % 1.0
                
                # Peripherals: Update every 5th frame (~6 FPS) to save bandwidth
                if frame_count % 5 == 0:
                     peri_color = self._bgr_int_from_hsv(base, 1.0, brightness)
                     self._broadcast_static(peri_color)

                grid = []
                for y in range(height):
                    row = []
                    for x in range(width):
                        h = (base + (x / width)) % 1.0
                        row.append(self._bgr_int_from_hsv(h, 1.0, brightness))
                    grid.append(row)
                self.set_custom(grid)
                frame_count += 1
                time.sleep(dt)

        self._start_effect(runner)

    def start_lightning_effect(self, base_color: str = "purple", base_brightness: float = 0.10, fps: int = 30):
        base_hue = self._named_hue(base_color)
        width, height = self.COLOR_COLS, self.COLOR_ROWS

        def runner():
            import random
            dt = 1.0 / max(1, fps)
            base_val = self._clamp(base_brightness)
            base_color_int = self._bgr_int_from_hsv(base_hue, 1.0, base_val)
            white_int = self._bgr_int_from_hsv(0.0, 0.0, 1.0) # White

            while not self._effect_stop.is_set():
                # Idle
                grid = [[base_color_int for _ in range(width)] for _ in range(height)]
                self.set_custom(grid)
                self._broadcast_static(base_color_int)

                wait_s = random.uniform(1.2, 4.0)
                end = time.time() + wait_s
                while time.time() < end and not self._effect_stop.is_set():
                    time.sleep(0.05)

                # Strike
                for _ in range(random.randint(1, 3)):
                    n = random.randint(12, 40)
                    coords = {(random.randrange(height), random.randrange(width)) for _ in range(n)}
                    
                    # Flash All Devices White
                    self._broadcast_static(white_int)
                    
                    for f in range(6):
                        if self._effect_stop.is_set(): return
                        decay = 1.0 - (f / 5.0)
                        
                        # Peripherals flash decay? Too fast. Just reset to base after flash.
                        if f == 0: self._broadcast_static(white_int)
                        elif f == 3: self._broadcast_static(base_color_int)
                        
                        grid = [[base_color_int for _ in range(width)] for _ in range(height)]
                        for (yy, xx) in coords:
                            grid[yy][xx] = self._bgr_int_from_hsv(0.0, 0.0, decay) # white flash
                        self.set_custom(grid)
                        time.sleep(dt)
                
                # Ensure we return to base
                self._broadcast_static(base_color_int)

        self._start_effect(runner)

    def start_tension_pulse(self, get_tension: Callable[[], float], color_name: str = "red", min_b: float = 0.08, max_b: float = 0.75, period: float = 0.9, fps: int = 30):
        import math
        hue = self._named_hue(color_name)
        width, height = self.COLOR_COLS, self.COLOR_ROWS

        def runner():
            t0 = time.time()
            dt = 1.0 / max(1, fps)
            frame_count = 0
            while not self._effect_stop.is_set():
                t = time.time() - t0
                try:
                    tension = self._clamp(float(get_tension() or 0.0))
                except: tension = 0.0
                
                # Pulse amplitude rises with tension
                pulse = (1.0 + math.sin((t / max(0.05, period)) * 2.0 * math.pi)) * 0.5
                v = min_b + (max_b - min_b) * (0.25 + 0.75 * tension) * pulse
                bgr = self._bgr_int_from_hsv(hue, 1.0, self._clamp(v))
                
                if frame_count % 3 == 0: # 10 FPS updates for peripherals
                     self._broadcast_static(bgr)

                grid = [[bgr for _ in range(width)] for _ in range(height)]
                self.set_custom(grid)
                frame_count += 1
                time.sleep(dt)

        self._start_effect(runner)

if __name__ == "__main__":
    # Test
    razer = RazerService()
    if razer.connect():
        print("Connected!")
        print("Wave...")
        razer.start_wave_effect()
        time.sleep(3)
        print("Lightning...")
        razer.start_lightning_effect()
        time.sleep(5)
        razer.close()
    else:
        print("Not connected.")
