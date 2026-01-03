#!/usr/bin/env python
"""
30-Turn LIVE Audio Latency Test
Injects text directly and measures full TTS pipeline.
"""
import asyncio
import time
import random
import statistics
from datetime import datetime
from google import genai
from google.genai import types
from rich.console import Console

from kaedra.core.config import PROJECT_ID, MODELS
from kaedra.core.models import AudioConfig, SessionConfig
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
from kaedra.core.engine import ConversationManager
from kaedra.services.tts import TTSService
from kaedra.services.lifx import LIFXService

PROMPTS = [
    "Yo Kaedra, what time is it?",
    "Turn my lights off.",
    "What's the weather in Miami right now?",
    "Give me a quick vibe check.",
    "Run a truth scan on me.",
    "Tell me something motivational.",
    "What should I work on today?",
    "Lights on, full brightness.",
    "Party mode, let's go!",
    "How do I close more photography clients?",
    "What's my schedule looking like?",
    "Give me a one liner.",
    "Set the mood, dim lights.",
    "What are you thinking about?",
    "Tell me about Who Visions.",
    "Break down my day for me.",
    "What's good fam?",
    "I need energy, pump me up!",
    "Chill vibes only right now.",
    "What's the move?",
    "Give me some wisdom.",
    "Check my invoices.",
    "How's my cash flow?",
    "Turn the lights blue.",
    "Red alert mode!",
    "Everything off, going to sleep.",
    "Wake up call!",
    "What's trending today?",
    "Summarize my goals.",
    "End transmission.",
]

async def run_live_test(num_turns=30):
    console = Console()
    console.print(f"[bold magenta]🎤 30-Turn LIVE Audio Latency Test[/bold magenta]")
    console.print(f"[dim]Measuring full TTS pipeline latency[/dim]\n")
    
    session_config = SessionConfig(max_history_turns=50, tts_variant="hifi-kore", thinking_level="LOW")
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    model_name = MODELS["flash"]  # Using Flash for speed
    
    # Real TTS Service
    tts = TTSService(model_variant="hifi-kore", device_name_filter="Webcam 4")
    
    conversation = ConversationManager(client, model_name, session_config, VOICE_SYSTEM_PROMPT)
    
    metrics = []
    
    for i in range(1, num_turns + 1):
        prompt = PROMPTS[(i - 1) % len(PROMPTS)]
        console.print(f"[cyan]Turn {i:2}:[/cyan] {prompt[:50]}...")
        
        t_start = time.time()
        
        try:
            # Inject real-time context
            import pytz
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern).strftime("%I:%M %p on %A, %B %d, %Y")
            
            persona_reminder = f"[CURRENT TIME: {current_time} (Eastern)]\n[LOCAL_STT: \"{prompt}\"]"
            
            # Measure First Token Latency
            inf_start = time.time()
            first_token_time = 0.0
            response_text = ""
            
            async with asyncio.timeout(15):
                stream = await conversation.chat.send_message_stream(message=persona_reminder)
                async for chunk in stream:
                    if not chunk.candidates: continue
                    if first_token_time == 0:
                        first_token_time = time.time() - inf_start
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            # Measure TTS latency
            tts_start = time.time()
            tts.speak(response_text[:200])  # Limit to 200 chars for speed
            tts_time = time.time() - tts_start
            
            turn_total = time.time() - t_start
            
            metrics.append({
                "ftl": first_token_time,
                "tts": tts_time,
                "total": turn_total,
                "len": len(response_text)
            })
            
            console.print(f"  [green]FTL: {first_token_time:.2f}s | TTS: {tts_time:.2f}s | Total: {turn_total:.2f}s[/green]")
            
        except asyncio.TimeoutError:
            console.print(f"  [red]TIMEOUT[/red]")
            continue
        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/red]")
            continue
            
        await asyncio.sleep(0.5)  # Brief pause between turns
    
    # Final Report
    if metrics:
        avg_ftl = statistics.mean([m["ftl"] for m in metrics])
        avg_tts = statistics.mean([m["tts"] for m in metrics])
        avg_total = statistics.mean([m["total"] for m in metrics])
        p95_total = sorted([m["total"] for m in metrics])[int(len(metrics) * 0.95)] if len(metrics) >= 20 else max(m["total"] for m in metrics)
        
        console.print(f"\n[bold green]═══ FINAL PERFORMANCE REPORT (n={len(metrics)}) ═══[/bold green]")
        console.print(f"[cyan]• Avg First Token:  {avg_ftl:.3f}s[/cyan]")
        console.print(f"[cyan]• Avg TTS Start:    {avg_tts:.3f}s[/cyan]")
        console.print(f"[cyan]• Avg Total Turn:   {avg_total:.3f}s[/cyan]")
        console.print(f"[cyan]• P95 Latency:      {p95_total:.3f}s[/cyan]")
        
        if avg_total < 3.0:
            console.print("[bold green]✅ STATUS: FAST[/bold green]")
        elif avg_total < 5.0:
            console.print("[bold yellow]⚠️ STATUS: ACCEPTABLE[/bold yellow]")
        else:
            console.print("[bold red]❌ STATUS: TOO SLOW[/bold red]")

if __name__ == "__main__":
    asyncio.run(run_live_test(30))
