"""
Audio Service v2.0
Handles Text-to-Speech (Gemini 2.5 TTS) and Speech-to-Text (Faster Whisper / Gemini).
Updated to Gemini 2.5 TTS API per official documentation.
"""
import wave
import logging
from pathlib import Path
from typing import Optional, Union, BinaryIO, List, Dict

# Config
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Local STT
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# VOICE REGISTRY (All 30 Gemini TTS Voices)
# ══════════════════════════════════════════════════════════════════════════════

VOICES = {
    # Primary Voices
    "Zephyr": "Bright",
    "Puck": "Upbeat",
    "Charon": "Informative",
    "Kore": "Firm",
    "Fenrir": "Excitable",
    "Leda": "Youthful",
    "Orus": "Firm",
    "Aoede": "Breezy",
    "Callirrhoe": "Easy-going",
    "Autonoe": "Bright",
    "Enceladus": "Breathy",
    "Iapetus": "Clear",
    "Umbriel": "Easy-going",
    "Algieba": "Smooth",
    "Despina": "Smooth",
    "Erinome": "Clear",
    "Algenib": "Gravelly",
    "Rasalgethi": "Informative",
    "Laomedeia": "Upbeat",
    "Achernar": "Soft",
    "Alnilam": "Firm",
    "Schedar": "Even",
    "Gacrux": "Mature",
    "Pulcherrima": "Forward",
    "Achird": "Friendly",
    "Zubenelgenubi": "Casual",
    "Vindemiatrix": "Gentle",
    "Sadachbia": "Lively",
    "Sadaltager": "Knowledgeable",
    "Sulafat": "Warm",
}

# Default TTS Model
TTS_MODEL_FLASH = "gemini-2.5-flash-preview-tts"
TTS_MODEL_PRO = "gemini-2.5-pro-preview-tts"


