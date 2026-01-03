#!/usr/bin/env python
"""
100-Turn TTS Refactor Stress Test
Measures latency with optimized TTS (no director prompt, minimal logging).
"""
import asyncio
import time
import statistics
from datetime import datetime
from google import genai
from google.genai import types
from rich.console import Console

from kaedra.core.config import PROJECT_ID, MODELS
from kaedra.core.models import SessionConfig
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
from kaedra.core.engine import ConversationManager
from kaedra.services.tts import TTSService

# Mixed prompts for realistic testing
PROMPTS = [
    "What time is it?",
    "Turn my lights off.",
    "Lights on.",
    "Give me a quick vibe check.",
    "Party mode.",
    "Dim the lights.",
    "What's good?",
    "How's my schedule?",
    "Tell me something motivational.",
    "What should I work on?",
    "Check my invoices.",
    "Weather in Miami?",
    "Give me a one liner.",
    "Chill vibes.",
    "Wake me up.",
    "What's the move?",
    "Run a truth scan.",
    "Tell me about Who Visions.",
    "Photography tips?",
    "End transmission.",
]

async def run_100_turn_test():
    console = Console()
    console.print(f"[bold magenta]🚀 100-Turn TTS Refactor Test[/bold magenta]")
    console.print(f"[dim]Measuring optimized TTS latency[/dim]\n")
    
    session_config = SessionConfig(max_history_turns=50, thinking_level="minimal")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    
    # TTS with Stealth 500X output
    tts = TTSService(model_variant="hifi-kore", device_name_filter="Stealth 500X")
    conversation = ConversationManager(client, "gemini-3-flash-preview", session_config, VOICE_SYSTEM_PROMPT)
    
    metrics = []
    
    for i in range(1, 101):
        prompt = PROMPTS[(i - 1) % len(PROMPTS)]
        
        t_start = time.time()
        
        try:
            import pytz
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern).strftime("%I:%M %p")
            
            message = f"[TIME: {current_time}]\n[STT: \"{prompt}\"]"
            
            # Get response
            inf_start = time.time()
            ftl = 0.0
            response_text = ""
            
            async with asyncio.timeout(15):
                active_chat = conversation.get_active_chat(prompt)
                stream = await active_chat.send_message_stream(message=message)
                async for chunk in stream:
                    if not chunk.candidates: continue
                    if ftl == 0:
                        ftl = time.time() - inf_start
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            # TTS (limit to 150 chars for speed)
            tts_text = response_text[:150]
            tts_start = time.time()
            tts.speak(tts_text)
            tts_time = time.time() - tts_start
            
            total = time.time() - t_start
            
            metrics.append({"ftl": ftl, "tts": tts_time, "total": total})
            
            if i % 10 == 0:
                console.print(f"[cyan]Turn {i:3}:[/cyan] FTL {ftl:.2f}s | TTS {tts_time:.2f}s | Total {total:.2f}s")
            
        except asyncio.TimeoutError:
            console.print(f"[red]Turn {i}: TIMEOUT[/red]")
        except Exception as e:
            console.print(f"[red]Turn {i}: {e}[/red]")
            
        await asyncio.sleep(0.3)
    
    # Final Report
    if metrics:
        avg_ftl = statistics.mean([m["ftl"] for m in metrics])
        avg_tts = statistics.mean([m["tts"] for m in metrics])
        avg_total = statistics.mean([m["total"] for m in metrics])
        p50 = sorted([m["total"] for m in metrics])[len(metrics)//2]
        p95 = sorted([m["total"] for m in metrics])[int(len(metrics) * 0.95)]
        
        console.print(f"\n[bold green]═══ 100-TURN FINAL REPORT ═══[/bold green]")
        console.print(f"• Avg FTL:    {avg_ftl:.3f}s")
        console.print(f"• Avg TTS:    {avg_tts:.3f}s")
        console.print(f"• Avg Total:  {avg_total:.3f}s")
        console.print(f"• P50:        {p50:.3f}s")
        console.print(f"• P95:        {p95:.3f}s")
        
        if avg_total < 3.0:
            console.print("[bold green]✅ STATUS: FAST[/bold green]")
        elif avg_total < 5.0:
            console.print("[bold yellow]⚠️ STATUS: ACCEPTABLE[/bold yellow]")
        else:
            console.print("[bold red]❌ STATUS: NEEDS WORK[/bold red]")

if __name__ == "__main__":
    asyncio.run(run_100_turn_test())
