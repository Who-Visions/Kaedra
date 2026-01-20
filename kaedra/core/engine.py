"""
KAEDRA v1.0 - Core Engine
The heartbeat of Kaedra, managing conversation flow, brain routing,
integrated hardware (LIFX), and agent skills.
"""

import asyncio
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

import pytz
from google import genai
from google.genai import types

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
            print("[🧠] Routing to PRO brain (deep thinking)")
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
            # Re-create flash chat with trimmed history
            self.chat = self.client.aio.chats.create(
                model="gemini-3-flash-preview", 
                history=trimmed, 
                config=self.flash_config
            )
            # Re-create pro chat with trimmed history
            self.pro_chat = self.client.aio.chats.create(
                model="gemini-3-pro-preview", 
                history=trimmed, 
                config=self.pro_config
            )
            return True
        return False

    def save_transcript(self, sessions_dir: str = "./sessions"):
        """Save the conversation transcript to a JSON file."""
        if not self.config.save_transcripts or not self.turns:
            return None
        p = Path(sessions_dir)
        p.mkdir(exist_ok=True)
        filepath = p / f"kaedra_session_{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "turns": [
                {
                    "user": t.transcription,
                    "kaedra": t.response,
                    "ms": int(t.inference_time * 1000)
                } for t in self.turns
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return filepath

