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
    parser = argparse.ArgumentParser(description="Kaedra Voice Engine v2.3 (Modular)")
    parser.add_argument("--tts", default="flash", help="TTS model variant (e.g. flash, chirp-kore)")
    parser.add_argument("--model", default="flash", help="Reasoning model (flash, pro, ultra)")
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--wake-threshold", type=int, default=500)
    parser.add_argument("--thinking", type=str, default=None, help="Thinking level override")
    parser.add_argument("--mic", type=str, default="Chat Mix", help="Mic name filter")
    parser.add_argument("--out", type=str, default="Stealth 500X", help="Speaker name filter")
    parser.add_argument("--stt", type=str, default="base.en", help="STT Model size (base.en, distil-large-v3)")
    args = parser.parse_args()

    audio_config = AudioConfig(wake_threshold=args.wake_threshold)
    session_config = SessionConfig(
        max_history_turns=args.max_turns,
        tts_variant=args.tts,
        thinking_level=args.thinking
    )

    print(f"[*] Initializing Kaedra (Modular Engine)...")

    try:
        # Core Services (Mandatory)
        mic = MicrophoneService(device_name_filter=args.mic)
        # Increase default threshold if no arg provided, or trust args.
        # User config is audio_config passed to engine.
        # Let's verify Engine's audio_config usage.
        # Actually, let's just make the CLI default higher in listen_and_speak.py logic too.
        # But for now, let's fix the ENGINE to be safer.
        pass # Placeholder, will edit listen_and_speak.py directly.
        tts = TTSService(model_variant=args.tts, device_name_filter=args.out)
        
        # LIFX is now a core tool, not optional
        if not LIFX_TOKEN:
            print("[!] CRITICAL: LIFX_TOKEN is missing. LIFX is a core tool and must be configured.")
            # We'll initialize it to raise the ValueError if token is empty
        lifx = LIFXService()
        print(f"[💡] LIFX Core Service active")

        model_name = MODELS.get(args.model, MODELS.get(DEFAULT_MODEL))
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        
        conversation = ConversationManager(client, model_name, session_config, VOICE_SYSTEM_PROMPT)

        engine = KaedraVoiceEngine(
            mic=mic,
            tts=tts,
            conversation=conversation,
            audio_config=audio_config,
            session_config=session_config,
            lifx=lifx, # Passed as mandatory
            model_name=model_name,
            stt_model=args.stt
        )

        await engine.run()

    except Exception as e:
        print(f"[!] Initialization Failure: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
