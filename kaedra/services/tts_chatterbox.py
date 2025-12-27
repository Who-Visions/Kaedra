"""
Chatterbox TTS Service for Kaedra Voice Engine.
Local GPU-accelerated TTS with voice cloning and paralinguistic tags.
"""

import re
import numpy as np
import threading
import queue
from pathlib import Path
from typing import Optional

import sounddevice as sd

try:
    import torch
    import torchaudio as ta
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    CHATTERBOX_AVAILABLE = True
except ImportError as e:
    CHATTERBOX_AVAILABLE = False
    print(f"[!] Chatterbox not available: {e}")


class StreamWorker:
    """Background worker to play audio stream."""
    def __init__(self, sample_rate: int = 24000):
        self.q = queue.Queue()
        self.playing = False
        self.sample_rate = sample_rate
        self._stop_flag = threading.Event()
        self.stream = sd.OutputStream(
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        self.stream.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def _run(self):
        while True:
            try:
                item = self.q.get(timeout=0.1)
                if item is None:
                    break
                
                self.playing = True
                self._stop_flag.clear()
                
                # Chunk playback for responsive stopping
                chunk_size = self.sample_rate // 10  # 100ms chunks
                for i in range(0, len(item), chunk_size):
                    if self._stop_flag.is_set():
                        break
                    chunk = item[i:i + chunk_size]
                    self.stream.write(chunk)
                
                self.playing = False
                self.q.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[!] Playback Error: {e}")
                self.playing = False

    def add(self, audio_data: np.ndarray):
        """Add audio to playback queue."""
        if audio_data is not None and len(audio_data) > 0:
            # Ensure float32 format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            self.q.put(audio_data)
        
    def stop_all(self):
        """Stop current playback and clear queue."""
        self._stop_flag.set()
        with self.q.mutex:
            self.q.queue.clear()
        self.playing = False

    def is_busy(self) -> bool:
        """True if playing or has items in queue."""
        return self.playing or not self.q.empty()


class ChatterboxTTSService:
    """
    Chatterbox Turbo TTS Service (Optimized).
    """
    
    def __init__(self, 
                 reference_audio: Optional[str] = None,
                 device: str = "cuda",
                 use_compile: bool = True):
        """
        Initialize Chatterbox TTS.
        """
        if not CHATTERBOX_AVAILABLE:
            raise RuntimeError("Chatterbox TTS not installed.")
        
        print(f"[*] Loading Chatterbox Turbo on {device}...")
        self.model = ChatterboxTurboTTS.from_pretrained(device=device)
        self.reference_audio = reference_audio
        self.device = device
        
        # Performance Upgrade: One-time conditioning
        if reference_audio and Path(reference_audio).exists():
            print(f"[*] Pre-conditioning voice reference: {reference_audio}")
            self.model.prepare_conditionals(reference_audio)
            self.reference_audio = None # Set to None so .generate() uses cached conds
        
        # Performance Upgrade: torch.compile (Inference Boost)
        if use_compile and device == "cuda":
            print("[*] Compiling model for speed (this takes a minute on first run)...")
            try:
                # Compile the main components
                self.model.t3 = torch.compile(self.model.t3, mode="reduce-overhead")
                self.model.s3gen = torch.compile(self.model.s3gen, mode="reduce-overhead")
                print("[*] Model compilation complete.")
            except Exception as e:
                print(f"[!] Compilation failed (skipping): {e}")

        # Initialize audio worker
        self.worker = StreamWorker(sample_rate=self.model.sr)
        print(f"[*] ChatterboxTTSService ready (SR: {self.model.sr})")
    
    def speak(self, text: str, blocking: bool = False):
        """
        Generate and play speech using sentence-level streaming.
        """
        try:
            # Performance Upgrade: Sentence-level streaming
            # Split by punctuation but keep the punctuation attached
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                
                # Generate audio for this sentence
                # Using cached conditioning (audio_prompt_path=None)
                wav = self.model.generate(
                    sentence, 
                    audio_prompt_path=None
                )
                
                # Convert to numpy
                if isinstance(wav, torch.Tensor):
                    audio_np = wav.squeeze().cpu().numpy()
                else:
                    audio_np = np.array(wav).squeeze()
                
                # Immediately push to playback queue while next sentence generates
                self.worker.add(audio_np)
            
            if blocking:
                self.worker.q.join()
                
        except Exception as e:
            print(f"[!] TTS Error: {e}")
    
    def stop(self):
        """Stop all playback immediately."""
        self.worker.stop_all()
    
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self.worker.is_busy()


def create_tts_service(backend: str = "chatterbox", **kwargs):
    """
    Factory function to create TTS service.
    
    Args:
        backend: "chatterbox" or "cloud" (Google Cloud TTS)
        **kwargs: Backend-specific arguments
        
    Returns:
        TTS service instance
    """
    if backend == "chatterbox":
        return ChatterboxTTSService(**kwargs)
    else:
        from .tts import TTSService
        return TTSService(**kwargs)


if __name__ == "__main__":
    # Quick test
    print("[*] Testing Chatterbox TTS...")
    tts = ChatterboxTTSService()
    tts.speak("Aight bet [chuckle], Kaedra online and locked in. What we working on today fam?", blocking=True)
    print("[*] Test complete!")
