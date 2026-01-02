
import asyncio
import os
from rich.console import Console

# Import the Engine (imports must be fixed now)
from auto_flow import UnifiedFlowEngine, main as real_main

console = Console()

async def mock_20_turns():
    """
    Start the engine, then inject 20 mock inputs to verify stability.
    """
    console.print("[bold green]Starting 20-Turn Stress Test[/bold green]")
    
    # Run the main setup to get the engine
    # Since main() runs forever, we need to extract the setup part or subclass.
    # Let's subclass to mock the run loop.
    
    class MockEngine(UnifiedFlowEngine):
        async def run_test(self):
            console.print("[cyan]Engine Initialized. Starting Mock Injection...[/cyan]")
            
            # Start background services (fake start)
            # self.start_flow() 
            # We don't want real audio/websocket for this stress test of the *Logic*
            # but user might want to test the connection too.
            # Let's assume we test the Logic Pipeline first (process_input).
            
            self.dashboard.set_status("TEST MODE", "magenta")
            
            for i in range(1, 21):
                text = f"This is test turn number {i}. Just confirming the system is stable."
                console.print(f"\n[bold yellow]--- Turn {i}/20 ---[/bold yellow]")
                console.print(f"Injecting: '{text}'")
                
                # Directly process (simulating queue get)
                try:
                    await self.process_input(text)
                    console.print(f"[green]Turn {i} Complete[/green]")
                except Exception as e:
                    console.print(f"[bold red]Turn {i} FAILED: {e}[/bold red]")
                    return
                
                await asyncio.sleep(0.5) # Slight breathing room
                
            console.print("\n[bold green]SUCCESS: 20 Turns Completed with no crash.[/bold green]")

    # Setup (Copied from auto_flow.py main)
    # ... ignoring deps ...
    # Actually, simpler: just run the script and let it fail if imports are bad.
    # But to inject turns we need the object.
    
    # We will assume if this script IMPORTS correctly, 50% of the battle is won.
    # Then we instantiate and run.
    
    from google import genai
    from kaedra.services.mic import MicrophoneService
    from kaedra.services.tts import TTSService
    from kaedra.services.lifx import LIFXService
    from kaedra.core.engine import ConversationManager
    from kaedra.core.models import AudioConfig, SessionConfig, SessionState
    from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
    from dotenv import load_dotenv
    
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1alpha'})
    
    # Mock Hardware
    mic = MicrophoneService()
    # Mock TTS to silence it
    class MockTTS:
        def speak(self, text): pass
        async def speak_stream(self, iterator):
            async for chunk in iterator: pass
        def begin_stream(self): pass
        @property
        def is_speaking(self):
            return False
                
    tts = MockTTS()
    
    # Mock LIFX safely
    class MockLIFX:
        def turn_on(self): pass
        def turn_off(self): pass
        def set_color(self, *args): pass
        def set_brightness(self, *args): pass
        def dim(self, *args): pass
        def party_mode(self): pass
    lifx = MockLIFX()
    
    # Mock Conversation Manager to avoid hitting real Gemini API (Speed up test)
    class MockConversationManager:
        def __init__(self, *args, **kwargs):
            self.history = []
        async def _stream_generator(self):
            # Mock Response Object
            class MockPart:
                def __init__(self, text): self.text = text
                @property
                def thought(self): return None

            class MockContent:
                def __init__(self, text): self.parts = [MockPart(text)]

            class MockCandidate:
                def __init__(self, text): self.content = MockContent(text)

            class MockChunk:
                def __init__(self, text): self.candidates = [MockCandidate(text)]

            # Simulate a stream generator
            words = ["Copy ", "that, ", "Dave. ", "System ", "is ", "stable. ", "Turn ", "complete."]
            for w in words:
                yield MockChunk(w)
                await asyncio.sleep(0.01)

        async def send_message_stream(self, message=None, config=None, **kwargs):
             return self._stream_generator()

        async def update_context(self, text):
            # Return dummy skill
            class MockSkill:
                name = "General"
            return MockSkill()
        async def prune_history(self):
            pass
        def save_transcript(self):
            pass
        def get_active_chat(self, text):
            # Return self because we implement send_message_stream
            return self
        
    # Replace the real one
    convo = MockConversationManager()
    
    engine = MockEngine(
        mic=mic,
        tts=tts,
        conversation=convo,
        audio_config=AudioConfig(),
        session_config=SessionConfig(),
        lifx=lifx,
        model_name="gemini-3-flash-preview",
        stt_model="distil-small.en"
    )
    
    await engine.run_test()

if __name__ == "__main__":
    asyncio.run(mock_20_turns())
