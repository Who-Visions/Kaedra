"""
Kaedra Voice Engine with Chatterbox TTS (Streaming Edition)
Streams conversation using local Chatterbox TTS with sentence-level buffering.
"""

# -----------------------------------------------------------------------------
# TQDM SUPPRESSION (Must be first)
# -----------------------------------------------------------------------------
import sys
import os

# Disable progress bars via Env Vars
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
import argparse
import asyncio
import io
import wave
import time
import re
import logging
import msvcrt  # Windows non-blocking input
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, AsyncGenerator
from enum import Enum

import numpy as np
import sounddevice as sd
import torch

from google import genai
from google.genai import types

from kaedra.core.config import PROJECT_ID
from kaedra.services.mic import MicrophoneService
from kaedra.services.memory import MemoryService
from kaedra.services.wispr import WisprService
from kaedra.agents.kaedra import KAEDRA_PROFILE
from kaedra.services.tts import StreamWorker  # Reusing existing worker

# Chatterbox TTS - HF_TOKEN must be set externally (do not hardcode!)
if not os.getenv('HF_TOKEN'):
    raise EnvironmentError("HF_TOKEN environment variable required for Chatterbox TTS")
from chatterbox.tts_turbo import ChatterboxTurboTTS

# Optional STT for RAG
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.align import Align
from rich import box

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

MODEL_NAME = "gemini-3-flash-preview"
SAMPLE_RATE = 24000
SENTENCE_ENDINGS = re.compile(r'(?<=[.?!])\s+')

VOICE_SYSTEM_PROMPT = """YOU ARE KAEDRA.
MANDATORY PERSONA:
- You are KAEDRA, the Shadow Tactician.
- Speak with AAVE flows. Vocabulary: "aight", "bet", "fam", "locked in".
- Tone: Natural, confident, sharp.
- START EVERY RESPONSE WITH A 1-WORD ACKNOWLEDGEMENT (e.g. "Bet.", "Say less.", "Got it.") to speed up audio.
- Keep responses CONCISE (1-3 sentences).
""" + KAEDRA_PROFILE

class SessionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class ChatterboxGenerator:
    """Handles TTS generation with optimizations for speed."""
    
    def __init__(self, reference_audio: Optional[str] = None, device: str = "cuda", use_compile: bool = True):
        self.console = Console()
        with self.console.status("[bold green]Loading Chatterbox Model...", spinner="dots"):
            self.model = ChatterboxTurboTTS.from_pretrained(device=device)
        
        self.sr = self.model.sr
        self.reference_audio = reference_audio
        
        # Performance Upgrade: One-time voice conditioning
        if reference_audio and Path(reference_audio).exists():
            with self.console.status(f"[bold blue]Conditioning voice reference: {Path(reference_audio).name}...", spinner="bouncingBar"):
                self.model.prepare_conditionals(reference_audio)
                self.reference_audio = None # Cached in model.conds now
        
        # Performance Upgrade: torch.compile (2-4x Speedup)
        if use_compile and device == "cuda":
            with self.console.status("[bold green]Compiling model for speed (approx 60s for RTX 2080 Super)...", spinner="aesthetic"):
                try:
                    self.model.t3 = torch.compile(self.model.t3, mode="reduce-overhead")
                    self.model.s3gen = torch.compile(self.model.s3gen, mode="reduce-overhead")
                    self.console.print("[green]✓[/green] Model Compilation Complete")
                except Exception as e:
                    self.console.print(f"[yellow]![/yellow] Compilation skipped: {e}")

        self.console.print(f"[green]✓[/green] Chatterbox Ready (SR: {self.sr})")
        
        # Warmup (Crucial for compiled models)
        try:
            self.console.print("[dim]Doing warmup inference...[/dim]")
            self.model.generate("Warmup.")
        except:
            pass
    
    def generate(self, text: str) -> Optional[np.ndarray]:
        """Generate audio for text using optimized settings."""
        try:
            text = text.strip()
            if not text:
                return None
                
            # Use cached conditionals
            wav = self.model.generate(
                text, 
                audio_prompt_path=None
            )
            
            # Move to CPU numpy
            audio = wav.squeeze(0).cpu().numpy()
            
            # VRAM Cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return audio
            
        except Exception as e:
            logging.error(f"TTS Generation Error: {e}")
            return None


