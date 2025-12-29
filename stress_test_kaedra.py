import asyncio
import time
import random
import statistics
import traceback
from datetime import datetime
from google import genai
from google.genai import types
from rich.console import Console
from rich.table import Table
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception

from kaedra.core.config import PROJECT_ID, MODELS
from kaedra.core.models import AudioConfig, SessionConfig
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
from kaedra.core.engine import ConversationManager, KaedraVoiceEngine

# Retry logic for 429s and transient errors
def is_429(exception):
    return "429" in str(exception)

@retry(
    wait=wait_exponential(multiplier=2, min=4, max=20),
    stop=stop_after_attempt(3),
    retry=retry_if_exception(is_429),
    reraise=True
)
async def send_message_with_retry(chat, message, config=None):
    return await chat.send_message_stream(message=message, config=config)

# Mock components for high-speed simulation
class MockMic:
    sample_rate = 16000
    device_index = 0
    def wait_for_speech(self, threshold): pass
    def listen_until_silence(self, threshold, duration): return b'\x00' * 32000
    def listen_continuous(self): yield b'\x00' * 8000
    def get_current_rms(self): return 0

class MockTTS:
    def is_speaking(self): return False
    def stop(self): pass
    def speak(self, text): pass
    def begin_stream(self): return MockTTSStream()

class MockTTSStream:
    def feed_text(self, text): pass
    def end(self): pass

class MockLIFX:
    def set_states(self, states): pass
    def set_state(self, **kwargs): pass

PROMPTS = [
    "Yo Kaedra, how you feelin' today?",
    "I need to verify a client named John Doe for a shoot tomorrow.",
    "Kaedra, check this contract for any hidden trap doors.",
    "Tell me about your ghost, do you really have one?",
    "Dave is stressin' out, Kaedra. You got any words of wisdom?",
    "Polygraph scan: is the following statement true: 'I am the best AI'?",
    "Stealth mode, blue lights only. We goin' dark.",
    "How much should I charge for a full day wedding shoot?",
    "Kaedra, analyze my existence for a second. Why are we even here?",
    "Crisis mode: a client just cancelled and wants a full refund on a non-refundable deposit."
]

async def run_stress_test(num_turns=100):
    console = Console()
    console.print(f"[bold magenta]🚀 Kaedra 100-Turn Stability & Latency Benchmark v2[/bold magenta]")
    console.print(f"[dim]Project: {PROJECT_ID} | Turns: {num_turns} | STT Model: 'base'[/dim]\n")
    
    session_config = SessionConfig(max_history_turns=50, tts_variant="flash-lite", thinking_level="LOW")
    audio_config = AudioConfig()
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    model_name = MODELS["flash"]
    
    conversation = ConversationManager(client, model_name, session_config, VOICE_SYSTEM_PROMPT)
    engine = KaedraVoiceEngine(
        mic=MockMic(), tts=MockTTS(), conversation=conversation,
        audio_config=audio_config, session_config=session_config,
        lifx=MockLIFX(), model_name=model_name
    )
    
    metrics = []
    table = Table(title=f"Live Turn Log", border_style="cyan")
    table.add_column("Turn", justify="right", style="dim")
    table.add_column("Phase", style="white")
    table.add_column("Lat (s)", justify="center")
    table.add_column("Status", justify="center")

    for i in range(1, num_turns + 1):
        prompt = random.choice(PROMPTS)
        t_start = time.time()
        
        try:
            # phase 1: Skill Selection
            skill_start = time.time()
            active_skill = await engine.skills.update_context(prompt)
            skill_lat = time.time() - skill_start
            
            # phase 2: Streaming Inference
            persona_reminder = f"[SKILL: {active_skill.name}]\n{engine.skills.get_skill_prompt()}\n[LOCAL_STT: \"{prompt}\"]"
            
            inf_start = time.time()
            first_token_time = 0.0
            response_text = ""
            
            # Watchdog for the stream loop
            try:
                async with asyncio.timeout(20): # 20s total turn timeout
                    stream = await send_message_with_retry(engine.conversation.chat, persona_reminder)
                    async for chunk in stream:
                        if not chunk.candidates: continue
                        if first_token_time == 0:
                            first_token_time = time.time() - inf_start
                        for part in chunk.candidates[0].content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
            except asyncio.TimeoutError:
                console.print(f"[bold red]Turn {i} TIMEOUT[/bold red]")
                continue

            turn_total = time.time() - t_start
            metrics.append({
                "ftl": first_token_time,
                "total": turn_total,
                "skill": skill_lat,
                "len": len(response_text)
            })

            # Real-time console update
            if i % 5 == 0 or i == 1:
                console.print(f"[Turn {i:3}] Skill: {active_skill.name:20} | FTL: {first_token_time:5.2f}s | Total: {turn_total:5.2f}s")
        
        except Exception as e:
            console.print(f"[bold red]Turn {i} FAILED:[/bold red] {e}")
            console.print(traceback.format_exc())
            if "429" in str(e):
                console.print("[bold red]Critical Rate Limit. Stopping.[/bold red]")
                break
            continue

    # Final Report
    if metrics:
        avg_ftl = statistics.mean([m["ftl"] for m in metrics])
        avg_total = statistics.mean([m["total"] for m in metrics])
        p95_total = statistics.quantiles([m["total"] for m in metrics], n=20)[18] 
        
        console.print(f"\n[bold green]Final Performance Report (n={len(metrics)})[/bold green]")
        console.print(f"• Avg FTL:    [cyan]{avg_ftl:.3f}s[/cyan]")
        console.print(f"• Avg Total:  [cyan]{avg_total:.3f}s[/cyan]")
        console.print(f"• P95 Latency:[cyan]{p95_total:.3f}s[/cyan]")
        
        if avg_total < 4.0:
            console.print("[bold green]✅ SYSTEM STATUS: OPTIMIZED[/bold green]")
        else:
            console.print("[bold yellow]⚠️ SYSTEM STATUS: CONGESTED[/bold yellow]")
    else:
        console.print("[bold red]No metrics collected.[/bold red]")

if __name__ == "__main__":
    asyncio.run(run_stress_test(100))
