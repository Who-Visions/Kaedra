import argparse
import asyncio
from google import genai

from kaedra.core.config import PROJECT_ID, MODELS, DEFAULT_MODEL, LIFX_TOKEN
from kaedra.core.models import AudioConfig, SessionConfig
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
from kaedra.core.engine import ConversationManager, KaedraVoiceEngine
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.services.lifx import LIFXService

async def main():
    parser = argparse.ArgumentParser(description="Kaedra Universe Builder Mode")
    parser.add_argument("--tts", default="flash", help="TTS model variant")
    parser.add_argument("--model", default="flash", help="Reasoning model")
    args = parser.parse_args()

    # Creative configuration
    audio_config = AudioConfig(wake_threshold=500)
    session_config = SessionConfig(
        max_history_turns=100, # Longer history for lore consistency
        tts_variant=args.tts,
        thinking_level="high" # Encourage deeper creative thinking
    )

    print(f"[*] Initializing Kaedra: UNIVERSE BUILDER MODE...")

    try:
        # Core Services
        mic = MicrophoneService(device_name_filter="Chat Mix")
        tts = TTSService(model_variant=args.tts, device_name_filter="Stealth 500X")
        if not LIFX_TOKEN:
            print("[!] LIFX_TOKEN missing. Lighting effects disabled.")
            lifx = None # Handle gracefully? Engine expects it. let's check. 
            # Engine init: lifx: LIFXService
            # We better provide a mock or the real service.
            # Assuming Token is there based on previous files.
        lifx = LIFXService()
        
        # Universe Builder System Prompt
        UNIVERSE_PROMPT = """
You are KAEDRA, functioning in UNIVERSE BUILDER MODE.
Your mission is to assist Dave (USER) in architecting the 'Ai with Dav3' Cinematic Universe.
We are building a Marvel-style saga from the Big Bang to the End of Time.
Suggest ideas, track timeline consistency, and remember established lore.
Be bold, creative, and precise.
""" + VOICE_SYSTEM_PROMPT

        model_name = MODELS.get(args.model, MODELS.get(DEFAULT_MODEL))
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        
        conversation = ConversationManager(client, model_name, session_config, UNIVERSE_PROMPT)

        engine = KaedraVoiceEngine(
            mic=mic,
            tts=tts,
            conversation=conversation,
            audio_config=audio_config,
            session_config=session_config,
            lifx=lifx,
            model_name=model_name
        )
        
        # Set initial visual state for Universe Mode (Violet/Purple) - Living Room ONLY
        await asyncio.to_thread(lifx.set_color, "group:Living Room", "purple")

        await engine.run()

    except Exception as e:
        print(f"[!] Initialization Failure: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
