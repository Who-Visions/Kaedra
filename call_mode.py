#!/usr/bin/env python
"""
KAEDRA SILENT CALL MODE v8
Hybrid: Whisper for YOUR mic (accurate) + Gemini for CALLER (fast).
"""
import asyncio
import numpy as np
import sounddevice as sd
from rich.console import Console
from datetime import datetime
import pytz
import threading
from queue import Queue
import io
import wave
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv
from faster_whisper import WhisperModel

console = Console()
load_dotenv()

# CONFIG
SAMPLE_RATE = 16000
# CONFIG
SAMPLE_RATE = 16000
CHUNK_DURATION = 30  # 30s chunks for maximum context

# Device IDs
YOUR_MIC_DEVICE = 1    # Chat Mix
BROWSER_DEVICE = 9     # Elgato Out Only

class HybridCallMode:
    def __init__(self):
        self.running = False
        self.transcript_lines = []
        self.gemini_client = None
        self.whisper_model = None
        self.audio_queue = Queue()
        
    def init_models(self):
        # Whisper for YOUR mic (accurate)
        console.print("[dim]Loading Whisper for your mic...[/dim]")
        self.whisper_model = WhisperModel("distil-large-v3", device="cpu", compute_type="int8")
        console.print("[green]✓ Whisper Ready[/green]")
        
        # Gemini for CALLER (cleaner audio)
        console.print("[dim]Connecting to Gemini for caller...[/dim]")
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.gemini_client = genai.Client(api_key=api_key)
            console.print("[green]✓ Gemini Ready[/green]")
        else:
            console.print("[yellow]No Gemini API key - using Whisper for both[/yellow]")
    
    def audio_callback_mic(self, indata, frames, time_info, status):
        self.audio_queue.put(("YOU", indata.copy()))
    
    def audio_callback_browser(self, indata, frames, time_info, status):
        self.audio_queue.put(("CALLER", indata.copy()))
    
    def audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wf.writeframes(audio_int16.tobytes())
        return buffer.getvalue()
    
    def transcribe_whisper(self, audio: np.ndarray) -> str:
        """Use Whisper for accurate transcription (no hallucinations)."""
        if np.abs(audio).max() < 0.005:
            return ""
        
        segments, _ = self.whisper_model.transcribe(
            audio,
            beam_size=1,
            language="en",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300)
        )
        text = " ".join([s.text.strip() for s in segments]).strip()
        return text if len(text) > 2 else ""
    
    def transcribe_gemini(self, audio: np.ndarray) -> str:
        """Use Gemini for caller (cleaner browser audio)."""
        if np.abs(audio).max() < 0.005:
            return ""
        
        if not self.gemini_client:
            return self.transcribe_whisper(audio)
        
        try:
            wav_bytes = self.audio_to_wav_bytes(audio.flatten())
            response = self.gemini_client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    "Transcribe ONLY the exact spoken words. Output nothing if unclear.",
                    types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
                ]
            )
            text = response.text.strip() if response.text else ""
            skip = ["[silence]", "(silence)", "[no speech]", "[music]", "(no speech)"]
            if text.lower() in skip or len(text) < 3:
                return ""
            return text
        except:
            return ""
    
    def transcribe_worker(self):
        eastern = pytz.timezone('US/Eastern')
        mic_buffer = []
        browser_buffer = []
        target_samples = int(SAMPLE_RATE * CHUNK_DURATION)
        
        while self.running:
            try:
                source, chunk = self.audio_queue.get(timeout=0.3)
                
                if source == "YOU":
                    mic_buffer.append(chunk)
                    if sum(len(c) for c in mic_buffer) >= target_samples:
                        audio = np.concatenate(mic_buffer).flatten()
                        mic_buffer = []
                        # Use WHISPER for your mic (accurate)
                        text = self.transcribe_whisper(audio)
                        if text:
                            timestamp = datetime.now(eastern).strftime("%H:%M:%S")
                            console.print(f"[dim]{timestamp}[/dim] [cyan]YOU:[/cyan] {text}")
                            self.transcript_lines.append(f"[{timestamp}] YOU: {text}")
                        
                elif source == "CALLER":
                    browser_buffer.append(chunk)
                    if sum(len(c) for c in browser_buffer) >= target_samples:
                        audio = np.concatenate(browser_buffer).flatten()
                        browser_buffer = []
                        # Use GEMINI for caller (faster, cleaner audio)
                        text = self.transcribe_gemini(audio)
                        if text:
                            timestamp = datetime.now(eastern).strftime("%H:%M:%S")
                            console.print(f"[dim]{timestamp}[/dim] [yellow]CALLER:[/yellow] {text}")
                            self.transcript_lines.append(f"[{timestamp}] CALLER: {text}")
            except:
                pass
    
    async def run(self):
        self.init_models()
        self.running = True
        
        console.print("\n[bold green]══ HYBRID CALL v8 ══[/bold green]")
        console.print("[dim]YOU: Whisper (accurate) | CALLER: Gemini (fast)[/dim]")
        console.print("[dim]Ctrl+C to stop[/dim]\n")
        
        transcribe_thread = threading.Thread(target=self.transcribe_worker, daemon=True)
        transcribe_thread.start()
        
        try:
            with sd.InputStream(
                device=YOUR_MIC_DEVICE,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                callback=self.audio_callback_mic,
                blocksize=int(SAMPLE_RATE * 0.3)
            ), sd.InputStream(
                device=BROWSER_DEVICE,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                callback=self.audio_callback_browser,
                blocksize=int(SAMPLE_RATE * 0.3)
            ):
                while self.running:
                    await asyncio.sleep(0.05)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            console.print("\n[yellow]== END ==[/yellow]")
            
            if self.transcript_lines:
                filename = f"call_{datetime.now().strftime('%H%M%S')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(self.transcript_lines))
                console.print(f"[green]Saved: {filename}[/green]")

if __name__ == "__main__":
    asyncio.run(HybridCallMode().run())
