"""
🎵 Lyria Music Generation Service
Kaedra's voice through Google DeepMind's Lyria RealTime API.

Model: lyria-realtime-exp
Output: 48kHz 16-bit PCM Stereo
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from google import genai
from google.genai import types
from rich.console import Console

console = Console()

@dataclass
class MusicConfig:
    """Configuration for music generation."""
    bpm: int = 90
    density: float = 0.5
    brightness: float = 0.5
    guidance: float = 4.0
    temperature: float = 1.0
    mute_bass: bool = False
    mute_drums: bool = False
    vocalization: bool = False  # Set True for vocal-like sounds
    scale: Optional[str] = None  # e.g., "C_MAJOR", "A_MINOR"

@dataclass 
class MusicPrompt:
    """Weighted prompt for music generation."""
    text: str
    weight: float = 1.0

class LyriaService:
    """Lyria RealTime music generation for Kaedra."""
    
    MODEL = "models/lyria-realtime-exp"
    SAMPLE_RATE = 48000
    CHANNELS = 2
    
    def __init__(self):
        # Use Gemini API with API key (Lyria not supported on Vertex AI)
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY required for Lyria")
        
        self.client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1alpha'}
        )
        self.session = None
        self.audio_buffer: List[bytes] = []
        self._receiving = False


    
    async def generate_track(
        self,
        prompts: List[MusicPrompt],
        config: MusicConfig = None,
        duration_seconds: int = 30,
        output_path: Optional[Path] = None
    ) -> bytes:
        """
        Generate a music track from prompts.
        
        Args:
            prompts: List of weighted prompts (genre, mood, instruments)
            config: Music generation config (BPM, density, etc.)
            duration_seconds: How long to generate (default 30s)
            output_path: Optional path to save WAV file
            
        Returns:
            Raw PCM audio bytes
        """
        config = config or MusicConfig()
        self.audio_buffer = []
        
        console.print(f"[bold magenta]🎵 Lyria generating...[/]")
        console.print(f"   Prompts: {[p.text for p in prompts]}")
        console.print(f"   Config: BPM={config.bpm}, Duration={duration_seconds}s")
        
        async def receive_audio(session):
            """Collect audio chunks."""
            self._receiving = True
            try:
                async for message in session.receive():
                    if hasattr(message, 'server_content') and message.server_content.audio_chunks:
                        audio_data = message.server_content.audio_chunks[0].data
                        self.audio_buffer.append(audio_data)
                    await asyncio.sleep(10**-12)
            except asyncio.CancelledError:
                pass
            finally:
                self._receiving = False
        
        async with self.client.aio.live.music.connect(model=self.MODEL) as session:
            # Start receiver task
            receive_task = asyncio.create_task(receive_audio(session))
            
            try:
                # Set prompts
                weighted_prompts = [
                    types.WeightedPrompt(text=p.text, weight=p.weight)
                    for p in prompts
                ]
                await session.set_weighted_prompts(prompts=weighted_prompts)
                
                # Set config
                gen_config = types.LiveMusicGenerationConfig(
                    bpm=config.bpm,
                    temperature=config.temperature,
                    guidance=config.guidance,
                    density=config.density,
                    brightness=config.brightness,
                    mute_bass=config.mute_bass,
                    mute_drums=config.mute_drums,
                )
                
                # Add vocalization mode if requested
                if config.vocalization:
                    gen_config.music_generation_mode = "VOCALIZATION"
                
                await session.set_music_generation_config(config=gen_config)
                
                # Start generation
                await session.play()
                
                # Wait for duration
                await asyncio.sleep(duration_seconds)
                
                # Stop
                await session.pause()
                
            finally:
                receive_task.cancel()
                try:
                    await receive_task
                except asyncio.CancelledError:
                    pass
        
        # Combine audio
        audio_bytes = b''.join(self.audio_buffer)
        console.print(f"[green]✅ Generated {len(audio_bytes)} bytes of audio[/]")
        
        # Save if path provided
        if output_path:
            self._save_wav(audio_bytes, output_path)
            console.print(f"[green]💾 Saved to {output_path}[/]")
        
        return audio_bytes
    
    def _save_wav(self, pcm_data: bytes, path: Path):
        """Save PCM data as WAV file."""
        import wave
        
        with wave.open(str(path), 'wb') as wav:
            wav.setnchannels(self.CHANNELS)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.SAMPLE_RATE)
            wav.writeframes(pcm_data)
    
    async def kaedra_theme(self, output_path: Optional[Path] = None) -> bytes:
        """Generate Kaedra's signature theme - dark, feminine, powerful."""
        prompts = [
            MusicPrompt("dark feminine electronic", weight=1.0),
            MusicPrompt("mysterious ethereal synth", weight=0.9),
            MusicPrompt("powerful queen energy", weight=0.7),
            MusicPrompt("noir atmosphere with subtle percussion", weight=0.6),
            MusicPrompt("haitian vodou undertones", weight=0.4),
        ]
        
        config = MusicConfig(
            bpm=85,
            density=0.4,
            brightness=0.35,
            guidance=4.5,
        )
        
        return await self.generate_track(
            prompts=prompts,
            config=config,
            duration_seconds=60,
            output_path=output_path
        )

    
    async def story_mood(
        self,
        mood: str,
        intensity: float = 0.5,
        output_path: Optional[Path] = None
    ) -> bytes:
        """Generate music for a story mood."""
        mood_presets = {
            "tension": {
                "prompts": ["suspenseful orchestral", "building tension", "dramatic strings"],
                "bpm": 100,
                "density": 0.6,
                "brightness": 0.4,
            },
            "victory": {
                "prompts": ["triumphant orchestral", "epic brass fanfare", "celebration"],
                "bpm": 120,
                "density": 0.7,
                "brightness": 0.7,
            },
            "melancholy": {
                "prompts": ["sad piano", "emotional strings", "gentle melancholy"],
                "bpm": 70,
                "density": 0.3,
                "brightness": 0.3,
            },
            "action": {
                "prompts": ["intense percussion", "driving electronic", "adrenaline"],
                "bpm": 140,
                "density": 0.8,
                "brightness": 0.6,
            },
            "romance": {
                "prompts": ["romantic piano", "soft strings", "intimate atmosphere"],
                "bpm": 75,
                "density": 0.4,
                "brightness": 0.5,
            },
        }
        
        preset = mood_presets.get(mood.lower(), mood_presets["tension"])
        
        prompts = [MusicPrompt(p, weight=1.0 - (i * 0.2)) for i, p in enumerate(preset["prompts"])]
        config = MusicConfig(
            bpm=preset["bpm"],
            density=preset["density"] * intensity,
            brightness=preset["brightness"],
        )
        
        return await self.generate_track(
            prompts=prompts,
            config=config,
            duration_seconds=30,
            output_path=output_path
        )


# CLI Test
async def main():
    service = LyriaService()
    
    console.print("[bold]🎵 Lyria Service Test[/]")
    console.print("Generating Kaedra's theme...")
    
    output = Path("kaedra_theme.wav")
    await service.kaedra_theme(output_path=output)
    
    console.print(f"\n✅ Done! Check: {output}")

if __name__ == "__main__":
    asyncio.run(main())
