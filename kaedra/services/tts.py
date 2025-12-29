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

# Audio playback (only works on machines with audio output)
try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except (ImportError, OSError) as e:
    # Catch both ImportError (not installed) and OSError (missing system, e.g. PortAudio)
    print(f"[!] Audio playback disabled: {e}")
    sd = None
    np = None
    HAS_AUDIO = False
    print("[!] Audio playback unavailable (sounddevice not installed or no audio device)")

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None
    print("[!] Warning: google-cloud-texttospeech not installed.")

class StreamWorker:
    """Background worker to play audio stream."""
    def __init__(self, sample_rate=24000):
        self.q = queue.Queue()
        self.playing = False
        self.sample_rate = sample_rate
        self.output_rate = 24000
        self.stream = None
        self._thread = None
        
        if not HAS_AUDIO:
            print("[!] StreamWorker: Audio disabled (no sounddevice)")
            return
            
        # For MULAW we need an 8kHz stream, or we decode to PWM.
        self.stream = sd.OutputStream(
            samplerate=self.output_rate,
            channels=1,
            dtype='int16'
        )
        self.stream.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def _run(self):
        import audioop
        while True:
            item = self.q.get()
            if item is None: break 
            
            data_bytes, audio_format = item
            self.playing = True
            try:
                if audio_format == "mulaw":
                    pcm_data = audioop.ulaw2lin(data_bytes, 2) # Decode 8-bit MULAW to 16-bit PCM
                    # Upsample from 8kHz to 24kHz
                    pcm_24k, _ = audioop.ratecv(pcm_data, 2, 1, 8000, 24000, None)
                    final_data = np.frombuffer(pcm_24k, dtype=np.int16)
                else:
                    # Assume LINEAR16 24kHz (Gemini/Cloud Oneshots)
                    final_data = np.frombuffer(data_bytes, dtype=np.int16)
                
                self.stream.write(final_data)
            except Exception as e:
                print(f"[!] Playback Error: {e}")
            finally:
                self.playing = False
                self.q.task_done()

    def add(self, pcm_data: bytes, audio_format: str = "linear16"):
        if pcm_data:
            self.q.put((pcm_data, audio_format))
        
    def stop_all(self):
        """Stop current and clear queue."""
        with self.q.mutex:
            self.q.queue.clear()
        # Sounddevice doesn't have an easy "flush" effectively without restarting,
        # but clearing the queue stops future chunks.
        self.playing = False

    def is_busy(self) -> bool:
        """True if playing or has items in queue."""
        return self.playing or not self.q.empty()


class StreamingSession:
    """Manages a single streaming session to Google Cloud TTS."""
    def __init__(self, client, config, persona_prompt=None):
        self._client = client
        self._config = config
        self._persona_prompt = persona_prompt
        self._q = queue.Queue()
        self._stop_event = threading.Event()
        self._generator_thread = None
        
    def start(self, output_callback):
        """Start the streaming request and feed output to callback."""
        def request_gen():
            # Initial config request
            yield texttospeech.StreamingSynthesizeRequest(streaming_config=self._config)
            
            first_chunk = True
            while not self._stop_event.is_set() or not self._q.empty():
                try:
                    text = self._q.get(timeout=0.1)
                    if text:
                        prompt = self._persona_prompt if first_chunk else None
                        
                        yield texttospeech.StreamingSynthesizeRequest(
                            input=texttospeech.StreamingSynthesisInput(
                                text=text,
                                prompt=prompt
                            )
                        )
                        first_chunk = False
                except queue.Empty:
                    continue
                    
        def run_stream():
            try:
                responses = self._client.streaming_synthesize(request_gen())
                for response in responses:
                     if response.audio_content:
                         output_callback(response.audio_content, "mulaw")
            except Exception as e:
                print(f"[!] TTS Stream Error: {e}")

        self._generator_thread = threading.Thread(target=run_stream, daemon=True)
        self._generator_thread.start()

    def feed_text(self, text: str):
        self._q.put(text)
        
    def end(self):
        self._stop_event.set()