def save_wave_file(filename: str, pcm_data: bytes, channels: int = 1, rate: int = 24000, sample_width: int = 2):
    """Save PCM audio data to a wave file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


class AudioService:
    def __init__(self):
        # 1. Initialize Gemini Client (TTS & Cloud STT) - Lazy
        self._client = None

        # 2. Whisper (Local STT) - Lazy
        self._whisper = None

    @property
    def client(self):
        if not self._client:
            from kaedra.core.config import get_gemini_client
            try:
                self._client = get_gemini_client()
            except Exception as e:
                print(f"[!] AudioService GenAI Init Failed: {e}")
                self._client = None
        return self._client

    def __getstate__(self):
        state = self.__dict__.copy()
        if "_client" in state: del state["_client"]
        if "_whisper" in state: del state["_whisper"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._client = None
        self._whisper = None

    def _get_whisper(self):
        if not self._whisper and WhisperModel:
            print("[INFO] Loading Whisper Model (base.en) on GPU...")
            try:
                self._whisper = WhisperModel("base.en", device="cuda", compute_type="float16")
            except Exception:
                print("[INFO] Whisper GPU failed. Falling back to CPU (int8)...")
                self._whisper = WhisperModel("base.en", device="cpu", compute_type="int8")
        return self._whisper

    def text_to_speech(
        self,
        text: str,
        voice: str = "Kore",
        output_path: str = "output.wav",
        pro: bool = False
    ) -> Optional[str]:
        """
        Generate single-speaker speech from text using Gemini 2.5 TTS.

        Args:
            text: The text to speak. Can include style prompts like "Say cheerfully: ..."
            voice: Voice name from VOICES dict (default: Kore)
            output_path: Where to save the .wav file
            pro: Use Pro model (higher quality) vs Flash (faster)

        Returns:
            Path to saved audio file, or None on failure.
        """
        if not self.client:
            print("[ERROR] TTS Unavailable: Gemini Client not initialized.")
            return None

        model = TTS_MODEL_PRO if pro else TTS_MODEL_FLASH

        print(f"[TTS] Generating ({len(text)} chars | Voice: {voice} | Model: {model.split('-')[-1]})...")
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    )
                )
            )

            # Extract audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data

            # Save as wave file
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            save_wave_file(str(path), audio_data)

            print(f"[TTS] Saved: {path}")
            return str(path)

        except Exception as e:
            print(f"[ERROR] TTS Error: {e}")
            return None

    def text_to_speech_multi(
        self,
        text: str,
        speakers: List[Dict[str, str]],
        output_path: str = "output.wav",
        pro: bool = False
    ) -> Optional[str]:
        """
        Generate multi-speaker audio (up to 2 speakers) using Gemini 2.5 TTS.

        Args:
            text: Transcript with speaker names, e.g.:
                  "Joe: How's it going?
                   Jane: Pretty good!"
            speakers: List of speaker configs, e.g.:
                      [{"name": "Joe", "voice": "Kore"}, {"name": "Jane", "voice": "Puck"}]
            output_path: Where to save the .wav file
            pro: Use Pro model vs Flash

        Returns:
            Path to saved audio file, or None on failure.
        """
        if not self.client:
            print("[ERROR] TTS Unavailable: Gemini Client not initialized.")
            return None

        if len(speakers) > 2:
            print("[WARN] Gemini TTS supports max 2 speakers. Using first 2.")
            speakers = speakers[:2]

        model = TTS_MODEL_PRO if pro else TTS_MODEL_FLASH

        # Build speaker configs
        speaker_configs = []
        for s in speakers:
            speaker_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=s["name"],
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=s.get("voice", "Kore")
                        )
                    )
                )
            )

        print(f"[TTS] Generating Multi-Speaker ({len(speakers)} speakers)...")
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs
                        )
                    )
                )
            )

            # Extract audio data
            audio_data = response.candidates[0].content.parts[0].inline_data.data

            # Save as wave file
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            save_wave_file(str(path), audio_data)

            print(f"[TTS] Multi-Speaker Saved: {path}")
            return str(path)

        except Exception as e:
            print(f"[ERROR] Multi-TTS Error: {e}")
            return None

    def speech_to_text(self, audio_source: Union[str, BinaryIO], local: bool = True) -> str:
        """
        Transcribe audio.
        local=True: Uses Faster Whisper (Free, Local, Fast)
        local=False: Uses Gemini 3 Multimodal (High Accuracy, Context aware)
        """
        if local:
            model = self._get_whisper()
            if not model:
                return "[Error: Faster Whisper not installed/loaded]"

            segments, info = model.transcribe(audio_source, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        else:
            # Cloud STT via Gemini Multimodal
            if not self.client:
                return "[Error: Cloud STT unavailable - no Gemini client]"

            try:
                # Read audio file
                if isinstance(audio_source, str):
                    audio_path = Path(audio_source)
                    if not audio_path.exists():
                        return f"[Error: File not found: {audio_source}]"
                    audio_bytes = audio_path.read_bytes()
                    # Detect mime type
                    ext = audio_path.suffix.lower()
                    mime_map = {
                        ".wav": "audio/wav",
                        ".mp3": "audio/mp3",
                        ".aiff": "audio/aiff",
                        ".aac": "audio/aac",
                        ".ogg": "audio/ogg",
                        ".flac": "audio/flac",
                    }
                    mime_type = mime_map.get(ext, "audio/wav")
                else:
                    audio_bytes = audio_source.read()
                    mime_type = "audio/wav"

                print(f"[STT] Transcribing via Gemini ({len(audio_bytes)} bytes)...")

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        "Generate a precise transcript of the speech in this audio.",
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                    ]
                )

                return response.text.strip() if response.text else "[No transcript generated]"

            except Exception as e:
                return f"[Error: Cloud STT failed: {e}]"

    def list_voices(self) -> Dict[str, str]:
        """Return all available TTS voices with their style descriptors."""
        return VOICES
