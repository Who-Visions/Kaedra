from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
import numpy as np

class SmartVadManager:
    """Manages Smart Turn VAD to detect end of speech."""
    def __init__(self):
        try:
            self.analyzer = LocalSmartTurnAnalyzerV3()
            self.enabled = True
            print("[*] Smart Turn VAD Initialized")
        except Exception as e:
            print(f"[!] Smart Turn VAD Init Failed: {e}. Falling back to energy VAD.")
            self.enabled = False

    def should_end_turn(self, audio_bytes: bytes, sample_rate: int = 16000) -> bool:
        if not self.enabled:
            return False
            
        # The analyzer expects a specific window (usually ~4-8s).
        # Let's slice the last 4 seconds to keep it snappy.
        # 16000 samples/sec * 4 sec = 64000 samples
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        if len(audio_int16) > 64000:
            audio_int16 = audio_int16[-64000:]
            
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        try:
             result = self.analyzer._predict_endpoint(audio_float32)
             return result.get("prediction", 0) == 1
        except Exception as e:
             return False