class TTSService:
    def __init__(self, model_variant: str = "pro"):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        # Prioritize 'tts-' prefix to avoid collision with reasoning models
        prefix_key = f"tts-{model_variant}"
        if prefix_key in MODELS:
            model_key = prefix_key
        elif model_variant in MODELS:
            model_key = model_variant
        else:
            model_key = "tts"
        
        self.model = MODELS.get(model_key, "en-US-Journey-F")
        print(f"[*] TTSService initialized with model: {self.model}")
        
        # Persona for Gemini-TTS (Steering)
        self.persona_prompt = (
            "You are Kaedra, the Shadow Tactician. "
            "Speak with a natural, conversational AAVE flow—direct, confident, and professional. "
            "Keep it fly but stay sharp; you are a partner, not just a narrator."
        )
        
        self.worker = StreamWorker(sample_rate=24000)
        
        # Audio buffer for sentence assembly (fallback)
        self._streaming_client = None

    def begin_stream(self) -> StreamingSession:
        """Start a new TTS stream session."""
        # Gemini TTS is now supported in the streaming pathway
            
        try:
            from google.cloud import texttospeech
        except ImportError:
             return None
             
        if not self._streaming_client:
            # Use regional endpoint for stability with new Gemini TTS models
            api_endpoint = f"{LOCATION}-texttospeech.googleapis.com" if LOCATION != "global" else "texttospeech.googleapis.com"
            self._streaming_client = texttospeech.TextToSpeechClient(
                client_options={
                    "api_endpoint": api_endpoint,
                    "quota_project_id": PROJECT_ID
                }
            )

        # Parse voice details
        language_code = "en-US"
        voice_name = self.model
        model_name = None
        
        # Handle Gemini format "model:voice"
        if ":" in self.model:
            model_name, voice_name = self.model.split(":", 1)
        
        # Handle Chirp/Cloud naming specifically
        # (Assuming standard formats like en-US-Chirp3-HD-Kore)
        if "-" in voice_name and not model_name:
             parts = voice_name.split("-")
             if len(parts) >= 2: language_code = f"{parts[0]}-{parts[1]}"
        
        config = texttospeech.StreamingSynthesizeConfig(
            voice=texttospeech.VoiceSelectionParams(
                language_code=language_code, 
                name=voice_name,
                model_name=model_name
            ),
            streaming_audio_config=texttospeech.StreamingAudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MULAW, 
                sample_rate_hertz=8000
            ),
        )
        
        session = StreamingSession(self._streaming_client, config, persona_prompt=self.persona_prompt if model_name else None)
        session.start(self.worker.add)
        return session

    def speak(self, text: str):
        """Standard oneshot speak (Fallback to cloud oneshot)."""
        try:
            self._speak_cloud_oneshot(text)
        except Exception as e:
            print(f"[!] TTS Error: {e}")

    def _speak_cloud_oneshot(self, text: str):
         # Reuse stream session or separate method? 
         # Separate is safer for one-off calls outside the streaming loop.
        try:
            from google.cloud import texttospeech
            api_endpoint = f"{LOCATION}-texttospeech.googleapis.com" if LOCATION != "global" else "texttospeech.googleapis.com"
            client = texttospeech.TextToSpeechClient(
                client_options={
                    "api_endpoint": api_endpoint,
                    "quota_project_id": PROJECT_ID
                }
            )
            
            language_code = "en-US"
            voice_name = self.model
            model_name = None
            
            if ":" in self.model:
                model_name, voice_name = self.model.split(":", 1)
            
            if "-" in voice_name and not model_name:
                 parts = voice_name.split("-")
                 if len(parts) >= 2: language_code = f"{parts[0]}-{parts[1]}"

            synthesis_input = texttospeech.SynthesisInput(
                text=text,
                prompt=self.persona_prompt if model_name else None
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code, 
                name=voice_name,
                model_name=model_name
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

            response = client.synthesize_speech(
                request={"input": synthesis_input, "voice": voice, "audio_config": audio_config}
            )
            
            # Skip RIFF header (44 bytes) if we are just appending to a raw stream?
            # Sounddevice raw stream handles int16. WAV usually has header.
            # If we send Header to stream, it might sound like a "pop".
            # Better to strip header for raw playback if possible, or just play it.
            # The 'wav_data' logic in StreamWorker uses np.frombuffer.
            # Riff header is just metadata, might cause slight noise.
            data = response.audio_content
            if data.startswith(b'RIFF'):
                data = data[44:] # Simple strip
            self.worker.add(data)
            
        except Exception as e:
            print(f"[!] OneShot Error: {e}")

    def _speak_gemini(self, text: str):
        """Use Gemini Generative TTS."""
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
        if not part.inline_data: return
        
        raw = part.inline_data.data
        if isinstance(raw, str): raw = base64.b64decode(raw)
        self.worker.add(raw)

    def stop(self):
        """Stop all playback."""
        self.worker.stop_all()

    def is_speaking(self) -> bool:
        return self.worker.is_busy()

if __name__ == "__main__":
    # Test
    pass
