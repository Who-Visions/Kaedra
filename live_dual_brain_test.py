#!/usr/bin/env python
"""
LIVE Audio Dual-Brain Test
Uses tiered prompts to test Flash (fast) vs Pro (deep thinking)
Outputs real TTS audio so you can hear Kaedra respond.
"""
import asyncio
import time
import random
from datetime import datetime
from google import genai
from google.genai import types
from rich.console import Console

from kaedra.core.config import PROJECT_ID, MODELS
from kaedra.core.models import AudioConfig, SessionConfig
from kaedra.core.prompts import VOICE_SYSTEM_PROMPT
from kaedra.core.engine import ConversationManager
from kaedra.services.tts import TTSService

# Tiered prompts: 1-15 (Flash), 16+ (Pro)
FLASH_PROMPTS = [
    # 1-5: Basic
    "What time is it right now?",
    "Turn my lights off.",
    "Give me a quick vibe check.",
    "What's the weather in Miami?",
    "Party mode, let's go!",
    # 6-10: Light reasoning
    "Is 7429 a prime number? Quick answer.",
    "Summarize Cinderella in 3 sentences.",
    "What's cloud computing? Keep it brief.",
    "Give me 3 photography tips for golden hour.",
    "What should I work on today?",
    # 11-15: Moderate
    "Explain what a variable is to a 10-year-old.",
    "Plan a 2-hour photo walk in Brooklyn.",
    "Give me 5 risks of launching an AI chat app.",
    "Write a one-line slogan for a streetwear hoodie.",
    "Generate 3 synthetic user messages for a portfolio site.",
]

PRO_PROMPTS = [
    # 16-20: Coding & deeper reasoning
    "Analyze this business model: AI voice assistant for photographers. What are the risks?",
    "Design an architecture for a multi-tenant SaaS on Vertex AI. Keep it under 200 words.",
    "Act as a strategy consultant. Give me a 6-month roadmap for an AI photography tool.",
    "Self-critique: How should I decide between Gemini 3 Pro and Flash for coding workloads?",
    "Design an agent that uses Google Search and Code Execution to fix failing CI tests.",
]

async def run_live_audio_test(num_turns=15):
    console = Console()
    console.print(f"[bold magenta]🎤 LIVE Audio Dual-Brain Test[/bold magenta]")
    console.print(f"[dim]Flash (minimal) for simple | Pro (high) for complex[/dim]\n")
    
    session_config = SessionConfig(max_history_turns=50, thinking_level="minimal")
    
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    
    # Real TTS Service
    tts = TTSService(model_variant="hifi-kore", device_name_filter="Webcam 4")
    
    conversation = ConversationManager(client, "gemini-3-flash-preview", session_config, VOICE_SYSTEM_PROMPT)
    
    metrics = {"flash": [], "pro": []}
    
    # Interleave prompts: mostly Flash, some Pro
    all_prompts = []
    for i, p in enumerate(FLASH_PROMPTS[:num_turns]):
        all_prompts.append(("flash", p))
        if i % 4 == 3 and PRO_PROMPTS:  # Every 4th prompt, add a Pro prompt
            all_prompts.append(("pro", PRO_PROMPTS.pop(0)))
    
    for i, (brain_type, prompt) in enumerate(all_prompts, 1):
        console.print(f"\n[cyan]═══ Turn {i} ({brain_type.upper()}) ═══[/cyan]")
        console.print(f"[dim]{prompt[:60]}...[/dim]")
        
        t_start = time.time()
        
        try:
            # Inject real-time context
            import pytz
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern).strftime("%I:%M %p on %A, %B %d, %Y")
            
            persona_reminder = f"[CURRENT TIME: {current_time} (Eastern)]\n[LOCAL_STT: \"{prompt}\"]"
            
            # Get appropriate brain
            active_chat = conversation.get_active_chat(prompt)
            
            # Measure First Token Latency
            inf_start = time.time()
            first_token_time = 0.0
            response_text = ""
            
            async with asyncio.timeout(30):  # Longer timeout for Pro
                stream = await active_chat.send_message_stream(message=persona_reminder)
                async for chunk in stream:
                    if not chunk.candidates: continue
                    if first_token_time == 0:
                        first_token_time = time.time() - inf_start
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
            
            # TTS Output (limit to 300 chars for speed)
            tts_text = response_text[:300] if len(response_text) > 300 else response_text
            console.print(f"[green]Kaedra: {tts_text[:100]}...[/green]")
            
            tts_start = time.time()
            tts.speak(tts_text)
            tts_time = time.time() - tts_start
            
            turn_total = time.time() - t_start
            
            metrics[brain_type].append({
                "ftl": first_token_time,
                "tts": tts_time,
                "total": turn_total
            })
            
            console.print(f"[yellow]FTL: {first_token_time:.2f}s | TTS: {tts_time:.2f}s | Total: {turn_total:.2f}s[/yellow]")
            
        except asyncio.TimeoutError:
            console.print(f"[red]TIMEOUT[/red]")
        except Exception as e:
            console.print(f"[red]ERROR: {e}[/red]")
            
        await asyncio.sleep(1)  # Pause between turns
    
    # Final Report
    console.print(f"\n[bold green]═══ FINAL PERFORMANCE REPORT ═══[/bold green]")
    
    for brain in ["flash", "pro"]:
        if metrics[brain]:
            import statistics
            avg_ftl = statistics.mean([m["ftl"] for m in metrics[brain]])
            avg_total = statistics.mean([m["total"] for m in metrics[brain]])
            console.print(f"\n[cyan]{brain.upper()} Brain (n={len(metrics[brain])}):[/cyan]")
            console.print(f"  Avg FTL:   {avg_ftl:.3f}s")
            console.print(f"  Avg Total: {avg_total:.3f}s")

if __name__ == "__main__":
    asyncio.run(run_live_audio_test(15))
