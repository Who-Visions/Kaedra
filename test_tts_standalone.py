from kaedra.services.tts import TTSService
import time

def test_tts():
    print("[*] Initializing TTS Service...")
    tts = TTSService()
    
    elemental_message = "Systems online. Monitoring transcript stream."
    print(f"[*] Speaking: '{elemental_message}'")
    tts.speak(elemental_message)
    
    # Wait for audio to play
    time.sleep(5)

if __name__ == "__main__":
    test_tts()
