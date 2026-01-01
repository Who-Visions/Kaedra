import asyncio
import time
import sys
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.services.transcription import TranscriptionService

async def watchdog_session():
    print("--- AUDIO WATCHDOG TEST ---")
    print("[1/5] Initializing Services...")
    try:
        mic = MicrophoneService(device_name_filter="Chat Mix")  # Default to what we found
        stt = TranscriptionService(model_size="base.en")
        tts = TTSService(model_variant="flash")
        print("[OK] Services Initialized.")
    except Exception as e:
        print(f"[FAIL] Init Error: {e}")
        return

    print("[2/5] Starting 5-minute Monitor (Press Ctrl+C to stop)...")
    end_time = time.time() + 300  # 5 minutes
    
    while time.time() < end_time:
        remaining = int(end_time - time.time())
        print(f"\n[TIME LEFT: {remaining}s] Listening...")
        
        try:
            # Record for 3 seconds of silence or speech? 
            # Let's use wait_for_speech logic to be efficient, then record.
            if mic.wait_for_speech(threshold=400):
                # Speech detected, record 4 seconds
                audio_data = mic.record_seconds(4)
                
                # Check RMS
                import numpy as np
                arr = np.frombuffer(audio_data, dtype=np.int16)
                rms = np.sqrt(np.mean(arr.astype(float)**2))
                print(f"[INPUT] Speech captured. RMS: {rms:.2f}")

                # Transcribe
                text = stt.transcribe(audio_data)
                print(f"[STT] Transcribed: '{text}'")

                if text:
                    # TTS Response
                    response = f"Success. I heard: {text}"
                    print(f"[TTS] Speaking: '{response}'")
                    tts.speak(response)
                    # Wait for playback roughly
                    time.sleep(3)
                else:
                    print("[WARN] Ignored empty transcription (or hallucination).")
            
        except Exception as e:
            print(f"[ERROR] Loop Error: {e}")
            time.sleep(1)
            
    print("--- 5 MINUTE TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(watchdog_session())