class KaedraVoiceEngine: # pylint: disable=too-many-instance-attributes
    """Main voice conversation engine with core LIFX integration."""
    def __init__(self, mic: MicrophoneService, tts: TTSService,
                 conversation: ConversationManager, audio_config: AudioConfig,
                 session_config: SessionConfig, lifx: LIFXService,
                 model_name: str = "gemini-3-flash-preview",
                 stt_model: str = "distil-large-v3"): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        Initialize the Kaedra Voice Engine.
        
        Args:
            mic: Microphone service for audio input.
            tts: Text-to-Speech service for audio output.
            conversation: Manager for chat history and brain routing.
            audio_config: Configuration for audio levels and thresholds.
            session_config: General session settings.
            lifx: LIFX service for hardware light control.
            model_name: Default Gemini model to use.
            stt_model: Whisper model size for transcription.
        """
        self.mic = mic
        self.tts = tts
        self.conversation = conversation
        self.audio_config = audio_config
        self.session_config = session_config
        self.lifx = lifx
        self.model_name = model_name
        self.stats = SessionStats()
        self.state = SessionState.IDLE
        self._should_stop = False
        self._last_tts_end_time = 0
        self.dashboard = KaedraDashboard()
        self.vad = SmartVadManager()
        self.stt = TranscriptionService(model_size=stt_model)
        self.skills = SkillManager()
        self.notion = NotionService()
        self._pending_exec_result = None
        self._active_tts_stream = None
        self.live = None
        self._first_sentence_spoken = False
        self._sentence_buffer = ""

    async def run(self):
        """Start the main loop of the voice engine."""
        self.dashboard.console.print(self._banner())
        # LIVE CHAT LOG MODE: No Rich.Live wrapper, direct console prints
        self.live = None  # Compatibility placeholder
        try:
            while not self._should_stop:
                await self._conversation_turn()
        except KeyboardInterrupt:
            pass
        finally:
            await self._shutdown()

    async def _conversation_turn(self):
        """Execute a single turn of the conversation (Listen -> Process -> Speak)."""
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

        # Context-Conditioned ASR: Inject Recent Context
        # This helps Whisper recognize domain-specific terms (Wispr Flow)
        context_prompt = "" 

        transcription = self.stt.transcribe(audio_data, context_prompt=context_prompt)

        # DEBUG: Show ALL transcriptions as requested
        self.dashboard.update_history("Raw Input", transcription, "dim grey")

        if not transcription.strip():
            return

        await self.process_input(transcription, audio_data)

    async def process_input(self, transcription: str, audio_data: Optional[bytes] = None):
        """Process text input through the full agent pipeline (Skills -> LIFX -> LLM -> TTS)."""
        self.dashboard.console.print(f"\n[bold green]User:[/bold green] {transcription}")

        # Context Engineering: Fast Skill Select
        active_skill = await self.skills.update_context(transcription)
        self.dashboard.set_status(f"Active: {active_skill.name}", "cyan")
        self.dashboard.update_history("User", transcription, "dim white")

        # PROACTIVE LIFX TRIGGER
        await self._handle_proactive_lifx(transcription)

        # Prepare parts for inference
        parts = self._prepare_model_parts(transcription, active_skill, audio_data)
        if self._pending_exec_result:
            parts.append(types.Part.from_text(text=self._pending_exec_result))
            self._pending_exec_result = None

        try:
            # DUAL-BRAIN ROUTING
            active_chat = self.conversation.get_active_chat(transcription)
            response_buffer, first_token_time, tts_stream_used = await self._process_stream(active_chat, parts)

            # Metadata extraction and post-processing
            meta = extract_all_metadata(response_buffer)
            self.dashboard.update_stats(first_token_time, 0, 0)

            await self._handle_exec_cmd(meta)
            await self._handle_light_actions(meta)
            await self._handle_notion_actions(meta)

            await self._finalize_turn(meta, tts_stream_used)

        except Exception as engine_err: # pylint: disable=broad-exception-caught
            self.dashboard.update_history("System", f"Error: {engine_err}", "red")

    async def _handle_proactive_lifx(self, transcription: str):
        """Proactively trigger LIFX commands based on transcription."""
        t_lower = transcription.lower()
        if not any(kw in t_lower for kw in ["light", "lights", "lamp", "bulb"]):
            return

        light_cmd = self._get_light_command(t_lower)
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
            except Exception as proactive_err: # pylint: disable=broad-exception-caught
                print(f"[!] LIFX Proactive Error: {proactive_err}")

    def _get_light_command(self, t_lower: str) -> Optional[str]:
        """Parse light command from text."""
        if any(kw in t_lower for kw in ["off", "turn off", "shut off", "kill"]):
            return "off"
        if any(kw in t_lower for kw in ["on", "turn on"]):
            return "on"
        if any(kw in t_lower for kw in ["dim", "lower", "darker"]):
            return "dim"
        if any(kw in t_lower for kw in ["bright", "brighter", "max"]):
            return "bright"
        for color in ["red", "blue", "green", "warm", "cool", "party"]:
            if color in t_lower:
                return color
        return None

    def _prepare_model_parts(self, transcription: str, active_skill, audio_data: Optional[bytes]) -> List[types.Part]:
        """Prepare content parts for the Gemini model."""
        tz_eastern = pytz.timezone('US/Eastern')
        current_time = datetime.now(tz_eastern).strftime("%I:%M %p on %A, %B %d, %Y")
        
        prompt = (f"[CURRENT TIME: {current_time} (Eastern)]\n"
                  f"[SKILL: {active_skill.name}]\n"
                  f"{self.skills.get_skill_prompt()}\n")

        if audio_data:
            wav_data = create_wav_buffer(audio_data, self.mic.sample_rate)
            audio_part = types.Part.from_bytes(data=wav_data, mime_type="audio/wav")
            prompt += f"[LOCAL_STT: \"{transcription}\"]"
            return [types.Part.from_text(text=prompt), audio_part]
        
        prompt += f"[USER_INPUT: \"{transcription}\"]"
        return [types.Part.from_text(text=prompt)]

    async def _process_stream(self, active_chat, parts: List[types.Part]):
        """Handle the response stream from the Gemini model."""
        t0 = time.time()
        first_token_time, response_buffer, tts_stream, tts_started, in_metadata = 0, "", None, False, False
        
        stream = await active_chat.send_message_stream(message=parts)
        async for chunk in stream:
            if not chunk.candidates:
                continue
            if first_token_time == 0:
                first_token_time = time.time() - t0
                self.dashboard.set_status("Responding...", "magenta")

            res_buf, tts_s, tts_st, in_meta = await self._handle_chunk(
                chunk, response_buffer, tts_stream, tts_started, in_metadata
            )
            response_buffer, tts_stream, tts_started, in_metadata = res_buf, tts_s, tts_st, in_meta

        self.dashboard.end_stream()
        if tts_stream:
            tts_stream.end()
        self._active_tts_stream = None
        return response_buffer, first_token_time, tts_started

    async def _handle_chunk(self, chunk, response_buffer: str, tts_stream, 
                            tts_started: bool, in_metadata: bool): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Handle a single chunk from the stream."""
        for part in chunk.candidates[0].content.parts:
            response_buffer += self._handle_part_thought(part)
            if not part.text:
                continue
            
            text = part.text
            if any(token in text for token in ["[SILENCE]", "[NO RESPONSE]", "[HOLD]"]):
                continue
            
            self._check_polygraph(text)

            if not in_metadata:
                clean_part = self._extract_clean_text(text)
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
                        self._handle_one_shot_tts(clean_part)
                if clean_part != text:
                    in_metadata = True
        return response_buffer, tts_stream, tts_started, in_metadata

    def _check_polygraph(self, text: str):
        """Check for polygraph/truth triggers."""
        if any(kw in text.upper() or kw in text for kw in ["POLYGRAPH", "scanning", "truth"]):
            self.dashboard.set_polygraph(True)

    def _handle_part_thought(self, part) -> str:
        """Process and display model thoughts."""
        if hasattr(part, 'thought') and part.thought:
            thought_text = part.text
            if thought_text:
                preview = thought_text[:200] + "..." if len(thought_text) > 200 else thought_text
                self.dashboard.print_stream(f"💭 Thinking: {preview}", style="dim cyan italic")
            return ""
        return part.text or ""

    def _extract_clean_text(self, text: str) -> str:
        """Extract text that is not part of a metadata/tool tag."""
        clean = ""
        for char in text:
            if char in ["[", "{", "`"]:
                break
            clean += char
        return clean

    def _handle_one_shot_tts(self, clean_part: str):
        """Fallback TTS handling for first sentence acceleration."""
        if not self._first_sentence_spoken:
            self._sentence_buffer += clean_part
            if any(c in self._sentence_buffer for c in ['.', '!', '?']):
                for i, char in enumerate(self._sentence_buffer):
                    if char in ['.', '!', '?']:
                        first_s = self._sentence_buffer[:i+1].strip()
                        if len(first_s) > 10:
                            asyncio.create_task(
                                asyncio.to_thread(self.tts.speak, first_s)
                            )
                            self._first_sentence_spoken = True
                        break

    async def _handle_exec_cmd(self, meta: Dict):
        """Handle shell command execution."""
        if meta.get('exec_cmd'):
            cmd = meta['exec_cmd']
            if any(cmd.lower().startswith(kw) for kw in ["cat", "ls", "dir", "type", "pwd", "grep", "find"]):
                try:
                    proc = subprocess.run(["powershell", "-Command", cmd], 
                                         capture_output=True, text=True, timeout=10, check=False)
                    self._pending_exec_result = f"[EXEC_OUTPUT of '{cmd}']:\n{proc.stdout or proc.stderr}"
                except (subprocess.SubprocessError, subprocess.TimeoutExpired, 
                        OSError, ValueError) as err:
                    print(f"[!] Exec Error: {err}")

    async def _handle_light_actions(self, meta: Dict):
        """Handle light color/state changes."""
        if meta.get('light_simple') or meta.get('light_json'):
            async def run_lights_bg():
                try:
                    if meta.get('light_json'):
                        await asyncio.to_thread(self.lifx.set_states, meta['light_json'])
                    elif meta.get('light_simple'):
                        await asyncio.to_thread(execute_light_command, self.lifx, meta['light_simple'])
                except (RuntimeError, ValueError, KeyError) as lifx_err:
                    print(f"[!] LIFX Error: {lifx_err}")
                except Exception as fatal_err: # pylint: disable=broad-exception-caught
                    print(f"[!!] LIFX Fatal Error: {fatal_err}")
            asyncio.create_task(run_lights_bg())

    async def _handle_notion_actions(self, meta: Dict):
        """Handle Notion idea logging."""
        if meta.get('notion_log'):
            async def run_notion_bg():
                try:
                    await asyncio.to_thread(self.notion.log_universe_idea, meta['notion_log'])
                    self.dashboard.update_history("System", f"Saved to Notion: {meta['notion_log'][:30]}...", "green")
                except (IOError, ValueError, KeyError) as notion_err:
                    print(f"[!] Notion Error: {notion_err}")
                except Exception as fatal_err: # pylint: disable=broad-exception-caught
                    print(f"[!!] Notion Fatal: {fatal_err}")
            asyncio.create_task(run_notion_bg())

    async def _finalize_turn(self, meta: Dict, tts_stream_used: bool):
        """Finalize turn: final TTS wait, stats, and history pruning."""
        final_clean = meta['clean_text']
        if any(token in final_clean for token in ["[SILENCE]", "[NO RESPONSE]", "[HOLD]"]):
            final_clean = ""
            self.dashboard.update_history("Kaedra", "[...silence...]", "dim blue")

        if not tts_stream_used:
            await self._speak_and_wait(final_clean)
        else:
            await self._speak_and_wait("")

        # Reset state for next turn
        self._first_sentence_spoken = False
        self._sentence_buffer = ""
        self.stats.successful_turns += 1
        await self.conversation.prune_history()
        self.conversation.save_transcript()


    async def _speak_and_wait(self, text: str):
        """Speak text and wait for completion, allowing interruption."""
        self.state = SessionState.SPEAKING
        if text:
            await asyncio.to_thread(self.tts.speak, text)
        while self.tts.is_speaking():
            try:
                if self.mic.get_current_rms() > self.audio_config.wake_threshold * 2:
                    if self._active_tts_stream:
                        self._active_tts_stream.end()
                    self.tts.stop()
                    break
            except (RuntimeError, ValueError, OSError):
                pass
            await asyncio.sleep(0.1)
        self._last_tts_end_time = time.time()

    async def _shutdown(self):
        """Shutdown the voice engine."""
        self.conversation.save_transcript()

    def _banner(self) -> str:
        """Return the engine banner text."""
        return f"[bold magenta]KAEDRA MODULAR ENGINE[/bold magenta] | Model: {self.model_name}\n"
