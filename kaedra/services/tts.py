import os
import wave
import base64
import queue
import threading
import time
try:
    import winsound
except ImportError:
    winsound = None
from google import genai
from google.genai import types
from datetime import datetime
from pathlib import Path

from ..core.config import MODELS, PROJECT_ID, LOCATION

import io

class StreamWorker:
    """Background worker to play audio snippets sequentially."""
    def __init__(self):
        self.q = queue.Queue()
        self.playing = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def _run(self):
        while True:
            item = self.q.get()
            if item is None: break # Poison pill
            
            wav_data = item
            self.playing = True
            try:
                if winsound:
                    # SND_MEMORY plays from RAM. 
                    # Without SND_ASYNC, it blocks this thread until done. Perfect.
                    winsound.PlaySound(wav_data, winsound.SND_MEMORY)
                else:
                    # Linux fallback (print duration)
                    time.sleep(1) 
            except Exception as e:
                print(f"[!] Playback Error: {e}")
            finally:
                self.playing = False
                self.q.task_done()

    def add(self, wav_data: bytes):
        self.q.put(wav_data)
        
    def stop_all(self):
        """Stop current and clear queue."""
        # Clear queue
        with self.q.mutex:
            self.q.queue.clear()
        
        # Stop playing current sound
        if winsound:
            winsound.PlaySound(None, winsound.SND_PURGE)
        self.playing = False

    @property
    def is_busy(self) -> bool:
        """True if playing or has items in queue."""
        return self.playing or not self.q.empty()


class TTSService:
    def __init__(self, model_variant: str = "pro"):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        # Select model based on variant
        model_key = f"tts-{model_variant}" if f"tts-{model_variant}" in MODELS else "tts"
        self.model = MODELS.get(model_key, "gemini-2.5-pro-preview-tts")
        print(f"[*] TTSService initialized with model: {self.model}")
        self.voice_name = "Kore" # Firm/Professional voice
        
        self.worker = StreamWorker()
        
        # Ensure output directory exists (temp or cache)
        self.output_dir = Path(os.environ.get("TEMP", ".")) / "kaedra_tts"
        self.output_dir.mkdir(exist_ok=True)

    def speak(self, text: str):
        """Generate speech from text and queue it for playback."""
        try:
            # print(f"[*] Generating speech for: {text[:30]}...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name,
                            )
                        )
                    ),
                )
            )
            
            if not response.candidates: return

            part = response.candidates[0].content.parts[0]
            if not part.inline_data or not part.inline_data.data:
                return
            
            raw_data = part.inline_data.data
            
            # Handle both raw bytes and base64 encoded string
            if isinstance(raw_data, str):
                audio_bytes = base64.b64decode(raw_data)
            else:
                audio_bytes = raw_data
            
            # Create WAV in memory (Gemini returns PCM usually? Need to wrap)
            # Actually Gemini TTS returns encoded audio often? 
            # The previous code re-wrapped it in WAV at 24000Hz.
            # Assuming raw_data is PCM? 
            # Docs say: "Unary: LINEAR16 (default)".
            # So wrapping in WAV container is required for winsound.
            
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_bytes)
            
            wav_data = wav_buf.getvalue()
            
            # Queue for playback
            self.worker.add(wav_data)
            
        except Exception as e:
            print(f"[!] TTS Error: {e}")
            
    def stop(self):
        """Stop all playback."""
        self.worker.stop_all()

    def is_speaking(self) -> bool:
        return self.worker.is_busy

if __name__ == "__main__":
    tts = TTSService()
    tts.speak("Streaming test. Phase 1.")
    tts.speak("Phase 2 initiating.")
    import time
    while tts.is_speaking():
        time.sleep(0.1)
