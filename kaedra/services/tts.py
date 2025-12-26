import os
import wave
import base64
import winsound
from google import genai
from google.genai import types
from datetime import datetime
from pathlib import Path

from ..core.config import MODELS, PROJECT_ID, LOCATION

class TTSService:
    def __init__(self, model_variant: str = "pro"):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        # Select model based on variant
        model_key = f"tts-{model_variant}" if f"tts-{model_variant}" in MODELS else "tts"
        self.model = MODELS.get(model_key, "gemini-2.5-pro-preview-tts")
        print(f"[*] TTSService initialized with model: {self.model}")
        self.voice_name = "Kore" # Firm/Professional voice
        
        # Ensure output directory exists (temp or cache)
        self.output_dir = Path(os.environ.get("TEMP", ".")) / "kaedra_tts"
        self.output_dir.mkdir(exist_ok=True)

    def speak(self, text: str):
        """Generate speech from text and play it immediately."""
        try:
            print(f"[*] Generating speech for: {text[:50]}...")
            
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
            
            # Extract audio data
            # Data is base64 encoded string in inline_data.data
            if not response.candidates:
                print("[!] No TTS candidates returned.")
                return

            part = response.candidates[0].content.parts[0]
            if not part.inline_data or not part.inline_data.data:
                print("[!] No audio data found in response.")
                return
            
            raw_data = part.inline_data.data
            print(f"[*] Received audio data: type={type(raw_data).__name__}, len={len(raw_data) if raw_data else 0}")
            
            # Handle both raw bytes and base64 encoded string
            if isinstance(raw_data, str):
                audio_bytes = base64.b64decode(raw_data)
            else:
                audio_bytes = raw_data  # Already bytes
            
            print(f"[*] Decoded audio size: {len(audio_bytes)} bytes")
            
            # Save to temporary WAV file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"response_{timestamp}.wav"
            
            with wave.open(str(filename), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_bytes)
                
            # Play audio
            print(f"[*] Playing audio: {filename}")
            winsound.PlaySound(str(filename), winsound.SND_FILENAME | winsound.SND_ASYNC)
            
        except Exception as e:
            print(f"[!] TTS Error: {e}")

if __name__ == "__main__":
    tts = TTSService()
    tts.speak("Systems online. Kaedra is listening.")
