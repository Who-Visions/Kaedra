import argparse
import asyncio
import os
from google import genai
from google.genai import types

from kaedra.core.config import PROJECT_ID, LOCATION
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.agents.kaedra import KAEDRA_PROFILE

# Live API Model
LIVE_MODEL = "gemini-live-2.5-flash"

LIVE_SYSTEM_PROMPT = KAEDRA_PROFILE + """
[LIVE MODE]
- Real-time bidirectional voice conversation
- Brief, natural responses (1-3 sentences)
- Use turn-taking cues to know when to respond
- Can be interrupted naturally
- Remember conversation context automatically
"""


async def live_mode():
    """Kaedra with Gemini Live API - Full duplex streaming."""
    
    parser = argparse.ArgumentParser(description="Kaedra Live API Mode")
    parser.add_argument("--tts-voice", default="Kore", help="TTS voice name")
    args = parser.parse_args()
    
    print(f"[*] Initializing Kaedra LIVE API Mode (Project: {PROJECT_ID})")
    
    # Configure Live API client
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global"
    )
    
    # Live API configuration
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=args.tts_voice
                )
            )
        ),
        system_instruction=types.Content(
            parts=[types.Part(text=LIVE_SYSTEM_PROMPT)]
        )
    )
    
    print("\n" + "="*60)
    print("KAEDRA LIVE API MODE - NATIVE STREAMING")
    print(f"Voice: {args.tts_voice} | Barge-in: Enabled | Memory: Automatic")
    print("="*60 + "\n")
    
    try:
        # Connect to Live API
        async with client.aio.live.connect(
            model=LIVE_MODEL,
            config=config
        ) as session:
            
            print("[*] Connected to Gemini Live API")
            print("[*] Start speaking... (Ctrl+C to exit)")
            
            # TODO: Integrate mic capture → session.send()
            # TODO: Handle session.receive() → audio playback
            # This requires WebSocket-based audio streaming
            
            # Placeholder for full implementation
            print("[!] Full Live API integration coming soon")
            print("[!] Requires WebSocket audio streaming setup")
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Disconnecting from Live API...")


if __name__ == "__main__":
    asyncio.run(live_mode())
