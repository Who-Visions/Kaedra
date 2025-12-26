import asyncio
import os
import io
import wave
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from kaedra.core.config import PROJECT_ID, LOCATION
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService

# Configuration
MODEL_NAME = "gemini-2.5-flash-preview"

def create_wav_buffer(audio_data, sample_rate=16000):
    """Wraps raw PCM audio in a WAV container for Gemini."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2) # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)
    return buf.getvalue()

async def main():
    print(f"[*] Initializing Kaedra Live Listen (Project: {PROJECT_ID})...")
    
    # Init Services
    try:
        mic = MicrophoneService(device_name_filter="Chat Mix")  # Specifically requested
        tts = TTSService()
        
        # Init Model
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel(MODEL_NAME)
        
    except Exception as e:
        print(f"[!] Initialization failed: {e}")
        return

    print("\n" + "="*50)
    print("KAEDRA LIVE MODE - Press Ctrl+C to stop")
    print(f"Using Microphone: Index {mic.device_index}")
    print("="*50 + "\n")

    try:
        while True:
            # 1. Listen
            print("\n[User] Listening (5s)... GO!")
            audio_data = mic.record_seconds(5)
            wav_data = create_wav_buffer(audio_data, mic.sample_rate)
            print("[User] Processing...")

            # 2. Think (Gemini)
            print(f"[Kaedra] Thinking ({MODEL_NAME})...")
            response = await model.generate_content_async(
                [
                    Part.from_data(wav_data, mime_type="audio/wav"),
                    "Listen to this audio and respond concisely to the user. Be helpful and tactical."
                ]
            )
            
            reply_text = response.text
            print(f"[Kaedra] {reply_text}")

            # 3. Speak
            print("[Kaedra] Speaking...")
            # Run in executor to avoid blocking loop if TTS was blocking
            await asyncio.to_thread(tts.speak, reply_text)
            
    except KeyboardInterrupt:
        print("\n[*] Stopping...")

if __name__ == "__main__":
    asyncio.run(main())
