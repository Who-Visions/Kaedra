from dataclasses import dataclass, field
from enum import Enum
import time

class SessionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    COOLDOWN = "cooldown"

@dataclass
class ConversationTurn:
    turn_id: int
    timestamp: str
    user_audio_kb: float
    user_audio_seconds: float
    transcription: str
    response: str
    inference_time: float
    tokens_used: int = 0

@dataclass
class SessionStats:
    start_time: float = field(default_factory=time.time)
    total_turns: int = 0
    successful_turns: int = 0
    total_tokens: int = 0
    total_inference_time: float = 0
    total_audio_seconds: float = 0
    hallucinations_caught: int = 0
    feedback_rejected: int = 0
    errors: int = 0

    def summary(self) -> str:
        duration = time.time() - self.start_time
        avg_inference = self.total_inference_time / max(1, self.successful_turns)
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    SESSION SUMMARY                           ║
╠══════════════════════════════════════════════════════════════╣
║  Duration:          {duration/60:.1f} minutes
║  Total Attempts:    {self.total_turns}
║  Successful Turns:  {self.successful_turns}
║  Hallucinations:    {self.hallucinations_caught} caught
║  Feedback Rejected: {self.feedback_rejected}
║  Total Audio:       {self.total_audio_seconds:.1f}s processed
║  Avg Inference:     {avg_inference:.2f}s per turn
║  Est. Tokens:       ~{self.total_tokens:,}
║  Est. Cost:         ${(self.total_tokens / 1_000_000) * 1.75:.4f}
║  Errors:            {self.errors}
╚══════════════════════════════════════════════════════════════╝"""

@dataclass
class AudioConfig:
    wake_threshold: int = 400
    silence_threshold: int = 350
    silence_duration: float = 0.7
    max_record_seconds: float = 360.0
    post_speech_cooldown: float = 2.0
    feedback_rms_threshold: int = 3000

@dataclass
class SessionConfig:
    max_history_turns: int = 60 # Default to deep context (approx 120 messages)
    save_transcripts: bool = True
    tts_variant: str = "flash-lite"
    retry_attempts: int = 3
    retry_delay: float = 1.0
    thinking_level: str = "LOW"

# Hang protection timeouts
TRANSCRIPTION_TIMEOUT = 8.0
BRAIN_TIMEOUT = 15.0
TTS_TIMEOUT = 10.0
