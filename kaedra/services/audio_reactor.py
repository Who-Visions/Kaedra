try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except (ImportError, OSError):
    sd = None
    np = None
    HAS_AUDIO = False

import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioReactor:
    """
    Listens to a specific audio input (e.g. Wave Link Mix) and analyzes it for:
    - RMS Energy (Volume)
    - Bass/Kick detection (FFT)
    """

    def __init__(self, device_id: Optional[str | int] = "Elgato Out Only"):
        self.device_index = None
        if HAS_AUDIO:
            self.device_index = self._find_device(device_id)

        self.sample_rate = 44100 # Standard audio
        self.block_size = 2048   # Good for FFT resolution
        self.channels = 1        # Mono is enough for beat detection

        # Runtime (Not Pickled)
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # State
        self.energy = 0.0      # Smoothed RMS (0.0 - 1.0)
        self.bass_energy = 0.0 # Low freq energy
        self.is_beat = False   # True if beat detected in last frame

        # Config
        self.gain = 2.0        # Software gain
        self.smooth_factor = 0.8

    def __getstate__(self):
        state = self.__dict__.copy()
        # Exclude thread
        if "_thread" in state: del state["_thread"]
        state["running"] = False # Ensure it starts stopped in cloud
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Restore runtime defaults
        self._thread = None
        self.running = False

    def _find_device(self, target: Optional[str | int]) -> Optional[int]:
        if target is None: return None
        if isinstance(target, int): return target

        name_filter = str(target)
        try:
            devices = sd.query_devices()
            best_idx = None

            # 1. Try to find Specific Target (e.g. "Elgato Out Only")
            for i, device in enumerate(devices):
                if name_filter.lower() in device['name'].lower() and device['max_input_channels'] > 0:
                    return i

            # 2. Fallback: Search for any "Mix" or "Stream" input if target failed
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name']
                    if "Elgato" in name and ("Mix" in name or "Stream" in name or "Output" in name):
                        return i

            return None
        except Exception:
            return None

    @classmethod
    def list_devices(cls):
        """List all available audio input devices."""
        if not HAS_AUDIO: return []
        try:
            devices = sd.query_devices()
            inputs = []
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0:
                    inputs.append((i, d['name']))
            return inputs
        except Exception:
            return []

    def start(self):
        if not HAS_AUDIO:
            print("[!] AudioReactor: Audio unavailable (Cloud Mode)")
            return
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[*] Audio Reactor Service Started")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _listen_loop(self):
        if self.device_index is None:
            # Try to find again or default
            self.device_index = sd.default.device[0]

        try:
            with sd.InputStream(device=self.device_index,
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                blocksize=self.block_size,
                                callback=self._audio_callback):
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            print(f"[!] AudioReactor Stream Error: {e}")
            self.running = False

    def _audio_callback(self, indata, frames, time_info, status):
        # 1. Calculate RMS (Volume)
        # Cast to avoid overflow
        data = indata[:, 0].astype(np.float32)
        rms = np.sqrt(np.mean(data**2))

        # Normalize/Gain
        target_energy = np.clip(rms * self.gain, 0.0, 1.0)

        # Smooth
        self.energy = (self.energy * self.smooth_factor) + (target_energy * (1 - self.smooth_factor))

        # 2. Simple FFT for Bass (0-150Hz)
        fft_data = np.fft.rfft(data * np.hanning(len(data)))
        fft_mag = np.abs(fft_data)
        freqs = np.fft.rfftfreq(len(data), 1/self.sample_rate)

        # Bass range indices
        bass_mask = (freqs > 20) & (freqs < 150)
        current_bass = np.mean(fft_mag[bass_mask]) if np.any(bass_mask) else 0.0

        # Normalize bass (heuristic)
        current_bass = np.clip(current_bass / 50.0, 0.0, 1.0) # Adjust divisor based on testing

        # Beat detection (simple threshold on rise)
        self.is_beat = False
        if current_bass > 0.4 and current_bass > (self.bass_energy * 1.3):
            self.is_beat = True

        self.bass_energy = (self.bass_energy * 0.7) + (current_bass * 0.3)

    def get_status(self):
        return {
            "energy": self.energy,
            "bass": self.bass_energy,
            "beat": self.is_beat
        }

if __name__ == "__main__":
    # Test
    reactor = AudioReactor("Mix")
    reactor.start()
    try:
        while True:
            s = reactor.get_status()
            bar = "#" * int(s["energy"] * 50)
            beat = "BASS!" if s["bass"] > 0.4 else "     "
            print(f"\r[{beat}] Energy: {s['energy']:.2f} | Bass: {s['bass']:.2f} {bar}", end="")
            time.sleep(0.05)
    except KeyboardInterrupt:
        reactor.stop()