class KaedraDashboard:
    """Console Dashboard"""
    def __init__(self):
        self.console = Console()
        self.status = "INITIALIZING"
        self.mic_status = "OFF"
        self.last_latency = 0.0
    
    def update(self, status: str, color: str = "white"):
        self.status = f"[{color}]{status}[/{color}]"
    
    def print_user(self, text: str):
        self.console.print(f"[bold cyan]You:[/bold cyan] {text}")
    
    def print_kaedra(self, text: str):
        self.console.print(f"[bold magenta]Kaedra:[/bold magenta] {text}")
            
    def generate_view(self) -> Panel:
        stats = f"Status: {self.status} | Mic: {self.mic_status} | Latency: {self.last_latency:.2f}s"
        return Panel(Align.center(stats), style="blue", box=box.ROUNDED, title="Kaedra + Chatterbox (Streaming)")


class ChatterboxVoiceEngine:
    def __init__(self, mic: MicrophoneService, tts: ChatterboxGenerator, client: genai.Client):
        self.mic = mic
        self.tts = tts
        self.client = client
        self.dashboard = KaedraDashboard()
        
        self.player = StreamWorker(sample_rate=tts.sr)
        # Worker starts automatically on init
        
        # Initialize Memory
        try:
            self.dashboard.console.print("[dim]Connecting to Memory Bank...[/dim]")
            self.memory = MemoryService()
            self.dashboard.console.print("[green]✓[/green] Memory Online")
        except Exception as e:
            logging.error(f"Memory Init Failed: {e}")
            self.memory = None

        # Define Tools
        def search_memory(query: str) -> str:
            """Search the persistent memory bank for historical context, Wispr Flow transcripts, or billing reports."""
            self.dashboard.console.print(f"[bold blue]🔎 Memory Search: {query}[/bold blue]")
            if not self.memory:
                return "Memory bank is currently offline."
            # Use recall method from MemoryService
            results = self.memory.recall(query)
            if not results:
                return f"No results found in memory for: {query}"
            
            summary = "\n".join([f"- [{m.get('timestamp', 'unknown')}] {m.get('content', '')}" for m in results])
            self.dashboard.console.print(f"[green]✓ Found {len(results)} memories[/green]")
            return f"FOUND MEMORIES for '{query}':\n{summary}"

        tools = [
            types.Tool(google_search=types.GoogleSearch()),
            search_memory
        ]
        
        # Initialize STT (for RAG)
        self.stt = None
        if HAS_WHISPER:
            try:
                self.dashboard.console.print("[dim]Loading Whisper STT (GPU Mode)...[/dim]")
                # GPU mode enabled after CUDA 12 reboot
                self.stt = WhisperModel("base.en", device="cuda", compute_type="float16")
                self.dashboard.console.print("[green]✓[/green] Whisper Online")
            except Exception as e:
                logging.error(f"STT Init Failed: {e}")
        
        self.tools_dict = {
            "search_memory": search_memory
        }

        self.chat = client.aio.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=VOICE_SYSTEM_PROMPT + "\n\nYou have access to a 'search_memory' tool. Use it to check for Wispr Flow transcripts or billing reports. You are automatically synced with these sources.",
                temperature=1.0,  # Gemini 3 recommendation - do not change
                thinking_config=types.ThinkingConfig(thinking_level="low"),  # Fast responses for chat
                tools=tools
            )
        )
        
        self.audio_level_threshold = 500  # Initial VAD threshold
        
        self._should_stop = False
        self.wake_threshold = 500
        self.silence_threshold = 700 
        self.silence_duration = 1.2 # Breathing room for deep flow
        
        # Wispr Service
        self.wispr = WisprService()
        self._wispr_task = None

    async def run(self):
        logging.info("Engine started")
        self.dashboard.console.print("[bold green]Kaedra Streaming Engine Online[/bold green]")
        self.dashboard.console.print("[dim]Press Ctrl+C to exit[/dim]")
        
        with Live(self.dashboard.generate_view(), refresh_per_second=4, console=self.dashboard.console) as live:
            self.live = live
            self.dashboard.update("Ready", "green")
            live.update(self.dashboard.generate_view())
            
            # Start Wispr Sync Task
            self._wispr_task = asyncio.create_task(self._wispr_sync_loop())
            
            try:
                while not self._should_stop:
                    live.update(self.dashboard.generate_view())
                    await self._conversation_turn()
            except KeyboardInterrupt:
                pass
            finally:
                if self._wispr_task:
                    self._wispr_task.cancel()
                self.player.stop_all()
                logging.info("Engine stopped")

    async def _conversation_turn(self):
        # 1. Listen for Voice OR Key
        self.dashboard.update("Listening (Press 'T' for Text)...", "green")
        self.live.update(self.dashboard.generate_view())
        
        # Non-blocking check for 'T' key or Speech
        found_trigger = None
        while not self._should_stop:
            # Check Keyboard
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char.lower() == b't':
                    found_trigger = "text"
                    break
            
            # Check Voice
            if self.mic.wait_for_speech_nonblocking(threshold=self.wake_threshold):
                found_trigger = "voice"
                break
            
            await asyncio.sleep(0.1)
            self.live.update(self.dashboard.generate_view())
        
        if found_trigger == "text":
            self.live.stop()
            await self._text_input_mode()
            self.live.start()
            return

        self.dashboard.update("Recording...", "red")
        self.live.update(self.dashboard.generate_view())
        
        # Record
        audio_data = self.mic.listen_until_silence(
            silence_threshold=self.audio_level_threshold,
            silence_duration=self.silence_duration
        )
        
        if len(audio_data) < 4000: # Ignore noise
            return
            
        # Stats
        duration = len(audio_data) / 32000
        self.dashboard.mic_status = f"{duration:.1f}s"
        self.dashboard.print_user(f"[{duration:.1f}s audio]")
        
        # 2. Process & Stream
        self.dashboard.update("Thinking...", "yellow")
        self.live.update(self.dashboard.generate_view())
        
        start_time = time.time()
        first_token_time = None
        
        try:
            # Prepare request
            wav_data = self._create_wav(audio_data)
            audio_part = types.Part.from_bytes(data=wav_data, mime_type="audio/wav")
            
            # RAG Retrieval & Persistence
            context_str = ""
            user_transcript = ""
            if self.memory and self.stt:
                try:
                    self.dashboard.console.print("[dim]Transcribing (Whisper GPU)...[/dim]")
                    # Transcribe for Memory Query
                    wav_io = io.BytesIO(wav_data)
                    segments, _ = self.stt.transcribe(wav_io, beam_size=1)
                    user_transcript = " ".join([s.text for s in segments]).strip()
                    
                    if user_transcript:
                        self.dashboard.print_user(f"You: '{user_transcript}'")
                        
                        # PERSIST MEMORY
                        self.dashboard.console.print("[dim]Saving & Recalling...[/dim]")
                        self.memory.insert(user_transcript, role="user")
                        
                        memories = self.memory.recall(user_transcript, top_k=2)
                        
                        if memories:
                            facts = [f"- {m['content']}" for m in memories]
                            context_str = "\n[MEMORY CONTEXT]:\n" + "\n".join(facts) + "\n"
                            self.dashboard.console.print(f"[dim]Recalled {len(memories)} facts[/dim]")
                    else:
                         self.dashboard.console.print("[dim]No speech extracted.[/dim]")
                         
                except Exception as e:
                    logging.error(f"RAG Error: {e}")
                    self.dashboard.console.print(f"[red]RAG Error: {e}[/red]")

            prompt = f"Respond naturally based on context. Keep it concise.{context_str}"
            
            self.dashboard.console.print("[dim]Gemini 3 Direct Call (thinking_level=low)...[/dim]")
            
            # Build full prompt with system instruction and current time (direct API pattern from cookbook)
            current_time = datetime.now(ZoneInfo("America/New_York")).strftime("%I:%M%p %Z on %A, %B %d, %Y")
            full_prompt = VOICE_SYSTEM_PROMPT + f"\n\n[CURRENT TIME: {current_time}]\n\n" + prompt
            
            # Direct model call - matching Gemini Cookbook pattern
            self.dashboard.console.print("[dim]→ Sending to Gemini...[/dim]")
            try:
                response_stream = await self.client.aio.models.generate_content_stream(
                    model=MODEL_NAME,
                    contents=[audio_part, full_prompt],
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_level="low",
                            include_thoughts=True
                        ),
                        temperature=1.0
                    )
                )
            except Exception as stream_error:
                self.dashboard.console.print(f"[red]Stream Error: {stream_error}[/red]")
                logging.error(f"Gemini Stream Error: {stream_error}")
                return
                
            self.dashboard.console.print("[dim]→ Stream connected, receiving...[/dim]")
            full_text = ""
            current_sentence = ""
            chunk_count = 0
            
            self.dashboard.update("Speaking...", "magenta")
            
            async for chunk in response_stream:
                chunk_count += 1
                if not first_token_time:
                    first_token_time = time.time()
                    self.dashboard.last_latency = first_token_time - start_time
                    
                # DEBUG: Log raw chunk info
                self.dashboard.console.print(f"[dim]  Chunk #{chunk_count}: {type(chunk).__name__}[/dim]")
                
                try:
                    if not hasattr(chunk, 'candidates') or not chunk.candidates:
                        self.dashboard.console.print(f"[dim yellow]  → No candidates in chunk[/dim yellow]")
                        continue
                    candidate = chunk.candidates[0]
                    if not hasattr(candidate, 'content') or not candidate.content:
                        continue
                    if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                        continue
                        
                    for part in candidate.content.parts:
                        # Log function calls (not executing - just direct model call)
                        if hasattr(part, 'function_call') and part.function_call:
                            self.dashboard.console.print(f"[bold yellow]🔧 Tool Request: {part.function_call.name}[/bold yellow]")
                            continue
                        
                        # Skip parts without text
                        if not hasattr(part, 'text') or not part.text:
                            continue
                        
                        # Skip thought parts (don't speak them)
                        if hasattr(part, 'thought') and part.thought:
                            self.dashboard.console.print(f"[dim cyan]💭 {part.text[:60]}...[/dim cyan]")
                            continue
                        
                        # Regular text - process for TTS
                        text_chunk = part.text
                        full_text += text_chunk
                        current_sentence += text_chunk
                        
                        # Sentence Splitter
                        sentences = SENTENCE_ENDINGS.split(current_sentence)
                        if len(sentences) > 1:
                            to_process = sentences[:-1]
                            current_sentence = sentences[-1]
                            for sent in to_process:
                                if sent.strip():
                                    self._process_tts(sent)
                                    self.dashboard.print_kaedra(sent)
                except Exception as chunk_error:
                    logging.error(f"Chunk Parse Error: {chunk_error}")
                    self.dashboard.console.print(f"[red]  Chunk Error: {chunk_error}[/red]")
                    continue

            # Stream completion log
            self.dashboard.console.print(f"[dim]Stream ended: {chunk_count} chunks, {len(full_text)} chars text[/dim]")
            
            if chunk_count == 0:
                self.dashboard.console.print("[red]No chunks received from Gemini![/red]")

            # Final sentence
            if current_sentence.strip():
                self._process_tts(current_sentence)
                self.dashboard.print_kaedra(current_sentence)

        except Exception as e:
            logging.error(f"Process Error: {e}")
            self.dashboard.update(f"Error: {e}", "red")

    async def _wispr_sync_loop(self):
        """Background task to sync Wispr Flow transcripts to Memory Bank."""
        self.dashboard.console.print("[dim]Wispr: Initializing Smart Sync...[/dim]")
        
        # 1. Initial Smart Ingest (Last 10 entries if not already processed)
        try:
            transcripts = self.wispr.get_recent_transcripts(limit=10)
            if transcripts and self.memory:
                # We reverse to process in chronological order
                for t in reversed(transcripts):
                    text = t.get('text', "").strip()
                    if len(text) > 10:
                        # MemoryService handles duplicates internally by content hash/timestamp usually
                        # but we just push it as a context event
                        context = f"Wispr Sync ({t['timestamp']}): {text}"
                        self.memory.insert(content=context, role="user")
                
                self.dashboard.console.print(f"[green]✓[/green] Wispr: Synced {len(transcripts)} recent notes")
        except Exception as e:
            logging.error(f"Wispr Initial Sync Error: {e}")

        # 2. Real-time Polling
        while not self._should_stop:
            try:
                # The WisprService class has its own polling internally if we use start()
                # but for simple integration here we'll just check for the LATEST entry
                # to avoid managing too many callbacks.
                latest = self.wispr._get_latest_transcript_entry()
                if latest:
                    ts = latest.get('timestamp')
                    if ts != self.wispr.last_processed_timestamp:
                        self.wispr.last_processed_timestamp = ts
                        text = latest.get('formattedText') or latest.get('asrText') or ""
                        if len(text.strip()) > 10:
                            context = f"Wispr Flow ({ts}): {text}"
                            if self.memory:
                                self.memory.insert(content=context, role="user")
                                self.dashboard.console.print(f"[dim]Wispr: Synced new note[/dim]")
                
                await asyncio.sleep(5) # Poll every 5s
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Wispr Sync Loop Error: {e}")
                await asyncio.sleep(10)

    async def _text_input_mode(self):
        """
        BULLETPROOF Paste Mode using raw msvcrt character capture with idle-timeout.
        
        Why this works:
        1. msvcrt.getwch() reads characters directly from the console buffer, bypassing
           Python's stdin which can be affected by Rich's Live display and PowerShell quirks.
        2. Uses a timeout-based "idle detection" - if no keypress for 1.5 seconds after
           receiving content, we assume the paste is complete.
        3. Supports manual submission via Enter on an empty line (double-Enter).
        """
        self.player.stop_all()  # Stop current speech
        
        # Completely stop the Live display to release terminal
        self.live.stop()
        
        print("\n" + "="*80)
        print(" [PASTE MODE - BULLETPROOF EDITION]")
        print(" 1. Paste your content now (Ctrl+V or right-click).")
        print(" 2. SUBMIT: Wait 1.5 seconds OR press Enter twice on empty line.")
        print("="*80 + "\n")
        
        def get_paste_input_bulletproof():
            import time
            
            # Flush any stray keys from buffer
            while msvcrt.kbhit():
                msvcrt.getch()
            
            buffer = []
            last_input_time = time.time()
            IDLE_TIMEOUT = 1.5  # Seconds of silence to auto-submit
            empty_line_count = 0
            current_line = []
            
            while True:
                # Check if a key is waiting
                if msvcrt.kbhit():
                    try:
                        char = msvcrt.getwch()  # Unicode-safe character read
                    except Exception:
                        continue
                    
                    last_input_time = time.time()
                    
                    # Handle special keys
                    if char == '\r':  # Enter key
                        line = "".join(current_line)
                        buffer.append(line)
                        print()  # Echo newline
                        
                        # Double-Enter detection for manual submit
                        if line.strip() == "":
                            empty_line_count += 1
                            if empty_line_count >= 2:
                                break
                        else:
                            empty_line_count = 0
                        
                        current_line = []
                    
                    elif char == '\x03':  # Ctrl+C - abort
                        return ""
                    
                    elif char == '\x1a':  # Ctrl+Z - submit (backup)
                        break
                    
                    elif char == '\b':  # Backspace
                        if current_line:
                            current_line.pop()
                            print('\b \b', end='', flush=True)  # Erase character visually
                    
                    elif char == '\x00' or char == '\xe0':
                        # Extended key (arrows, etc.) - read and ignore the next char
                        msvcrt.getwch()
                    
                    else:
                        current_line.append(char)
                        print(char, end='', flush=True)  # Echo character
                        empty_line_count = 0  # Reset on any non-empty input
                
                else:
                    # No key waiting - check for idle timeout
                    if buffer or current_line:  # Only timeout if we have SOME content
                        if time.time() - last_input_time > IDLE_TIMEOUT:
                            # Idle timeout - assume paste is done
                            if current_line:
                                buffer.append("".join(current_line))
                            break
                    
                    time.sleep(0.01)  # Small sleep to avoid busy-waiting
            
            return "\n".join(buffer).strip()

        # Run blocking input in a separate thread
        print("[DEBUG] Starting paste capture...")
        text_input = await asyncio.to_thread(get_paste_input_bulletproof)
        print(f"[DEBUG] Paste capture complete: {len(text_input) if text_input else 0} chars")
        
        if not text_input:
            print("[DEBUG] No text received, returning to main loop")
            self.live.start()  # Restart live display before returning
            return
        
        self.dashboard.print_user(f"[TEXT DUMP]: {len(text_input)} chars received.")
        
        # Re-start live view
        self.live.start()
        
        # Process as Chat Input
        self.dashboard.update("Analyzing Consolidated Content...", "yellow")
        
        start_time = time.time()
        first_token_time = None
        
        print(f"[DEBUG] Sending to Gemini: '{text_input[:100]}...'")
        
        try:
            # Enhanced prompt for large context with current time
            current_time = datetime.now(ZoneInfo("America/New_York")).strftime("%I:%M%p %Z on %A, %B %d, %Y")
            full_prompt = (
                VOICE_SYSTEM_PROMPT + f"\n\n[CURRENT TIME: {current_time}]\n\n"
                f"The user has provided a LARGE block of text (chat log / article). "
                f"Analyze the ENTIRE content first, then provide a soulful, strategic response via voice. "
                f"Don't just acknowledge snippets—give me the big picture analysis in your Shadow Tactician persona.\n\n"
                f"CONTENT:\n{text_input}"
            )
            
            self.dashboard.update("Analyzing...", "yellow")
            
            # Direct model call - matching working voice pattern
            self.dashboard.console.print("[dim]Gemini 3 Direct Call (Text Mode)...[/dim]")
            response_stream = await self.client.aio.models.generate_content_stream(
                model=MODEL_NAME,
                contents=[full_prompt],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low",
                        include_thoughts=True
                    ),
                    temperature=1.0
                )
            )
            
            current_sentence = ""
            chunk_count = 0
            full_text = ""
            
            self.dashboard.update("Speaking (Analysis)...", "magenta")
            
            async for chunk in response_stream:
                chunk_count += 1
                if not first_token_time:
                    first_token_time = time.time()
                    self.dashboard.last_latency = first_token_time - start_time
                
                try:
                    if not hasattr(chunk, 'candidates') or not chunk.candidates:
                        continue
                    candidate = chunk.candidates[0]
                    if not hasattr(candidate, 'content') or not candidate.content:
                        continue
                    if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                        continue
                        
                    for part in candidate.content.parts:
                        # Skip thought parts
                        if hasattr(part, 'thought') and part.thought:
                            self.dashboard.console.print(f"[dim cyan]💭 {part.text[:60]}...[/dim cyan]")
                            continue
                        
                        if not hasattr(part, 'text') or not part.text:
                            continue
                        
                        text_chunk = part.text
                        full_text += text_chunk
                        current_sentence += text_chunk
                        
                        # Sentence Splitter
                        sentences = SENTENCE_ENDINGS.split(current_sentence)
                        if len(sentences) > 1:
                            to_process = sentences[:-1]
                            current_sentence = sentences[-1]
                            for sent in to_process:
                                if sent.strip():
                                    self._process_tts(sent)
                                    self.dashboard.print_kaedra(sent)
                except Exception as chunk_error:
                    logging.error(f"Chunk Parse Error: {chunk_error}")
                    continue

            # Stream completion log
            self.dashboard.console.print(f"[dim]Text Mode Stream ended: {chunk_count} chunks, {len(full_text)} chars[/dim]")

            # Final Sentence
            if current_sentence.strip():
                self._process_tts(current_sentence)
                self.dashboard.print_kaedra(current_sentence)
                
        except Exception as e:
            logging.error(f"Text Mode Error: {e}")
            self.dashboard.update(f"Text Error: {e}", "red")

    def _process_tts(self, text: str):
        """Generate and queue audio."""
        # Strip markdown/parents
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\*.*?\*', '', text)
        text = text.strip()
        
        if not text: return
        
        audio = self.tts.generate(text)
        if audio is not None:
            # Convert float32 to int16 for StreamWorker
            audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)
            self.player.add(audio_int16.tobytes())

    def _create_wav(self, data: bytes) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(data)
        return buf.getvalue()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default="kaedra_voice_reference.wav")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    
    # Init Logging
    logging.basicConfig(
        filename='kaedra_voice.log', 
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )
    
    print("Initializing...")
    
    # 1. Client
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    
    # 2. Mic
    mic = MicrophoneService()
    
    # 3. TTS
    voice_ref = args.voice if Path(args.voice).exists() else None
    tts = ChatterboxGenerator(reference_audio=voice_ref, device=args.device)
    
    # 4. Engine
    engine = ChatterboxVoiceEngine(mic, tts, client)
    
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
