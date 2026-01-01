#!/usr/bin/env python
"""
LONG FLOW MODE (Enterprise)
Uses kaedra.services.fast_flow for optimized long-context transcription.
"""
import asyncio
import sounddevice as sd
from rich.console import Console
from datetime import datetime
import time
from kaedra.services.fast_flow import FastFlowService

console = Console()

# CONFIG
SAMPLE_RATE = 16000
DEVICE_ID = 1  # Chat Mix
DEBUG = False

class LongFlowApp:
    def __init__(self):
        self.running = False
        self.service = FastFlowService(model_size="distil-small.en", debug=DEBUG)
        self.transcript_log = []
        
    def on_commit(self, text):
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Clear partial line
        print(f"\r" + " " * 100 + "\r", end="", flush=True)
        
        console.print(f"[{timestamp}] [green]➤ {text}[/green]")
        self.transcript_log.append(f"[{timestamp}] {text}")

    def on_partial(self, text):
        # Truncate for display if too long
        display_text = text[-80:] if len(text) > 80 else text
        print(f"\r[Partial] {display_text}" + " " * 20, end="", flush=True)

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            console.print(f"[red]Audio Status: {status}[/red]")
        self.service.add_audio(indata.copy())

    async def run(self):
        console.print(f"[bold cyan]FastFlow Enterprise Mode (Device {DEVICE_ID})[/bold cyan]")
        console.print("[dim]Loading customized distil-small.en model...[/dim]")
        
        self.service.start(on_commit=self.on_commit, on_partial=self.on_partial)
        self.running = True
        
        console.print("[dim]✓ Ready. Speak continuously.[/dim]")
        console.print("[dim]Ctrl+C to stop[/dim]\n")

        try:
            with sd.InputStream(
                device=DEVICE_ID,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='float32',
                callback=self.audio_callback,
                blocksize=4096
            ):
                while self.running:
                    await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.service.stop()
            console.print("\n[yellow]Stopping...[/yellow]")
            
            if self.transcript_log:
                fname = f"fast_flow_{datetime.now().strftime('%H%M%S')}.txt"
                with open(fname, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.transcript_log))
                console.print(f"[green]Saved {fname}[/green]")

if __name__ == "__main__":
    asyncio.run(LongFlowApp().run())
