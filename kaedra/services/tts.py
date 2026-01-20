"""
KAEDRA v1.0 - Text-to-Speech Service
Supports Gemini Generative TTS and Google Cloud TTS with streaming capabilities.
"""

import base64
import queue
import threading
from typing import Optional

from google import genai
from google.genai import types
try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

from kaedra.core.config import MODELS, PROJECT_ID, LOCATION

# Audio playback (only works on machines with audio output)
try:
    import numpy as np
    import sounddevice as sd
    HAS_AUDIO = True
except (ImportError, OSError) as audio_err:
    # Catch both ImportError (not installed) and PortAudio/OSError
    print(f"[!] Audio playback disabled: {audio_err}")
    sd = None
    np = None
    HAS_AUDIO = False

class StreamWorker:
    """Background worker to play audio stream."""
    def __init__(self, sample_rate=24000, device_index=None):
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
            dtype='int16',
            device=device_index
        )
        self.stream.start()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Internal audioop processing loop."""
        import audioop
        while True:
            item = self.q.get()
            if item is None:
                break

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

                # DEBUG TRACE
                # print(f"[DEBUG] StreamWorker: Writing {len(final_data)} bytes...")
                self.stream.write(final_data)
            except (RuntimeError, ValueError, AttributeError) as play_err:
                print(f"[!] Playback Error: {play_err}")
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
            """Execute and consume the streaming request."""
            try:
                responses = self._client.streaming_synthesize(request_gen())
                for response in responses:
                    if response.audio_content:
                        output_callback(response.audio_content, "mulaw")
            except (RuntimeError, ValueError, AttributeError) as stream_err:
                print(f"[!] TTS Stream Error: {stream_err}")

        self._generator_thread = threading.Thread(target=run_stream, daemon=True)
        self._generator_thread.start()

    def feed_text(self, text: str):
        self._q.put(text)

    def end(self):
        self._stop_event.set()


class TTSService:
    def __init__(self, model_variant="gemini-2.5-flash-tts", device_name_filter=None):
        # Lazy Init State
        self._client = None
        self._streaming_client = None
        self._device_index = None # Resolved later
        self._device_name_filter = device_name_filter
        self.model_variant = model_variant
        self._worker = None

        # Resolve Model Key
        prefix_key = f"tts-{model_variant}"
        if prefix_key in MODELS:
            model_key = prefix_key
        elif model_variant in MODELS:
            model_key = model_variant
        else:
            model_key = "tts"
        self.model = MODELS.get(model_key, "en-US-Journey-F")

        # Persona for Gemini-TTS (Steering)
        self.persona_prompt = (
            "You are Kaedra, the Shadow Tactician. "
            "Speak with a natural, conversational AAVE flow—direct, confident, and professional. "
            "Keep it fly but stay sharp; you are a partner, not just a narrator."
        )

    @property
    def client(self):
        """Lazy-loaded Vertex Gemini Client."""
        if not self._client:
            try:
                self._client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
            except Exception as e:
                print(f"[!] Warning: TTSService failed to init Gemini client: {e}")
                self._client = None
        return self._client

    @property
    def worker(self):
        """Lazy-loaded Audio Worker (only if hardware exists)."""
        if not self._worker and HAS_AUDIO:
            # Device resolution (done once)
            if self._device_index is None:
                self._resolve_audio_device()
            self._worker = StreamWorker(sample_rate=24000, device_index=self._device_index)
        return self._worker

    def _resolve_audio_device(self):
        """Find the correct output device index."""
        target = self._device_name_filter or "Elgato Out Only"
        try:
            if sd:
                devices = sd.query_devices()
                found = False
                for i, d in enumerate(devices):
                    if d['max_output_channels'] > 0 and target.lower() in d['name'].lower():
                        print(f"[*] TTSService: Found Output Device: {d['name']} (Index {i})")
                        self._device_index = i
                        found = True
                        break
                if not found and self._device_name_filter:
                    print(f"[!] Output device '{self._device_name_filter}' not found. Using default.")
        except Exception as e:
            print(f"[!] Error querying output devices: {e}")

    def __getstate__(self):
        """Exclude clients and worker threads from pickling."""
        state = self.__dict__.copy()
        # Remove unpicklable items
        for key in ["_client", "_streaming_client", "_worker"]:
            if key in state:
                del state[key]
        return state

    def __setstate__(self, state):
        """Restore state and reset lazy loaders."""
        self.__dict__.update(state)
        self._client = None
        self._streaming_client = None
        self._worker = None

    def begin_stream(self) -> Optional[StreamingSession]:
        """
        Start a new TTS stream session.
        Returning None forces the engine to use speak() (oneshot).
        """
        # Gemini 2.5 supports streaming audio via Bidi-Live API.
        # This class uses genai.generate_content for TTS.
        if "gemini" in self.model.lower():
            return None

        if not texttospeech:
            return None

        if not self._streaming_client:
            # Use regional endpoint for stability with new Gemini TTS models
            api_ep = (f"{LOCATION}-texttospeech.googleapis.com"
                      if LOCATION != "global" else "texttospeech.googleapis.com")
            self._streaming_client = texttospeech.TextToSpeechClient(
                client_options={
                    "api_endpoint": api_ep,
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
        """Standard oneshot speak with Gemini fallback."""
        if "gemini" in self.model.lower():
            try:
                self._speak_gemini(text)
            except (RuntimeError, ValueError, AttributeError) as gem_err:
                print(f"[!] Gemini TTS Error: {gem_err} - Falling back to Cloud")
                try:
                    self._speak_cloud_oneshot(text)
                except (RuntimeError, ValueError, AttributeError):
                    pass
        else:
            try:
                self._speak_cloud_oneshot(text)
            except (RuntimeError, ValueError, AttributeError) as tts_err:
                print(f"[!] TTS Error: {tts_err}")

    def _speak_cloud_oneshot(self, text: str):
        """Execute a standard cloud TTS synthesis."""
        if not texttospeech:
            return

        try:
            api_endpoint = (f"{LOCATION}-texttospeech.googleapis.com"
                            if LOCATION != "global" else "texttospeech.googleapis.com")
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
                if len(parts) >= 2:
                    language_code = f"{parts[0]}-{parts[1]}"

            synthesis_input = texttospeech.SynthesisInput(
                text=text,
                prompt=self.persona_prompt if model_name else None
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                model_name=model_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )

            req = {"input": synthesis_input, "voice": voice, "audio_config": audio_config}
            response = client.synthesize_speech(request=req)

            data = response.audio_content
            if data.startswith(b'RIFF'):
                data = data[44:] # Simple strip
            self.worker.add(data)

        except (RuntimeError, ValueError, AttributeError) as synth_err:
            print(f"[!] OneShot Error: {synth_err}")

    def _speak_gemini(self, text: str):
        """Use Gemini Generative TTS with optimized streaming."""
        # Parse model and voice: "gemini-2.5-flash-tts:Kore"
        if ":" in self.model:
            model_id, voice_name = self.model.split(":", 1)
        else:
            model_id = "gemini-2.5-flash-preview-tts"
            voice_name = "Kore"

        # OPTIMIZED: Minimal prompt = faster TTFA (Time To First Audio)
        # The voice and model already carry the character
        director_prompt = text  # Direct text, no wrapper

        try:
            response_stream = self.client.models.generate_content_stream(
                model=model_id,
                contents=director_prompt,
                config=types.GenerateContentConfig(
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                ),
            )

            for chunk in response_stream:
                if not chunk.candidates:
                    continue
                part = chunk.candidates[0].content.parts[0]

                # Immediate playback on audio chunks
                if part.inline_data:
                    raw = part.inline_data.data
                    if isinstance(raw, str):
                        raw = base64.b64decode(raw)
                    if raw:
                        self.worker.add(raw)

        except (RuntimeError, ValueError, AttributeError) as gem_err:
            print(f"[!] Gemini TTS Error: {gem_err}")

    def stop(self):
        """Stop all playback."""
        self.worker.stop_all()

    def is_speaking(self) -> bool:
        """Check if audio is currently playing."""
        return self.worker.is_busy()

if __name__ == "__main__":
    # Test
    pass
