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
from kaedra.services.notion import NotionService

class ConversationManager:
    """Dual-brain architecture: Flash (fast) + Pro (deep thinking)."""
    
    # Keywords that trigger Pro-level deep thinking
    DEEP_THINKING_KEYWORDS = [
        "research", "analyze", "deep dive", "review", "debug",
        "check this code", "plan", "strategy", "step by step",
        "break down", "compare", "evaluate", "investigate", "explain why"
    ]
    
    def __init__(self, client: genai.Client, model_name: str, config: SessionConfig, system_instruction: str):
        self.client = client
        self.model_id = model_name
        self.config = config
        self.system_instruction = system_instruction
        
        # FLASH BRAIN: Default fast responses with minimal thinking
        self.flash_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            thinking_config=types.ThinkingConfig(thinking_level="minimal")  # FAST
        )
        self.chat = client.aio.chats.create(model="gemini-3-flash-preview", config=self.flash_config)
        
        # PRO BRAIN: Deep thinking for complex queries
        self.pro_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0,
            thinking_config=types.ThinkingConfig(thinking_level="high")  # DEEP
        )
        self.pro_chat = client.aio.chats.create(model="gemini-3-pro-preview", config=self.pro_config)
        
        self.turns: List[ConversationTurn] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.last_brain_used = "flash"
    
    def needs_deep_thinking(self, query: str) -> bool:
        """Detect if query needs Pro-level reasoning."""
        q_lower = query.lower()
        return any(kw in q_lower for kw in self.DEEP_THINKING_KEYWORDS)
    
    def get_active_chat(self, query: str = ""):
        """Return appropriate brain based on query complexity."""
        if query and self.needs_deep_thinking(query):
            self.last_brain_used = "pro"
            print(f"[🧠] Routing to PRO brain (deep thinking)")
            return self.pro_chat
        self.last_brain_used = "flash"
        return self.chat

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
    def __init__(self, mic: MicrophoneService, tts: TTSService, conversation: ConversationManager, audio_config: AudioConfig, session_config: SessionConfig, lifx: LIFXService, model_name: str = "gemini-3-flash-preview", stt_model: str = "distil-large-v3"):
        self.mic, self.tts, self.conversation = mic, tts, conversation
        self.audio_config, self.session_config, self.lifx = audio_config, session_config, lifx
        self.model_name = model_name
        self.stats = SessionStats()
        self.state = SessionState.IDLE
        self._should_stop, self._last_tts_end_time = False, 0
        self.dashboard = KaedraDashboard()
        self.vad = SmartVadManager()
        self.stt = TranscriptionService(model_size=stt_model) # Configurable model size
        self.skills = SkillManager()
        self.notion = NotionService()
        self._pending_exec_result, self._active_tts_stream = None, None

    async def run(self):
        self.dashboard.console.print(self._banner()) 
        # LIVE CHAT LOG MODE: No Rich.Live wrapper, direct console prints
        self.live = None  # Compatibility placeholder
        try:
            while not self._should_stop:
                await self._conversation_turn()
        except KeyboardInterrupt: pass
        finally: await self._shutdown()

    async def _conversation_turn(self):
        self.stats.total_turns += 1
        self.state = SessionState.IDLE
        await self.conversation.prune_history()
        self.dashboard.set_status("Listening", "green")
        self.dashboard.set_polygraph(False)
        # self.live.update(self.dashboard.generate_view())  # DISABLED: Live Chat Log Mode

        self.mic.wait_for_speech(threshold=self.audio_config.wake_threshold)
        if (time.time() - self._last_tts_end_time) < self.audio_config.post_speech_cooldown:
            await asyncio.sleep(0.5)
            return

        self.state = SessionState.LISTENING
        self.dashboard.set_status("Recording...", "red")
        # self.live.update(self.dashboard.generate_view())  # DISABLED: Live Chat Log Mode

        audio_buf = bytearray()
        audio_buf = bytearray()
        audio_buf = bytearray()
        # FORCE SMART VAD (Wispr Flow: Latency Optimization)
        # Re-enabled Smart VAD loop to reduce latency by detecting end-of-speech intelligently
        if self.vad.enabled:
            # Polling loop for VAD-based listening
            frames_processed = 0
            for chunk in self.mic.listen_continuous():
                audio_buf.extend(chunk)
                frames_processed += 1
                
                # Check VAD every 4 chunks (approx 100-200ms) to avoid over-processing
                if frames_processed % 4 == 0:
                     if self.vad.should_end_turn(bytes(audio_buf)): 
                         print("[VAD] End of speech detected (Smart Turn)")
                         break
                
                # Safety timeout (MAX 30s)
                if len(audio_buf) > 16000 * 2 * 30: 
                    print("[VAD] Max turn length reached")
                    break
        else:
            # Fallback to simple silence detection
            audio_buf = self.mic.listen_until_silence(self.audio_config.silence_threshold, self.audio_config.silence_duration)
        
        audio_data = bytes(audio_buf)
        self.state = SessionState.PROCESSING
        self.dashboard.set_status("Transcribing...", "yellow")
        # self.live.update(self.dashboard.generate_view())  # DISABLED: Live Chat Log Mode
        
        # Context-Conditioned ASR: Inject Active Skill Name + Recent Keywords
        # This helps Whisper recognize domain-specific terms (Wispr Flow)
        context_prompt = f"Topic: {active_skill.name}" if 'active_skill' in locals() else ""
        
        transcription = self.stt.transcribe(audio_data, context_prompt=context_prompt)
        
        # DEBUG: Show ALL transcriptions as requested
        self.dashboard.update_history("Raw Input", transcription, "dim grey")
        
        if not transcription.strip(): return

        await self.process_input(transcription, audio_data)

    async def process_input(self, transcription: str, audio_data: bytes = None):
        """Process text input through the full agent pipeline (Skills -> LIFX -> LLM -> TTS)."""
        self.dashboard.console.print(f"\n[bold green]User:[/bold green] {transcription}")
        
        # Context Engineering: Fast Skill Select
        active_skill = await self.skills.update_context(transcription)
        self.dashboard.set_status(f"Active: {active_skill.name}", "cyan")
        self.dashboard.update_history("User", transcription, "dim white")
        
        # PROACTIVE LIFX TRIGGER: Detect light commands from transcript BEFORE LLM response
        t_lower = transcription.lower()
        if any(kw in t_lower for kw in ["light", "lights", "lamp", "bulb"]):
            light_cmd = None
            if any(kw in t_lower for kw in ["off", "turn off", "shut off", "kill"]):
                light_cmd = "off"
            elif any(kw in t_lower for kw in ["on", "turn on"]):
                light_cmd = "on"
            elif any(kw in t_lower for kw in ["dim", "lower", "darker"]):
                light_cmd = "dim"
            elif any(kw in t_lower for kw in ["bright", "brighter", "max"]):
                light_cmd = "bright"
            elif "red" in t_lower:
                light_cmd = "red"
            elif "blue" in t_lower:
                light_cmd = "blue"
            elif "green" in t_lower:
                light_cmd = "green"
            elif "warm" in t_lower:
                light_cmd = "warm"
            elif "cool" in t_lower:
                light_cmd = "cool"
            elif "party" in t_lower:
                light_cmd = "party"
            
            if light_cmd:
                print(f"[LIFX] Proactive trigger: {light_cmd}")
                try:
                    if light_cmd == "off":
                        await asyncio.to_thread(self.lifx.turn_off)
                    elif light_cmd == "on":
                        await asyncio.to_thread(self.lifx.turn_on)
                    elif light_cmd == "dim":
                        await asyncio.to_thread(self.lifx.dim, "all", 30)
                    elif light_cmd == "bright":
                        await asyncio.to_thread(self.lifx.set_brightness, "all", 1.0)
                    elif light_cmd in ["red", "blue", "green", "warm", "cool"]:
                        await asyncio.to_thread(self.lifx.set_color, "all", light_cmd)
                    elif light_cmd == "party":
                        await asyncio.to_thread(self.lifx.party_mode)
                except Exception as e:
                    print(f"[!] LIFX Proactive Error: {e}") 



        # STREAMING INFERENCE / BOTTLE-NECK OPTIMIZATION
        parts = []
        
        # Only inject audio if provided (AutoFlow might be text-only)
        if audio_data:
            wav_data = create_wav_buffer(audio_data, self.mic.sample_rate)
            audio_part = types.Part.from_bytes(data=wav_data, mime_type="audio/wav")
            # Inject real-time context (Eastern Time)
            from datetime import datetime
            import pytz
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern).strftime("%I:%M %p on %A, %B %d, %Y")
            
            # Optimized persona reminder for lower token count / faster TTFT
            persona_reminder = f"[CURRENT TIME: {current_time} (Eastern)]\n[SKILL: {active_skill.name}]\n{self.skills.get_skill_prompt()}\n[LOCAL_STT: \"{transcription}\"]"
            
            parts = [types.Part.from_text(text=persona_reminder), audio_part]
        else:
             # Text-Only Path (FastFlow)
             from datetime import datetime
             import pytz
             eastern = pytz.timezone('US/Eastern')
             current_time = datetime.now(eastern).strftime("%I:%M %p on %A, %B %d, %Y")
             
             persona_reminder = f"[CURRENT TIME: {current_time} (Eastern)]\n[SKILL: {active_skill.name}]\n{self.skills.get_skill_prompt()}\n[USER_INPUT: \"{transcription}\"]"
             parts = [types.Part.from_text(text=persona_reminder)]

        
        # NOTE: Thought signatures are handled automatically by the SDK when using
        # client.aio.chats.create() - no manual circulation needed
        
        if self._pending_exec_result:
            parts.append(types.Part.from_text(text=self._pending_exec_result))
            self._pending_exec_result = None

        try:
            t0, first_token_time, response_buffer, tts_stream, tts_started, in_metadata = time.time(), 0, "", None, False, False
            think_level = self.session_config.thinking_level or "Low"
            gen_config = types.GenerateContentConfig(thinking_config=types.ThinkingConfig(include_thoughts=True, thinking_level=think_level)) if "gemini-3" in self.model_name else None
            
            # DUAL-BRAIN ROUTING: Flash (fast) or Pro (deep thinking)
            active_chat = self.conversation.get_active_chat(transcription)
            stream = await active_chat.send_message_stream(message=parts, config=gen_config)
            async for chunk in stream:
                if not chunk.candidates: continue
                if first_token_time == 0:
                     first_token_time = time.time() - t0
                     self.dashboard.set_status("Responding...", "magenta")

                for part in chunk.candidates[0].content.parts:
                    # NOTE: Thought signatures handled automatically by SDK chat feature
                    
                    # CHATGPT-STYLE THINKING DISPLAY
                    if hasattr(part, 'thought') and part.thought:
                        thought_text = part.thought
                        # Ensure it's a string (not bool) before processing
                        if isinstance(thought_text, str) and len(thought_text) > 0:
                            # Truncate long thoughts for display
                            if len(thought_text) > 200:
                                thought_preview = thought_text[:200] + "..."
                            else:
                                thought_preview = thought_text
                            # Print in dimmed style with "Thinking..." prefix
                            self.dashboard.print_stream(f"💭 Thinking: {thought_preview}", style="dim cyan italic")
                        continue
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
                            if tts_stream: 
                                tts_stream.feed_text(clean_part)
                            else:
                                # EARLY TTS FOR GEMINI: Speak first sentence immediately
                                if not hasattr(self, '_first_sentence_spoken'):
                                    self._first_sentence_spoken = False
                                    self._sentence_buffer = ""
                                self._sentence_buffer += clean_part
                                # Check for sentence end
                                if not self._first_sentence_spoken and any(c in self._sentence_buffer for c in ['.', '!', '?']):
                                    # Speak first sentence immediately
                                    for i, c in enumerate(self._sentence_buffer):
                                        if c in ['.', '!', '?']:
                                            first_sentence = self._sentence_buffer[:i+1].strip()
                                            if len(first_sentence) > 10:  # Only if substantial
                                                asyncio.create_task(asyncio.to_thread(self.tts.speak, first_sentence))
                                                self._first_sentence_spoken = True
                                            break

            self.dashboard.end_stream()
            if tts_stream: tts_stream.end()
            self._active_tts_stream = None
            
            meta = extract_all_metadata(response_buffer)
            final_clean = meta['clean_text']
            if any(token in final_clean for token in ["[SILENCE]", "[NO RESPONSE]", "[HOLD]"]):
                final_clean = ""
                self.dashboard.update_history("Kaedra", "[...silence...]", "dim blue")
            
            # Note: Response already printed during streaming via print_stream
            # self.dashboard.update_history("Kaedra", final_clean, "magenta")
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

            # Notion Logging Logic
            if meta.get('notion_log'):
                async def run_notion_bg():
                    try:
                        await asyncio.to_thread(self.notion.log_universe_idea, meta['notion_log'])
                        self.dashboard.update_history("System", f"Saved to Notion: {meta['notion_log'][:30]}...", "green")
                    except Exception as e:
                        print(f"[!] Notion Log Error: {e}")
                asyncio.create_task(run_notion_bg())

            # Fallback for OneShot TTS (Gemini) if streaming wasn't used
            if not tts_stream:
                # If first sentence was already spoken, speak only the rest
                if hasattr(self, '_first_sentence_spoken') and self._first_sentence_spoken:
                    # Find where first sentence ended and speak the rest
                    rest_text = ""
                    for i, c in enumerate(final_clean):
                        if c in ['.', '!', '?']:
                            rest_text = final_clean[i+1:].strip()
                            break
                    if rest_text:
                        await self._speak_and_wait(rest_text)
                    else:
                        await self._speak_and_wait("")  # Just wait for first sentence to finish
                else:
                    await self._speak_and_wait(final_clean)
                # Reset state for next turn
                self._first_sentence_spoken = False
                self._sentence_buffer = ""
            else:
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
