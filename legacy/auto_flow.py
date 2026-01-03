#!/usr/bin/env python
"""
KAEDRA AUTO FLOW (Unified Engine)
Integrates FastFlowService directly into the main AI pipeline.
Removes need for manual Wispr activation keys.
Audio -> FastFlow (Stream) -> Committed Text -> Kaedra AI -> Response
"""
import asyncio
import queue
import time
import sounddevice as sd
from typing import Optional
from rich.console import Console

# Import Core Engine and Services
from kaedra.core.engine import KaedraVoiceEngine
from kaedra.services.fast_flow import FastFlowService
try:
    from kaedra.services.wispr_cloud import WisprCloudService
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
# Import Desktop Service
from kaedra.services.wispr import WisprService

from kaedra.core.models import AudioConfig, SessionConfig, SessionState
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT

# Setup Imports
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.services.lifx import LIFXService
from kaedra.core.engine import ConversationManager
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
console = Console()

# Config
FAST_FLOW_MODEL = "distil-small.en"
USE_CLOUD_FLOW = False  # Keep disabled
USE_WISPR_DESKTOP = True # Enable Local DB Sync (Free)

class UnifiedFlowEngine(KaedraVoiceEngine):
    """
    Subclass of KaedraVoiceEngine that replaces the standard microphone loop
    with the streaming FastFlowService (or Wispr Cloud).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if USE_WISPR_DESKTOP:
            self.mode = "DESKTOP"
            # In Desktop mode, we poll the DB. No wake word required for auto-flow.
            self.service = WisprService(wake_word_required=False, callback=self._on_desktop_input)
            self.dashboard.console.print(f"[bold cyan]KAEDRA AUTO FLOW (DESKTOP)[/bold cyan] | Source: Wispr Flow App (SQLite)")
        elif USE_CLOUD_FLOW and CLOUD_AVAILABLE:
            self.mode = "CLOUD"
            self.service = WisprCloudService()
            self.dashboard.console.print(f"[bold cyan]KAEDRA AUTO FLOW (CLOUD)[/bold cyan] | Service: Wispr Flow API")
        else:
            self.mode = "LOCAL"
            self.service = FastFlowService(model_size=FAST_FLOW_MODEL, debug=False)
            self.dashboard.console.print(f"[bold cyan]KAEDRA AUTO FLOW (LOCAL)[/bold cyan] | Model: {FAST_FLOW_MODEL}")

        self.input_queue = asyncio.Queue()
        
    async def start_flow(self):
        """Start the background transcription service"""
        # Determine strict callback mapping
        kwargs = {
            "on_commit": self._on_commit,
            "on_partial": self._on_partial
        }
        
        # Check if start is async (Wispr) or Sync (FastFlow)
        if asyncio.iscoroutinefunction(self.service.start):
             await self.service.start(**kwargs)
        else:
             self.service.start(**kwargs)

    def _audio_callback(self, indata, frames, time, status):
        """Feed audio to Service"""
        if status:
            print(f"Audio Status: {status}")
        self.service.add_audio(indata.copy())

    def _on_commit(self, text):
        """Callback from FastFlow when text is stable"""
        # Push to async queue for the main loop to pick up
        self.input_queue.put_nowait(text)
        
    async def _on_desktop_input(self, text):
        """Callback from Wispr Desktop Service"""
        # Immediate Feedback for User
        console.print(f"\n[bold cyan][Wispr Input]:[/bold cyan] {text}")
        self.input_queue.put_nowait(text)

    def _on_partial(self, text):
        """Update dashboard with partials"""
        # Truncate for display if too long
        display_text = text[-80:] if len(text) > 80 else text
        self.dashboard.set_status(f"Listening: {display_text}", "green")

    async def run(self):
        """Overridden Run Loop"""
        print(f"[UnifiedFlowEngine] Starting {self.mode} Stream...")
        
        # Start Service (Polling or Stream)
        await self.start_flow()
        
        # Decide if we need Microphone Stream (Local/Cloud) or just Wait (Desktop)
        if self.mode == "DESKTOP":
            # No Mic needed - Wispr App handles audio
            self.dashboard.set_status(f"Ready ({self.mode})", "green")
            await self._process_loop()
        else:
            # Mic needed for Local/Cloud
            stream = sd.InputStream(
                device=1, 
                samplerate=16000,
                channels=1,
                dtype='float32',
                callback=self._audio_callback,
                blocksize=4096
            )
            with stream:
                self.dashboard.set_status(f"Ready ({self.mode})", "green")
                await self._process_loop()

    async def _process_loop(self):
        """Common Processing Loop"""
        try:
            while not self._should_stop:
                # BLOCKING WAIT for COMMITTED text
                text = await self.input_queue.get()
                
                if text:
                    self.stats.total_turns += 1
                    self.state = SessionState.PROCESSING
                    self.dashboard.set_status("Processing...", "yellow")
                    
                    await self.process_input(text)
                    
                    self.stats.successful_turns += 1
                    await self.conversation.prune_history()
                    self.conversation.save_transcript()
                    
                    self.state = SessionState.IDLE
                    self.dashboard.set_status("Listening...", "green")
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            console.print(f"[red]Error in AutoFlow Loop: {e}[red]")
        finally:
            if asyncio.iscoroutinefunction(self.service.stop):
                await self.service.stop()
            else:
                self.service.stop()
            await self._shutdown()

async def main():
    # 1. Load Keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("Error: GEMINI_API_KEY not found in .env")
        return

    # 2. Setup Services
    client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1alpha'})
    
    # Safe LIFX Init
    try:
        lifx = LIFXService()
    except ValueError:
        print("[Warn] LIFX_TOKEN not found. Using Mock LIFX Service.")
        class MockLIFX:
            def turn_on(self): pass
            def turn_off(self): pass
            def set_color(self, *args): pass
            def set_brightness(self, *args): pass
            def dim(self, *args): pass
            def party_mode(self): pass
        lifx = MockLIFX()
    
    # Configs
    audio_cfg = AudioConfig()
    session_cfg = SessionConfig()
    
    # Hardware
    mic = MicrophoneService() # Not used for listening, but needed for init
    
    # FIX: Correct Argument 'model_variant' and use generic 'flash' to let config.py handle resolution
    # or use "en-US-Journey-F" / "en-US-Studio-O" directly if using Cloud TTS.
    # The user wants NO deprecated models. 
    # If TTS service uses 'en-US-Journey-F' by default, that is safe.
    tts = TTSService(model_variant="flash") 
    
    # Conversation
    # FIX: Use VOICE_SYSTEM_PROMPT, not KAEDRA_PROFILE
    convo = ConversationManager(client, "gemini-3-flash-preview", session_cfg, VOICE_SYSTEM_PROMPT)
    
    # 3. Initialize Unified Engine
    engine = UnifiedFlowEngine(
        mic=mic,
        tts=tts,
        conversation=convo,
        audio_config=audio_cfg,
        session_config=session_cfg,
        lifx=lifx,
        model_name="gemini-3-flash-preview",
        stt_model="distil-small.en" # Redundant as we use FastFlowService internally
    )
    
    # 4. Run
    await engine.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye.")
