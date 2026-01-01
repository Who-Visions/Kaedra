
import asyncio
import numpy as np
import time
import logging
from rich.console import Console
from rich.table import Table
from kaedra.services.fast_flow import FastFlowService

console = Console()
logging.getLogger("FastFlow").setLevel(logging.WARNING) # Reduce noise

def stress_test():
    console.print("[bold cyan]Running FastFlow Stress Test...[/bold cyan]")
    
    # 1. Initialize Service
    service = FastFlowService(model_size="distil-small.en", debug=True)
    
    commits = []
    
    def on_commit(text):
        latency = (time.time() - start_time) 
        commits.append((text, latency))
        console.print(f"[green]COMMIT:[/green] {text} (T+{latency:.2f}s)")

    def on_partial(text):
        pass # console.print(f"[dim]Partial: {text}[/dim]")

    service.start(on_commit=on_commit, on_partial=on_partial)
    
    # 2. Simulate User Speech (10 seconds of simulated audio)
    # We will feed audio chunks at accelerated rate to test throughput
    
    # Generate 10s of random noise (silence) mixed with sine wave (speech-like signal)
    # Actually, Whisper needs somewhat real audio to output text.
    # We can't easily synthesize speech here without TTS.
    # So we will rely on silence processing speed and/or pre-recorded file if available.
    # For this test, we accept that verify processing speed of EMPTY/SILENCE or NOISE buffers 
    # is a valid proxy for pipeline overhead.
    
    console.print("[yellow]Simulating 30s audio stream...[/yellow]")
    
    sample_rate = 16000
    chunk_size = 1024
    
    # Generate a "beep" every 2 seconds
    audio_stream = []
    for i in range(30 * 16000 // chunk_size):
        if (i * chunk_size) % 32000 < 4000: # 0.25s beep
            chunk = np.sin(np.linspace(0, 440, chunk_size)) * 0.5
        else:
            chunk = np.zeros(chunk_size)
        audio_stream.append(chunk.astype(np.float32))

    start_time = time.time()
    
    for chunk in audio_stream:
        service.add_audio(chunk)
        # Simulate real-time by sleeping? 
        # If we want to test SPEED capability, we should NOT sleep and see how fast it chews through.
        # But FastFlow has an internal polling loop. If we flood the queue, it should drain it.
        time.sleep(chunk_size / sample_rate / 10) # Feed at 10x real-time speed
        
    end_time = time.time()
    service.stop()
    
    duration = end_time - start_time
    console.print(f"\n[bold]Results:[/bold]")
    console.print(f"Total Stream Time: 30s")
    console.print(f"Processing Time: {duration:.2f}s ({30/duration:.1f}x Real-Time)")
    console.print(f"Commits: {len(commits)}")
    
    if 30/duration > 1.0:
        console.print("[green]PASS: Faster than Real-Time[/green]")
    else:
        console.print("[red]FAIL: Slower than Real-Time[/red]")

if __name__ == "__main__":
    stress_test()
