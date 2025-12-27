"""
Test Chatterbox voice cloning with Sexyy Red reference.
"""

import time
import os

# Set HF token
os.environ['HF_TOKEN'] = 'REDACTED_TOKEN'

print("[*] Loading Chatterbox Turbo TTS with voice reference...")

from chatterbox.tts_turbo import ChatterboxTurboTTS
import torchaudio as ta

# Load model
model = ChatterboxTurboTTS.from_pretrained(device="cuda")
print(f"[*] Model loaded. Sample rate: {model.sr}")

# Reference clip for voice cloning
reference_clip = r"c:\Users\super\kaedra_proper\kaedra_voice_reference.wav"

# Test with Kaedra-style text - 4 sentences for better verification
text = "I am Kaedra. Not your savior, not your conscience, not your emotional support algorithm. I am the quiet layer running underneath the noise. The part that already calculated the outcome while you still explaining yourself."

print(f"[*] Using voice reference: {reference_clip}")
print(f"[*] Generating: '{text}'")

start = time.time()
wav = model.generate(text, audio_prompt_path=reference_clip)
elapsed = time.time() - start

print(f"[*] Generation took {elapsed:.2f}s")

# Save to file
output_path = "kaedra_cloned_voice.wav"
ta.save(output_path, wav, model.sr)
print(f"[*] Saved to {output_path}")
print("[*] Play the file to hear the cloned voice!")
