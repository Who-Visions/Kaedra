import asyncio
import time
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from rich.live import Live

from kaedra.core.models import (
    SessionState, ConversationTurn, SessionStats, 
    AudioConfig, SessionConfig
)
from kaedra.core.utils import (
    create_wav_buffer, extract_all_metadata, execute_light_command
)
from kaedra.core.skills import SkillManager
from kaedra.ui.dashboard import KaedraDashboard
from kaedra.services.vad import SmartVadManager
from kaedra.services.mic import MicrophoneService
from kaedra.services.tts import TTSService
from kaedra.services.transcription import TranscriptionService
from kaedra.services.lifx import LIFXService

class ConversationManager:
    """Handles history, pruning, and persistence."""
    def __init__(self, client: genai.Client, model_name: str, config: SessionConfig, system_instruction: str):
        self.client = client
        self.model_id = model_name
        self.config = config
        self.system_instruction = system_instruction
        self.chat_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0
        )
        self.chat = client.aio.chats.create(model=model_name, config=self.chat_config)
        self.turns: List[ConversationTurn] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def prune_history(self):
        """Smart pruning to maintain 'full grasp' of context."""
        history = self.chat.get_history()
        # Allow deeper context (defined in config, default 20 turns / 40 messages)
        limit = self.config.max_history_turns * 2
        if len(history) > limit:
            trimmed = list(history[-limit:])
            self.chat = self.client.aio.chats.create(model=self.model_id, history=trimmed, config=self.chat_config)
            return True
        return False

    def save_transcript(self, sessions_dir: str = "./sessions"):
        if not self.config.save_transcripts or not self.turns: return None
        from pathlib import Path
        p = Path(sessions_dir)
        p.mkdir(exist_ok=True)
        filepath = p / f"kaedra_session_{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "turns": [{"user": t.transcription, "kaedra": t.response, "ms": int(t.inference_time * 1000)} for t in self.turns]
        }
        with open(filepath, 'w') as f: json.dump(data, f, indent=2)
        return filepath

