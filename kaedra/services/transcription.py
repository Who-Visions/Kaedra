import os
import io
import wave
import torch
from faster_whisper import WhisperModel
from typing import Optional

class TranscriptionService:
    """
    Systran Faster-Whisper Service for local high-fidelity STT.
    Optimized for speed and accuracy.
    """
    def __init__(self, model_size: str = "distil-large-v3", device: str = None, compute_type: str = "int8"):
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"[*] Initializing Faster-Whisper ({model_size}) on {self.device}...")
        
        # Load model
        self.model = WhisperModel(model_size, device=self.device, compute_type=compute_type)
        print(f"[*] Faster-Whisper Loaded.")

    def transcribe(self, audio_data: bytes, sample_rate: int = 16000, context_prompt: str = None) -> str:
        """
        Transcribes a raw PCM audio buffer.
        """
        # Convert raw PCM to a format faster-whisper can read (wav-like or float32 np array)
        # Faster-Whisper can take a file path, a file-like object, or a numpy array.
        # Using a BytesIO with WAV header is reliable.
        
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)
        
        wav_io.seek(0)
        
        # Initial prompt guidelines to help Whisper with context and specific names
        base_prompt = "Kaedra is a sharp, intelligent AI voice assistant based in New York. Conversational, modern slang."
        
        # Inject dynamic context if provided (Wispr Flow: Context-Conditioned ASR)
        full_prompt = f"{base_prompt} Context: {context_prompt}" if context_prompt else base_prompt

        segments, info = self.model.transcribe(
            wav_io, 
            beam_size=5, 
            initial_prompt=full_prompt
        )
        
        text = " ".join([segment.text for segment in segments]).strip()
        
        # Hallucination Filter
        # Faster-Whisper often outputs "Thank you." or "MBC" on silence/noise.
        hallucinations = ["Thank you.", "Thank you", "Thanks.", "MBC", "You", "."]
        if text in hallucinations or not text:
            return ""
            
        return text

if __name__ == "__main__":
    # Quick test if run directly
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        service = TranscriptionService(model_size="tiny") # Use tiny for quick verify
        with open(path, "rb") as f:
            audio = f.read()
        print(f"Result: {service.transcribe(audio)}")
