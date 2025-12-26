import sounddevice as sd
import numpy as np
import logging
from typing import Generator, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class MicrophoneService:
    """
    Captures audio from the microphone.
    """
    def __init__(self, device_name_filter: str = "Chat Mix"):
        self.device_index = self._find_device(device_name_filter)
        self.sample_rate = 16000 # 16kHz is standard for speech models
        self.channels = 1
        self.dtype = 'int16'
        self.block_size = 1024

    def _find_device(self, name_filter: str) -> Optional[int]:
        """Finds a device index containing the name_filter."""
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0 and name_filter.lower() in device['name'].lower():
                    logger.info(f"[*] Found Microphone: {device['name']} (Index {i})")
                    print(f"[*] Found Microphone: {device['name']} (Index {i})")
                    return i
            
            logger.warning(f"[!] Device '{name_filter}' not found. Using default.")
            print(f"[!] Device '{name_filter}' not found. Using default.")
            return None # Default
        except Exception as e:
            logger.error(f"[!] Error querying devices: {e}")
            return None

    def listen_continuous(self) -> Generator[bytes, None, None]:
        """
        Yields raw audio chunks continuously.
        """
        q = []
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            q.append(indata.copy())

        try:
            with sd.InputStream(device=self.device_index,
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype=self.dtype,
                                blocksize=self.block_size,
                                callback=callback):
                print("[*] Microphone listening...")
                while True:
                    if q:
                        chunk = q.pop(0)
                        yield chunk.tobytes()
                    else:
                        sd.sleep(10) # Wait a bit to avoid busy loop
                        
        except Exception as e:
            logger.error(f"[!] Microphone error: {e}")
            raise e

    def record_seconds(self, duration: int = 5) -> bytes:
        """Record for a fixed duration."""
        print(f"[*] Recording for {duration} seconds...")
        recording = sd.rec(int(duration * self.sample_rate),
                           samplerate=self.sample_rate,
                           channels=self.channels,
                           device=self.device_index,
                           dtype=self.dtype)
        sd.wait()
        return recording.tobytes()

    def _calculate_rms(self, indata):
        """Calculate Root Mean Square amplitude."""
        # Cast to float to avoid integer overflow when squaring int16
        return np.sqrt(np.mean(indata.astype(float)**2))

    def get_current_rms(self) -> float:
        """Quick sample of current mic level for barge-in detection."""
        try:
            with sd.InputStream(device=self.device_index,
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                dtype=self.dtype,
                                blocksize=self.block_size) as stream:
                indata, _ = stream.read(self.block_size)
                return self._calculate_rms(indata)
        except:
            return 0.0

    def wait_for_speech(self, threshold: int = 300) -> bool:
        """
        Blocks until audio energy exceeds threshold.
        Returns True when speech triggers.
        """
        print(f"[*] Waiting for speech (Threshold: {threshold})...")
        with sd.InputStream(device=self.device_index,
                            samplerate=self.sample_rate,
                            channels=self.channels,
                            dtype=self.dtype,
                            blocksize=self.block_size) as stream:
            while True:
                indata, _ = stream.read(self.block_size)
                rms = self._calculate_rms(indata)
                if rms > threshold:
                    print(f"[*] Speech Detected! (RMS: {rms:.2f})")
                    return True

    def listen_until_silence(self, silence_threshold: int = 300, silence_duration: float = 1.5) -> bytes:
        """
        Records audio until silence is detected for `silence_duration` seconds.
        """
        print("[*] Recording... (Stop speaking to finish)")
        buffer = []
        silent_chunks = 0
        chunks_per_second = self.sample_rate / self.block_size
        max_silent_chunks = int(silence_duration * chunks_per_second)
        
        with sd.InputStream(device=self.device_index,
                            samplerate=self.sample_rate,
                            channels=self.channels,
                            dtype=self.dtype,
                            blocksize=self.block_size) as stream:
            while True:
                indata, _ = stream.read(self.block_size)
                buffer.append(indata.tobytes())
                
                rms = self._calculate_rms(indata)
                if rms < silence_threshold:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                
                if silent_chunks > max_silent_chunks:
                    print("[*] Silence detected. Stopping.")
                    break
        
        return b"".join(buffer)
