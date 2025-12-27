"""
Extract Pour Minds voice clip and convert for Chatterbox.
"""

from pydub import AudioSegment
import os

# Source file
source_audio = r"c:\Users\super\kaedra_proper\gabrielle_union.mp3"

# Output path  
output_wav = r"c:\Users\super\kaedra_proper\kaedra_voice_reference.wav"

print(f"[*] Loading: {os.path.basename(source_audio)}")
audio = AudioSegment.from_mp3(source_audio)

print(f"[*] Duration: {len(audio)/1000:.2f}s")

# Take first 10 seconds
clip = audio[:10000]

# Convert to mono and 24kHz sample rate (Chatterbox native format)
clip = clip.set_channels(1)
clip = clip.set_frame_rate(24000)

# Export as WAV
clip.export(output_wav, format="wav")
print(f"[*] Saved reference clip to: {output_wav}")
print(f"[*] Duration: {len(clip)/1000:.2f}s")
