"""
StoryEngine LIFX Integration
Rate limiting, deduplication, and light control.
"""
import time
import random
import queue
import threading
from typing import Callable, Optional

from kaedra.core.config import LIFX_TOKEN
from kaedra.services.lifx import LIFXService

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
    
    def __init__(self):
        self.lifx: Optional[LIFXService] = None
        self.gate = LifxGate()
        self._lifx_q: queue.Queue = queue.Queue(maxsize=1)
        self._lifx_thread: Optional[threading.Thread] = None
        self._initial_state: Optional[dict] = None
        self._running = False
        self.pulse_count = 0
        
    def init(self) -> bool:
        """Initialize LIFX with connection status."""
        if not LIFX_TOKEN:
            log.warning("LIFX_TOKEN not set - lights disabled")
            return False
            
        try:
            self.lifx = LIFXService()
            lights = self.lifx.list_lights()
            if not lights:
                log.warning("LIFX: No lights found")
                return False
                
            # Save initial state for restore (LightState is a dataclass, not dict)
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
    
    def set_color(self, hue: float, saturation: float, brightness: float, kelvin: int = 3500):
        """Set light color (non-blocking)."""
        if not self.lifx:
            return
            
        sig = f"color:{hue:.0f}:{saturation:.2f}:{brightness:.2f}"
        
        def do_set():
            self.gate.call(
                lambda: self.lifx.set_color(hue, saturation, brightness, kelvin),
                sig=sig
            )
        
        self.request_update(do_set)
    
    def breathe(self, color: str = "red", cycles: int = 1, period: float = 2.0):
        """Trigger breathe effect (non-blocking)."""
        if not self.lifx:
            return
            
        def do_breathe():
            self.gate.call(
                lambda: self.lifx.breathe(color=color, cycles=cycles, period=period),
                sig=f"breathe:{color}"
            )
        
        self.request_update(do_breathe)
    
    def restore(self):
        """Restore lights to initial state."""
        if not self.lifx or not self._initial_state:
            return
            
        try:
            color = self._initial_state.get("color", {})
            if color:
                self.lifx.set_color(
                    hue=color.get("hue", 0),
                    saturation=color.get("saturation", 0),
                    brightness=self._initial_state.get("brightness", 1.0),
                    kelvin=color.get("kelvin", 3500)
                )
        except Exception as e:
            log.debug(f"LIFX restore failed: {e}")
    
    def shutdown(self):
        """Shutdown the lights controller."""
        self._running = False
        if self._lifx_thread and self._lifx_thread.is_alive():
            self._lifx_thread.join(timeout=2.0)
