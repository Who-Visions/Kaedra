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
    def __init__(self):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        self.model = MODELS.get('tts', "gemini-2.5-flash-preview-tts")
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
                
            audio_bytes = base64.b64decode(part.inline_data.data)
            
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