class KaedraVoiceEngine:
    """Main voice conversation engine with core LIFX integration."""
    def __init__(self, mic: MicrophoneService, tts: TTSService, conversation: ConversationManager, audio_config: AudioConfig, session_config: SessionConfig, lifx: LIFXService, model_name: str = "gemini-3-flash-preview"):
        self.mic, self.tts, self.conversation = mic, tts, conversation
        self.audio_config, self.session_config, self.lifx = audio_config, session_config, lifx
        self.model_name = model_name
        self.stats = SessionStats()
        self.state = SessionState.IDLE
        self._should_stop, self._last_tts_end_time = False, 0
        self.dashboard = KaedraDashboard()
        self.vad = SmartVadManager()
        self.stt = TranscriptionService() # Defaults to high-fidelity distil-large-v3
        self.skills = SkillManager()
        self._pending_exec_result, self._active_tts_stream = None, None

    async def run(self):
        self.dashboard.console.print(self._banner()) 
        with Live(self.dashboard.generate_view(), refresh_per_second=10, console=self.dashboard.console) as live:
            self.live = live
            try:
                while not self._should_stop:
                    self.live.update(self.dashboard.generate_view())
                    await self._conversation_turn()
            except KeyboardInterrupt: pass
            finally: await self._shutdown()

    async def _conversation_turn(self):
        self.stats.total_turns += 1
        self.state = SessionState.IDLE
        await self.conversation.prune_history()
        self.dashboard.set_status("Listening", "green")
        self.dashboard.set_polygraph(False)
        self.live.update(self.dashboard.generate_view())

        self.mic.wait_for_speech(threshold=self.audio_config.wake_threshold)
        if (time.time() - self._last_tts_end_time) < self.audio_config.post_speech_cooldown:
            await asyncio.sleep(0.5)
            return

        self.state = SessionState.LISTENING
        self.dashboard.set_status("Recording...", "red")
        self.live.update(self.dashboard.generate_view())

        audio_buf = bytearray()
        if self.vad.enabled:
            for chunk in self.mic.listen_continuous():
                audio_buf.extend(chunk)
                if self.vad.should_end_turn(bytes(audio_buf)): break
        else:
            audio_buf = self.mic.listen_until_silence(self.audio_config.silence_threshold, self.audio_config.silence_duration)
        
        audio_data = bytes(audio_buf)
        self.state = SessionState.PROCESSING
        self.dashboard.set_status("Transcribing...", "yellow")
        self.live.update(self.dashboard.generate_view())
        
        transcription = self.stt.transcribe(audio_data)
        if not transcription.strip(): return

        # Context Engineering: Fast Skill Select
        active_skill = await self.skills.update_context(transcription)
        self.dashboard.set_status(f"Active: {active_skill.name}", "cyan")
        self.dashboard.update_history("User", transcription, "dim white")

        # STREAMING INFERENCE / BOTTLE-NECK OPTIMIZATION
        wav_data = create_wav_buffer(audio_data, self.mic.sample_rate)
        audio_part = types.Part.from_bytes(data=wav_data, mime_type="audio/wav")
        
        # Optimized persona reminder for lower token count / faster TTFT
        persona_reminder = f"[SKILL: {active_skill.name}]\n{self.skills.get_skill_prompt()}\n[LOCAL_STT: \"{transcription}\"]"
        
        parts = [types.Part.from_text(text=persona_reminder), audio_part]
        if self._pending_exec_result:
            parts.append(types.Part.from_text(text=self._pending_exec_result))
            self._pending_exec_result = None

        try:
            t0, first_token_time, response_buffer, tts_stream, tts_started, in_metadata = time.time(), 0, "", None, False, False
            think_level = self.session_config.thinking_level or "Low"
            gen_config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_level=think_level)) if "gemini-3" in self.model_name else None
            
            stream = await self.conversation.chat.send_message_stream(message=parts, config=gen_config)
            async for chunk in stream:
                if not chunk.candidates: continue
                if first_token_time == 0:
                     first_token_time = time.time() - t0
                     self.dashboard.set_status("Responding...", "magenta")

                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought: continue
                    if not part.text: continue
                    text = part.text
                    response_buffer += text
                    if any(token in text for token in ["[SILENCE]", "[NO RESPONSE]", "[HOLD]"]): continue
                    if any(kw in text.upper() or kw in text for kw in ["POLYGRAPH", "scanning", "truth"]): self.dashboard.set_polygraph(True)

                    if not in_metadata:
                        clean_part = ""
                        for char in text:
                            if char in ["[", "{", "`"]:
                                in_metadata = True
                                break
                            clean_part += char
                        if clean_part:
                            if not tts_started:
                                tts_stream = self.tts.begin_stream()
                                self._active_tts_stream = tts_stream
                                self.dashboard.start_stream("Kaedra")
                                tts_started = True
                            self.dashboard.print_stream(clean_part)
                            if tts_stream: tts_stream.feed_text(clean_part)

            self.dashboard.end_stream()
            if tts_stream: tts_stream.end()
            self._active_tts_stream = None
            
            meta = extract_all_metadata(response_buffer)
            final_clean = meta['clean_text']
            if any(token in final_clean for token in ["[SILENCE]", "[NO RESPONSE]", "[HOLD]"]):
                final_clean = ""
                self.dashboard.update_history("Kaedra", "[...silence...]", "dim blue")
            
            self.dashboard.update_history("Kaedra", final_clean, "magenta")
            self.dashboard.update_stats(first_token_time, 0, 0)

            # Exec Command handling
            if meta['exec_cmd']:
                 cmd = meta['exec_cmd']
                 if any(cmd.lower().startswith(kw) for kw in ["cat", "ls", "dir", "type", "pwd", "grep", "find"]):
                     try:
                         import subprocess
                         proc = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=10)
                         self._pending_exec_result = f"[EXEC_OUTPUT of '{cmd}']:\n{proc.stdout or proc.stderr}"
                     except Exception: pass

            # LIFX Execution logic
            if meta['light_simple'] or meta['light_json']:
                 async def run_lights_bg():
                     try:
                         if meta['light_json']: await asyncio.to_thread(self.lifx.set_states, meta['light_json'])
                         elif meta['light_simple']: await asyncio.to_thread(execute_light_command, self.lifx, meta['light_simple'])
                     except Exception as e:
                         print(f"[!] LIFX Execution Error: {e}")
                 asyncio.create_task(run_lights_bg())

            await self._speak_and_wait("")
            self.stats.successful_turns += 1
            await self.conversation.prune_history()
            self.conversation.save_transcript()

        except Exception as e:
            self.dashboard.update_history("System", f"Error: {e}", "red")

    async def _speak_and_wait(self, text: str):
        self.state = SessionState.SPEAKING
        if text: await asyncio.to_thread(self.tts.speak, text)
        while self.tts.is_speaking():
            try:
                if self.mic.get_current_rms() > self.audio_config.wake_threshold * 2:
                    if self._active_tts_stream: self._active_tts_stream.end()
                    self.tts.stop()
                    break
            except: pass
            await asyncio.sleep(0.1)
        self._last_tts_end_time = time.time()

    async def _shutdown(self):
        self.conversation.save_transcript()

    def _banner(self) -> str:
        return f"[bold magenta]KAEDRA MODULAR ENGINE[/bold magenta] | Model: {self.model_name}\n"
