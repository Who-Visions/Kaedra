"""
StoryEngine LIFX Integration
Rate limiting, deduplication, and light control.
"""
import time
import random
import queue
import threading
from datetime import datetime
from typing import Callable, Optional

from kaedra.core.config import LIFX_TOKEN
from kaedra.services.lifx import LIFXService
from kaedra.services.razer import RazerService

from .config import RateLimitConfig
from .ui import log


class LifxGate:
    """Rate limiter and deduplicator for LIFX calls."""
    
    def __init__(self, cfg: RateLimitConfig | None = None):
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

    def call(self, fn: Callable, *, sig: str | None = None):
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


class LightsController:
    """Manages LIFX lights with background worker thread."""
    
    def __init__(self, razer_service=None, lifx_service=None):
        self.razer = razer_service
        self.lifx = lifx_service
        self.gate = LifxGate()
        self._lifx_q: queue.Queue = queue.Queue(maxsize=1)
        self._lifx_thread: Optional[threading.Thread] = None
        self._initial_state: Optional[dict] = None
        self._running = False
        self.pulse_count = 0
        self.audio_reactor = None

    def pulse(self, color: str = "white", brightness: float = 1.0, duration: float = 0.1):
        """Short pulse for beat detection (non-blocking)."""
        if self.razer:
            # We use a thread to avoid blocking the engine's physics tick
            threading.Thread(target=self._fire_pulse, args=(color, brightness, duration), daemon=True).start()

    def _fire_pulse(self, color, brightness, duration):
        # 1. Flash ON
        # Convert color name -> HSB -> BGR
        hue = self.razer._named_hue(color)
        bgr = self.razer._bgr_int_from_hsv(hue, 1.0, brightness)
        # Use our new public method
        self.razer.broadcast_static(bgr)
        
        time.sleep(duration)
        
        # 2. Flash OFF (or reset?)
        # Ideally we'd restore previous state, but statutory lighting is complex.
        # For now, just black out to emphasize the beat staccato.
        self.razer.broadcast_static(0x000000)

    def init(self) -> bool:
        """Initialize LIFX with connection status."""
        try:
            # 1. Init Razer (Hardware)
            self.razer = RazerService()
            if self.razer.connect():
                log.info("Razer Chroma linked.")
            else:
                log.warning("Razer Synapse not found (Hardware skipped)")
            
            # 2. Init LIFX (IoT)
            if not LIFX_TOKEN:
                 log.warning("LIFX_TOKEN not set - lights disabled")
                 return False

            self.lifx = LIFXService()
            lights = self.lifx.list_lights()
            if not lights:
                log.warning("LIFX: No lights found")
                return False
                
            # Capture initial state of the target group if possible
            # For now, we just grab the first light's state as a baseline reference
            first_light = lights[0]
            self._initial_state = {
                "color": first_light.color,
                "power": first_light.power,
                "brightness": first_light.brightness
            }
            
            # Start background worker
            self._running = True
            self._lifx_thread = threading.Thread(target=self._worker, daemon=True)
            self._lifx_thread.start()
            
            # Startup Mood: Purple 35%
            # hue=280 (Purple), sat=1.0, bri=0.35
            self.set_color(hue=280, saturation=1.0, brightness=0.35)
            
            log.info(f"LIFX connected: {len(lights)} light(s)")
            return True
        except Exception as e:
            log.warning(f"Lights init panic: {e}")
            return False

    def set_color(self, color_name: str, brightness: float = 1.0):
        """Initialize LIFX with connection status."""
        if not LIFX_TOKEN:
            log.warning("LIFX_TOKEN not set - lights disabled")
            return False
            
        try:
            # 1. Init Razer (Hardware)
            self.razer = RazerService()
            if self.razer.connect():
                log.info("Razer Chroma linked.")
            else:
                log.warning("Razer Synapse not found (Hardware skipped)")
            
            # 2. Init LIFX (IoT)
            self.lifx = LIFXService()
            lights = self.lifx.list_lights()
            if not lights:
                log.warning("LIFX: No lights found")
                return False
                
            # Capture initial state of the target group if possible
            # For now, we just grab the first light's state as a baseline reference
            first_light = lights[0]
            self._initial_state = {
                "color": first_light.color,
                "power": first_light.power,
                "brightness": first_light.brightness
            }
            
            # Start background worker
            self._running = True
            self._lifx_thread = threading.Thread(target=self._worker, daemon=True)
            self._lifx_thread.start()
            
            # Startup Mood: Purple 35%
            # hue=280 (Purple), sat=1.0, bri=0.35
            self.set_color(hue=280, saturation=1.0, brightness=0.35)
            
            log.info(f"LIFX connected: {len(lights)} light(s)")
            return True
            
        except Exception as e:
            log.warning(f"LIFX init failed: {e}")
            return False
    
    def _worker(self):
        """Background worker for LIFX updates."""
        while self._running:
            try:
                update_fn = self._lifx_q.get(timeout=1.0)
                if update_fn:
                    update_fn()
                self._lifx_q.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                log.debug(f"LIFX worker error: {e}")
    
    def request_update(self, update_fn: Callable):
        """Queue a non-blocking LIFX update."""
        if not self.lifx or not self._running:
            return
        try:
            # Drop old if queue full
            while not self._lifx_q.empty():
                try:
                    self._lifx_q.get_nowait()
                    self._lifx_q.task_done()
                except queue.Empty:
                    break
            self._lifx_q.put_nowait(update_fn)
            self.pulse_count += 1
        except queue.Full:
            pass
    
    def fire_mode(self, brightness: float = 0.25):
        """Set Fire Atmosphere: Warm base + Flame effect. Targets Living Room (Eve Safe)."""
        if not self.lifx:
            return

        selector = "group:Living Room"
        
        def do_fire():
            # 1. Base State: Warm Orange @ 25%
            self.gate.call(
                lambda: self.lifx.set_color(selector, color="hue:35 saturation:1.0 kelvin:1500", brightness=brightness, duration=2.0),
                sig="fire_base"
            )
            # 2. Trigger Flame Effect
            self.gate.call(
                lambda: self.lifx.flame(selector, period=5.0),
                sig="fire_fx"
            )
            
            # 3. Razer Broadcast (Animation)
            if self.razer:
                self.razer.start_fire_effect()
                self.razer.set_chromalink_fire()  # Also set 3rd party devices (LIFX Connector)
        
        self.request_update(do_fire)
    
    @property
    def is_night_mode(self) -> bool:
        """Check if currently in Night Mode (11PM - 8AM)."""
        now = datetime.now()
        return now.hour >= 23 or now.hour < 8

    def set_color(self, hue: float, saturation: float, brightness: float, kelvin: int = 3500):
        """Set light color (non-blocking). Targets Living Room (No Eve)."""
        if not self.lifx:
            return

        # Night Mode Safety Cap (Max 60%)
        if self.is_night_mode:
            if brightness > 0.60:
                log.info(f"[Night Mode] Capping brightness {brightness:.2f} -> 0.60")
                brightness = 0.60
            
        # Construct color string for LIFX API
        # hue:0-360 saturation:0.0-1.0
        color_str = f"hue:{hue} saturation:{saturation} kelvin:{kelvin}"
        sig = f"{color_str}:{brightness:.2f}"
        
        # Selector that avoids Eve (Bedroom)
        selector = "group:Living Room"
        
        def do_set():
            self.gate.call(
                lambda: self.lifx.set_color(selector, color=color_str, brightness=brightness, duration=1.0),
                sig=sig
            )

            # Broadcast to Razer (simple color match)
            if self.razer:
                # Basic mapping: "red" -> set_static("red")
                # Strip LIFX params to get color name if possible
                base_color = color_str.split()[0].split(":")[0] 
                if "hue" in base_color: # Handle HSB
                    # TODO: Convert Hue to RGB for Razer
                    pass 
                else:
                    self.razer.set_static(base_color)
        
        self.request_update(do_set)
    
    def breathe(self, color: str = "red", cycles: int = 1, period: float = 2.0, peak: float = 0.5):
        """Trigger breathe effect (non-blocking). Targets Living Room (Eve Safe)."""
        if not self.lifx:
            return
            
        selector = "group:Living Room"
            
        def do_breathe():
            self.gate.call(
                lambda: self.lifx.breathe(selector, color=color, cycles=cycles, period=period, peak=peak),
                sig=f"breathe:{color}"
            )
        
        self.request_update(do_breathe)
        
        # Razer Broadcast
        if self.razer:
            self.razer.breathe(color)
    
    def restore(self):
        """Restore lights to baseline. Night Mode (11pm-6am) = Red 35%, else Day = 4500k 60%."""
        if not self.lifx:
            return
            
        selector = "group:Living Room"
        
        try:
            # Night Mode: 11 PM (23) to 6 AM (6)
            if self.is_night_mode:
                # Night: Red @ 35%
                self.request_update(
                    lambda: self.lifx.set_color(selector, color="red", brightness=0.35, duration=2.0)
                )
                log.info("LIFX Restore: Night Mode (Red 35%)")
            else:
                # Day/Eve: Neutral daylight (4500k) @ 60%
                self.request_update(
                    lambda: self.lifx.set_color(selector, color="kelvin:4500", brightness=0.6, duration=2.0)
                )
                log.info("LIFX Restore: Standard Mode (4500k 60%)")
            
            if self.razer:
                self.razer.restore()
                
        except Exception as e:
            log.debug(f"LIFX restore failed: {e}")
    
    def stop(self):
        """Stop all active effects."""
        if self.razer:
            self.razer.stop_effect()

    def wave(self, color="cyan", period=2.5, brightness=0.6):
        if self.razer:
            self.razer.start_wave_effect(color, period, brightness)
        # LIFX: keep it calm
        self.breathe(color=color, cycles=0, period=max(1.5, period), peak=min(0.6, brightness))

    def rainbow_cycle(self, period=4.0, brightness=0.55):
        if self.razer:
            self.razer.start_rainbow_cycle(period, brightness)

    def lightning(self, base_color="purple"):
        if self.razer:
            self.razer.start_lightning_effect(base_color)

    def tension_pulse(self, get_tension, color="red", min_brightness=0.08, max_brightness=0.75, period=0.9):
        if self.razer:
            self.razer.start_tension_pulse(get_tension, color, min_brightness, max_brightness, period)

    def shutdown(self):
        """Shutdown the lights controller."""
        self._running = False
        if self._lifx_thread and self._lifx_thread.is_alive():
            self._lifx_thread.join(timeout=2.0)
        
        if self.razer:
            self.razer.close()
