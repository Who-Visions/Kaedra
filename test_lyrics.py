import asyncio
import logging
import numpy as np
from kaedra.services.tts import StreamWorker
from chatterbox_speak import ChatterboxGenerator

LYRICS = """
I'm out of town, thuggin' with my rounds
My coochie pink, my booty-hole brown
Where the niggas? I'm lookin' for the hoes
Quit playin', nigga, come suck a bitch toe

Pound town, just left pound town
With my nigga, he just took a bitch down
Yeah, that nigga dick a bitch down
Yeah, that nigga eat me out

Verse 2:
Uh, uh, I'm out here in Miami
Lookin' for the hoochie daddies (Where they at?)
Where the niggas that get ratchet? (Where they at?)
My son need a new pappy
Too many bitches, where the niggas at?
I'm tryna get my coochie scratched (Yeah)
I'm tryna get my coochie stretched (Yeah)
You know them dread heads do it the best (Oh, yeah)
I like a nigga with a check
All my niggas give me neck
You know I'm sexy, I'm the best
I'm the shit, lil' bitch, I'm that (You know it)
I-I-I can't say his name 'cause he be cheatin' (I love you, baby)
Yeah, and I'm the reason
Ahahaha, niggas love a bad bitch (Yeah, yeah)
What Suki say? Nut on my tits (Sexyy)

Pound town, just left pound town (What?)
With my nigga, he just took a bitch down (What?)
Yeah, that nigga dick a bitch down (Hmm)
Yeah, that nigga eat me out (Hmm)
Pound town, just left pound town (Yeah)
With my nigga, he just took a bitch down
Yeah, that nigga dick a bitch down
Yeah, that nigga eat me out (Hmm)
"""

async def rap_test():
    print("[*] Initializing Chatterbox (Reference: kaedra_voice_new.wav)...")
    # Using local wrapper
    tts = ChatterboxGenerator(reference_audio="kaedra_voice_new.wav", device="cpu") # Force CPU to avoid pending restart issues
    
    player = StreamWorker(sample_rate=24000)
    
    print("[*] Spitting bars (4-bar chunks)...")
    # Clean and split into lines
    lines = [line.strip() for line in LYRICS.strip().split('\n') if line.strip()]
    
    # Group into chunks of 4 lines
    chunks = ['\n'.join(lines[i:i+4]) for i in range(0, len(lines), 4)]
    
    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i+1}]")
        print(chunk)
        
        audio = tts.generate(chunk)
        if audio is not None:
             # Convert float32 to int16
             audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)
             player.add(audio_int16.tobytes())
        
        # Pause between chunks to let them breathe
        await asyncio.sleep(0.5)
        
    print("[*] Done.")
    # Wait for playback
    await asyncio.sleep(10)
    player.stop_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(rap_test())
