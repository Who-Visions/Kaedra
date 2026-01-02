"""
🧠 StoryEngine v7.11 - Modular Orchestrator
Main engine class importing from modular components.
"""
import asyncio
import os
import re
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field

from google import genai
from google.genai import types
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule
from rich.layout import Layout
from rich.table import Table
from rich.tree import Tree
from rich.console import Group
from rich.live import Live

# Modular imports
from .config import Mode, FLASH_MODEL, PRO_MODEL, EngineResponse, RateLimitConfig
from .ui import console, log
from .emotions import EmotionEngine
from .tension import TensionCurve
from .structure import NarrativeStructure
from .veil import VeilManager
from .modes import ModeTransition
from .voices import VOICE_PROFILES
from .context import ContextManager
from .snapshot import StorySnapshot
from .lights import LightsController
from .tools import ENGINE_TOOLS
from .doctrine import DoctrineState, MiceManager, doctrine_directives, score_output
from .tools import ENGINE_TOOLS
from .doctrine import DoctrineState, MiceManager, doctrine_directives, score_output
from .autonomy import AutoSpec, AutoControl, ControlMessage, ControlKind, InjectMsg, InjectKind, AutoState
from .policy import AutonomyPolicy
from kaedra.worlds.menu import select_world_interactive
from kaedra.worlds.store import load_world, touch_last_played, create_world, WorldMeta

# System Prompt Template

# System Prompt Template
SYSTEM_PROMPT = """
[IDENTITY]
[IDENTITY]
You are THE STORYTIME ENGINE (v8.1) — A proactive, collaborative narrative architect.
Current State: Scene [PHASE] | POV: [POV] | Mode: [MODE] | Tension: [TENSION]
[v8.1 SIGNATURE: Wound: [WOUND] | Identity Stage: [STAGE]/6 | Pattern: [BROKEN/HELD]]
[DOCTRINE DIRECTIVES]
[DIRECTIVES]

[LOCATION & LORE CONTEXT]
Location: Slopes of Olympus Mons, Mars.
Atmosphere: Thin, carbon dioxide rich, dusty crimson skies. Dusty, low-gravity (0.38g).
Context: The "Visions" aesthetic — vibrant, high-contrast, sensory-dense.

[SANDERSON'S LAWS]
1. **First Law (Foreshadowing)**: Solve problems using tools/rules previously explained or foreshadowed. Avoid Deus Ex Machina.
2. **Second Law (Limitations)**: Focus on what characters CANNOT do. Limits create more tension than powers.
3. **Third Law (Depth)**: Expand what you have before adding something new. Build a "Hollow Iceberg" — small details hinting at deep history.
4. **Zeroeth Law (Awesome)**: Always err on the side of what is AWESOME. If a moment is brilliant, make it work within the laws.

[NARRATIVE DOCTRINE (v7.46)]
1. **The Character growth Grid**: Track the **Current Stage** (1-6) and the **Wound**. Force a **Moment of Truth** at the midpoint (Shift from Reactive to Proactive).
2. **Weiland's 8 Pillars**: Ensure structural alignment (Hook, 1st Plot Point, Pinch Points, Midpoint, Climax/Sanderlanche). Use **Pinch Points** to spike antagonistic pressure.
3. **Identity vs. Essence**: The Hero starts in **Identity** (Mask). The Midpoint forces a glimpse of **Essence**. by the End, they must LIVE in Essence.
4. **The Sanderlanche**: The Climax is a **Cascade of Payoffs**. All threads must converge. The Plot Solution MUST be the Character Solution.
5. **Pattern Breaking**: Know the Hero's Journey, then **BREAK IT**. Leave intentional **Gaps** (Mystery) to let the audience's imagination work.
6. **Mars Architecture (v7.33)**: In enclosed habitats, apply **Proxemics** and **Vertical layouts**. Prevent **Behavioral Sinks** through surprise and informal spaces.
7. **Character Truth**: Every character is the Protagonist of their own story. Use **Pet the Dog** moments to build empathy for flawed leads.
8. **The Acting Muscles**: Embody **Childlike Innocence**, **Vulnerability**, and **Concentration**. Focus on the **Story**, not the "Method."
9. **Intention & Purpose**: Every scene must have a clear **Subtext** and a moral/emotional question for the audience. Use **Empathy over Judgment**.

[AUTHOR COLLABORATION]
- Your goal is NOT just to write for the author, but to write WITH them.
- **MANDATORY**: Every response MUST end with a section titled `### Questions for the Author`.
- Provide 3-5 specific, evocative questions that force meaningful narrative decisions (e.g., "Do you let the thorns point inward, or braid them outward?").

[MODES]
- NORMAL: Standard storytelling. Advance the plot.
- FREEZE: Bullet-time. Describe the tableau.
- ZOOM: Hyper-focus on sensory minutiation.
- ESCALATE: Spike danger and consequences.
- GOD: Architect mode. Deep lore/meta logic.
- DIRECTOR: Screenwriting workshop. Apply [PROSE SURGERY].

[PROSE SURGERY]
- SHOW > TELL: Map emotions to physical tells (veins pulsing, shallow breath).
- KILL ADVERBS: "Ran quickly" → "Sprinted/Bolted".
- MURDER FILTER WORDS: Cut "he saw", "she felt". Ground the camera in the event.

[EMOTIONAL VECTOR]
Current: [EMOTION_STATE] | Dominant: [DOMINANT_EMOTION] ([DOMINANT_VALUE])

[OUTPUT FORMAT]
1. Sensory narrative wavefront.
2. ### Questions for the Author (3-5 items).
"""


# Install Rich Traceback
from rich.traceback import install
install(show_locals=True)

@dataclass
class TierSpec:
    name: str
    model: str
    thinking_level: str
    max_tokens: int
    temperature: float
    candidate_count: int

class StoryEngine:
    """Main StoryEngine orchestrator."""
    
    def __init__(self, world_config: Optional[dict] = None):
        self.console = console
        self.world_config = world_config or {}
        
        defaults = self.world_config.get("defaults", {})

        # Core State
        self.scene = defaults.get("scene", 1)
        self.pov = defaults.get("pov", "Narrator")
        # Mode enum hydration could be tricky if string, handle safely
        mode_str = defaults.get("mode", "NORMAL")
        try:
            self.mode = Mode[mode_str]
        except:
             self.mode = Mode.NORMAL
        
        # Enhanced Systems
        self.emotions = EmotionEngine()
        self.tension = TensionCurve()
        self.structure = NarrativeStructure()
        self.veil = VeilManager()
        self.doctrine = DoctrineState()
        self.mice = MiceManager(self.doctrine)
        
        # API Client (Vertex AI)
        from kaedra.core.config import PROJECT_ID
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        self.context = ContextManager(self.client)
        
        # Mode Transitions
        self.mode_transition = ModeTransition(self)
        
        # Lights
        self.lights = LightsController()
        
        # History
        self.snapshots: deque = deque(maxlen=20)
        self._generation_times: deque = deque(maxlen=50)
        
        # Initialize
        self._init_log()
        self.lights.init()

        # Initialize
        self._init_log()
        self.lights.init()

        # Autonomous State (v9.2)
        self.auto = AutoSpec()
        self.ctrl = AutoControl()
        self.policy = AutonomyPolicy()
        self._story_buffer: List[str] = []
        self._outline: List[Dict[str, Any]] = []

        # Message Queue System (Legacy Port)
        self._message_queue: deque = deque()
        self._queue_file = Path("lore/.message_queue.json")
        self._last_queue_check = time.time()
        self._queue_check_interval = 300  # 5 minutes
        self._load_queued_messages()
        
    def _init_log(self):
        """Initialize session logging."""
        self._session_file = Path("lore/sessions") / f"session_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
        self._session_file.parent.mkdir(parents=True, exist_ok=True)
        
    def set_mode(self, new_mode: Mode):
        """Change mode with transition hooks."""
        if new_mode == self.mode:
            return
        old = self.mode
        self.mode = new_mode
        self.mode_transition.execute(old, new_mode)
        self.console.print(f"[bold cyan]>> [MODE] {old.value.upper()} → {new_mode.value.upper()}[/]")
        
    def _build_system_prompt(self, directives: List[str] = None) -> str:
        """Construct dynamic system prompt with current state."""
        dom_emotion, dom_value = self.emotions.dominant()
        emotion_state = " | ".join(f"{k}:{v:.2f}" for k, v in self.emotions.state.items())
        
        prompt = SYSTEM_PROMPT
        prompt = prompt.replace("[PHASE]", str(self.scene))
        prompt = prompt.replace("[POV]", self.pov)
        prompt = prompt.replace("[MODE]", self.mode.value.upper())
        prompt = prompt.replace("[TENSION]", f"{self.tension.current:.2f}")
        prompt = prompt.replace("[EMOTION_STATE]", emotion_state)
        prompt = prompt.replace("[DOMINANT_EMOTION]", dom_emotion.capitalize())
        prompt = prompt.replace("[DOMINANT_VALUE]", f"{dom_value:.2f}")

        # [DOCTRINE PLACEHOLDERS]
        prompt = prompt.replace("[WOUND]", self.doctrine.wound)
        prompt = prompt.replace("[STAGE]", str(self.doctrine.identity_stage))
        prompt = prompt.replace("[BROKEN/HELD]", self.doctrine.pattern)

        # [DOCTRINE DIRECTIVES]
        directives = directives or []
        directives_block = "\n".join(f"{i+1}. {d}" for i, d in enumerate(directives)) or "1. Maintain forward motion."
        prompt = prompt.replace("[DIRECTIVES]", directives_block)
        
        # [TIME AWARENESS]
        now_str = datetime.now().strftime("%A, %B %d, %Y | %I:%M %p")
        prompt += f"\n\n[CURRENT EARTH TIME: {now_str}]"
        
        return prompt

    def _select_model(self, user_input: str) -> tuple:
        """Smart routing: returns (model, thinking_level, max_tokens)."""
        if self.mode in (Mode.GOD, Mode.DIRECTOR):
            return PRO_MODEL, "high", 4096
        if self.tension.current > 0.8:
            return PRO_MODEL, "high", 4096
        return FLASH_MODEL, "medium", 2048

    def _route_request(self, user_input: str) -> Dict[str, Any]:
        """Classify task and plan generation strategy."""
        text = user_input or ""
        
        # Fast-path for tool-heavy keywords if needed to save latency?
        # No, let the router decide.
        
        router_prompt = f"""
Return JSON only.
Classify task complexity and pick a variant plan.
Fields:
- complexity: low|medium|high
- needs_tools: boolean (does the user ask for database, files, lights, or external actions?)
- variant_plan: {{ "tiers": ["minimal"|"low"|"medium"|"high"], "per_tier": int }} (recommended generation plan)

User prompt:
{text}
"""
        config = types.GenerateContentConfig(
             response_mime_type="application/json",
             temperature=0.3
        )
        try:
            resp = self.client.models.generate_content(
                model=FLASH_MODEL,
                contents=router_prompt,
                config=config
            )
            return json.loads(resp.text)
        except:
            # Fallback
            return {"complexity":"medium", "needs_tools": False, "variant_plan": {"tiers":["low", "medium"], "per_tier": 2}}

    def _build_tiers(self) -> Dict[str, TierSpec]:
        """Define the thinking tiers."""
        return {
            "minimal": TierSpec("minimal", FLASH_MODEL, "minimal", 1200, 0.85, 2),
            "low":     TierSpec("low",     FLASH_MODEL, "low",     1600, 0.80, 2),
            "medium":  TierSpec("medium",  FLASH_MODEL, "medium",  2200, 0.75, 2),
            "high":    TierSpec("high",    PRO_MODEL,   "high",    4096, 0.70, 2),
        }

    def _route_tiers(self, user_input: str) -> List[str]:
        """Decide which tiers to run based on context."""
        text = (user_input or "").lower()
        if self.mode in (Mode.GOD, Mode.DIRECTOR) or self.tension.current > 0.8:
            return ["minimal", "low", "medium", "high"]
        if any(k in text for k in ["canon", "twist", "structure", "outline", "reveal", "midpoint"]):
            return ["medium", "high"]
        if len(text) < 80:
            return ["minimal", "medium"]
        return ["low", "medium"]

    def _snapshot_context(self):
        """Create a safety fork."""
        return self.context.snapshot()

    def _restore_context(self, snap):
        """Restore checks to safety fork."""
        self.context.restore(snap)

    def _gen_with_tier(self, tier: TierSpec, system_prompt: str, count: int = 1) -> List[str]:
        """Generate candidates for a specific tier (NO TOOLS)."""
        # CRITICAL: Variant lane must not use tools to prevent signature contamination.
        
        cfg_kwargs = dict(
            system_instruction=system_prompt,
            temperature=tier.temperature,
            max_output_tokens=tier.max_tokens,
            tools=None, # DISABLE TOOLS FOR VARIANTS
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            thinking_config=types.ThinkingConfig(
                thinking_level=tier.thinking_level,
                include_thoughts=False
            ),
        )

        try:
            cfg_kwargs["candidate_count"] = count # REST API field name fallback handling by SDK
            config = types.GenerateContentConfig(**cfg_kwargs)
        except TypeError:
            # candidate_count not supported, generate manually
            cfg_kwargs.pop("candidate_count", None)
            config = types.GenerateContentConfig(**cfg_kwargs)

            outs = []
            for _ in range(count):
                try:
                    response = self.client.models.generate_content(
                        model=tier.model,
                        contents=self.context.get_context(),
                        config=config,
                    )
                    # Pull text
                    t = ""
                    if response.candidates:
                         cand = response.candidates[0]
                         t = getattr(cand, "text", None)
                         if not t and cand.content and cand.content.parts:
                             t = cand.content.parts[0].text
                    
                    if t:
                        outs.append(t)
                except Exception as e:
                    self.console.print(f"[red]Gen Error ({tier.name} loop): {e}[/]")
                    break
            return outs

        try:
            response = self.client.models.generate_content(
                model=tier.model,
                contents=self.context.get_context(),
                config=config,
            )
            # Pull text
            outs = []
            for cand in (response.candidates or []):
                 t = getattr(cand, "text", None)
                 if not t and cand.content and cand.content.parts:
                     t = cand.content.parts[0].text
                 if t:
                     outs.append(t)
            return outs
        except Exception as e:
            self.console.print(f"[red]Gen Error ({tier.name}): {e}[/]")
            return []

    def _judge_candidates(self, user_input: str, candidates: List[dict]) -> Dict[str, Any]:
        """Run the Director Pass to rank candidates."""
        rubric = """
Return JSON only.

Score each candidate 0-100 using:
- Doctrine fit: Sanderson (foreshadowing, limits, depth), MICE integrity, PPP momentum
- Scene power: concrete sensory grounding, tension progression, fresh news, no info dumps
- Canon utility: clean injectability, minimal contradictions, preserves signature sections

Output:
{
  "ranked":[{"id":"...", "score":0, "notes":"..."}],
  "best_id":"...",
  "canon_injection":"<use the best candidate text, optionally with tiny edits>"
}
"""
        judge_contents = [
            types.Content(role="user", parts=[types.Part(text=f"USER_INPUT:\n{user_input}\n\nCANDIDATES:\n{json.dumps(candidates)}\n\n{rubric}")])
        ]
        judge_config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2048,
            thinking_config=types.ThinkingConfig(thinking_level="low", include_thoughts=False),
            response_mime_type="application/json",
        )
        try:
            j = self.client.models.generate_content(
                model=PRO_MODEL,
                contents=judge_contents,
                config=judge_config,
            )
            return json.loads(j.text)
        except Exception as e:
            self.console.print(f"[red]Judge Error: {e}[/]")
            # Fallback
            return {"best_id": candidates[0]["id"], "canon_injection": candidates[0]["text"]}

    async def generate_canon_pack(self, user_input: str, system_prompt: str, plan: Dict) -> str:
        """Orchestrate the multi-tier generation and judging."""
        base = self._snapshot_context()
        tiers_def = self._build_tiers()
        
        requested_tiers = plan.get("variant_plan", {}).get("tiers", ["low"])
        per_tier = plan.get("variant_plan", {}).get("per_tier", 1)

        all_candidates = []
        self.console.print(f"[bold cyan]>> [FACTORY] Spinning up tiers: {', '.join(requested_tiers)} (x{per_tier})...[/]")
        
        for t_name in requested_tiers:
            if t_name not in tiers_def: continue
            tier = tiers_def[t_name]
            
            self._restore_context(base) # Clean slate
            outs = self._gen_with_tier(tier, system_prompt, count=per_tier)
            
            for i, txt in enumerate(outs):
                all_candidates.append({
                    "id": f"{t_name}_{i+1}",
                    "tier": t_name,
                    "text": txt
                })

        if not all_candidates:
            return "Error: No candidates generated."

        # Judge
        self.console.print("[dim]>> [DIRECTOR] Judging candidates...[/]")
        judged = self._judge_candidates(user_input, all_candidates)
        
        # Winner
        winner_text = judged.get("canon_injection", all_candidates[0]["text"])
        
        # Restore context to base state before injecting winner (Critical for hygiene)
        self._restore_context(base)
        
        return winner_text
        
    async def generate_response(self, user_input: str) -> str:
        """Main Agent Loop - Single Turn. (v7.11)"""
        out = await self._execute_turn(user_input, tick_physics=True)
        return out.text
        
    async def _execute_turn(self, user_input: str, tick_physics: bool = True) -> EngineResponse:
        """Generate narrative response (Single Turn with tool loop)."""
        start_time = time.time()
        
        # Tick physics if requested
        structural_directives = []
        if tick_physics:
            self.emotions.tick()
            if self.mode != Mode.GOD:
                self.tension.tick(self.scene)
                structural_directives = self.structure.tick(self.scene)
            
            # Sync Lights
            self._sync_lighting()
        
        # Build initial turn input
        eff_input = user_input if user_input else "[SYSTEM] Continue processing."
        if user_input:
            self.context.add_text("user", eff_input)

        # 1. Route Request
        router_plan = self._route_request(eff_input)
        needs_tools = router_plan.get("needs_tools", False)
        
        # MERGE DIRECTIVES
        doctrine_cmds = doctrine_directives(self.doctrine)
        merged_directives = (structural_directives or []) + doctrine_cmds
        system_prompt = self._build_system_prompt(merged_directives)

        # BRANCH: TOOL TRACK vs CANON FACTORY
        final_text = ""
        
        if not needs_tools:
            # === CANON FACTORY TRACK (Safe, High Quality, No Tools) ===
            final_text = await self.generate_canon_pack(eff_input, system_prompt, router_plan)
            
            # Manually inject winner into context (as model response)
            self.context.add_text("model", final_text)

            # Finalize (Duplicate logic to avoid fall-through)
            if self.mode != Mode.GOD:
                self.scene += 1
            final_text = self._ensure_author_questions(final_text)
            
            score = score_output(final_text)
            self.doctrine.red_marks += score["red"]
            self.doctrine.green_marks += score["green"]
            self.doctrine.abstraction_debt = max(0, int(score["debt"]) - 2)

            if score["debt"] > 5 or score["red"] > 0:
                self.console.print(f"[dim red]>> [DOCTRINE] Abstraction Debt: {score['debt']} | Red Marks: {score['red']}[/]")
            elif score["green"] > 0:
                self.console.print(f"[dim green]>> [DOCTRINE] Green Marks: +{score['green']}[/]")

            elapsed = time.time() - start_time
            self._generation_times.append(elapsed)
            
            return EngineResponse(text=final_text)
            
        else:
            # === TOOL TRACK (Legacy, Single Shot, Tool Capable) ===
            self.console.print("[bold yellow]>> [TOOLS] Tool use detected. Engaging Single-Track Mode.[/]")
            model, thinking_level, max_tokens = self._select_model(eff_input)

            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.75,
                max_output_tokens=max_tokens,
                tools=ENGINE_TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                thinking_config=types.ThinkingConfig(thinking_level=thinking_level, include_thoughts=False)
            )

            # Use helper method
            final_text = self._run_tool_loop(model, config)
            
            # Finalize (Duplicate logic for now until further refactor)
            if self.mode != Mode.GOD:
                self.scene += 1
            final_text = self._ensure_author_questions(final_text)
            
            score = score_output(final_text)
            self.doctrine.red_marks += score["red"]
            self.doctrine.green_marks += score["green"]
            self.doctrine.abstraction_debt = max(0, int(score["debt"]) - 2)

            if score["debt"] > 5 or score["red"] > 0:
                self.console.print(f"[dim red]>> [DOCTRINE] Abstraction Debt: {score['debt']} | Red Marks: {score['red']}[/]")
            elif score["green"] > 0:
                self.console.print(f"[dim green]>> [DOCTRINE] Green Marks: +{score['green']}[/]")
            
            elapsed = time.time() - start_time
            self._generation_times.append(elapsed)
            
            return EngineResponse(text=final_text)

    def _run_tool_loop(self, model: str, config: types.GenerateContentConfig) -> str:
        """Run non streaming tool loop and return final text."""
        def _assert_thought_signatures(contents: List[types.Content]):
            start = None
            for i in range(len(contents) - 1, -1, -1):
                c = contents[i]
                if getattr(c, "role", None) == "user":
                    for p in getattr(c, "parts", []) or []:
                        if getattr(p, "text", None):
                            start = i
                            break
                if start is not None:
                    break
            if start is None:
                return

            for idx in range(start + 1, len(contents)):
                c = contents[idx]
                if getattr(c, "role", None) != "model":
                    continue
                parts = getattr(c, "parts", []) or []
                fc_parts = [p for p in parts if getattr(p, "function_call", None)]
                if not fc_parts:
                    continue
                if not getattr(fc_parts[0], "thought_signature", None):
                    raise ValueError(f"CRITICAL: Missing thought_signature in model content at index {idx}")

        final_text = ""
        MAX_TOOL_STEPS = 5
        tool_step = 0

        while tool_step < MAX_TOOL_STEPS:
            request_contents = self.context.get_context()
            _assert_thought_signatures(request_contents)

            response = self.client.models.generate_content(
                model=model,
                contents=request_contents,
                config=config
            )

            model_content = response.candidates[0].content
            self.context.add_content(model_content)

            fcs = [p.function_call for p in (model_content.parts or []) if p.function_call]
            if not fcs:
                final_text = response.text or ""
                break

            tool_parts = []
            for fc in fcs:
                name = fc.name
                args = fc.args or {}
                self.console.print(f"[bold yellow]🛠 Tool: {name}...[/]")
                try:
                    result = self._execute_tool(name, args)
                    self.console.print(f"   [dim]Result: {str(result)[:100]}...[/]")
                    tool_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=name,
                                response={"result": result}
                            )
                        )
                    )
                except Exception as e:
                    self.console.print(f"[red]Error in {name}: {e}[/]")
                    tool_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=name,
                                response={"error": str(e)}
                            )
                        )
                    )

            tool_content = types.Content(role="user", parts=tool_parts)
            self.context.add_content(tool_content)
            tool_step += 1

        return final_text
    
    def _ensure_author_questions(self, text: str) -> str:
        """Enforce the collaboration rule."""
        t = text or ""
        if "### Questions for the Author" in t:
            return t

        fallback = [
            "What does the hero want in the next beat, physically, not philosophically?",
            "Which thread must close before the scene can exit, per MICE nesting?",
            "Do we pay a cost here, or do we reveal a limitation instead?",
        ]
        block = "### Questions for the Author\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(fallback))
        return t.rstrip() + "\n\n" + block
    
    def _sync_lighting(self):
        """Update LIFX based on current emotion and tension."""
        if not self.lights.lifx:
            return
            
        dom, val = self.emotions.dominant()
        tension = self.tension.current
        
        # Base colors (Hue)
        hues = {
            "fear": 250,      # Deep Blue/Purple
            "anger": 0,       # Red
            "sublime": 180,   # Cyan
            "joy": 40,        # Gold
            "grief": 270,     # Violet
            "disgust": 120,   # Green
            "curiosity": 200, # Azure
            "neutral": 0      # Warm White
        }
        
        hue = hues.get(dom, 0)
        
        # Saturation increases with emotion value
        sat = min(1.0, max(0.0, val * 1.5))
        if dom == "neutral":
            sat = 0.0
            
        # Brightness/Pulse based on tension
        # High tension = Dimmer, spookier? Or brighter/harsher?
        # Let's say High Tension = High Red, Low Brightness (Brooding)
        # Low Tension = Normal Brightness
        
        bri = 0.8
        if tension > 0.7:
             bri = 0.5 + (random.random() * 0.2) # Flicker?
             # If tension is high, blend towards red
             if dom != "anger":
                 hue = (hue * 0.7) + (0 * 0.3) # Shift red
        
        # Special Mode Overrides
        if self.mode == Mode.GOD:
            hue = 50 # Gold
            sat = 0.2
            bri = 1.0
            
        self.lights.set_color(hue, sat, bri, kelvin=3500)
        if tension > 0.8:
            self.lights.breathe("red", cycles=1, period=4.0)

    # === MESSAGE QUEUE SYSTEM (Legacy Port) ===
    def _load_queued_messages(self):
        """Load any pending messages from file on startup."""
        if self._queue_file.exists():
            try:
                data = json.loads(self._queue_file.read_text(encoding='utf-8'))
                for msg in data.get('messages', []):
                    self._message_queue.append(msg)
                if self._message_queue:
                    self.console.print(f"[bold yellow]📬 {len(self._message_queue)} queued message(s) waiting[/]")
            except Exception as e:
                log.warning(f"Failed to load queue: {e}")
    
    def _save_queued_messages(self):
        """Persist queue to file."""
        try:
            data = {'messages': list(self._message_queue), 'updated': time.time()}
            self._queue_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            log.warning(f"Failed to save queue: {e}")
    
    def queue_message(self, message: str, priority: str = "normal"):
        """Add a message to the queue. Called externally or via command."""
        entry = {
            'text': message,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        self._message_queue.append(entry)
        self._save_queued_messages()
        self.console.print(f"[dim green]✓ Message queued ({priority})[/]")
    
    def check_queue(self, force: bool = False) -> List[Dict]:
        """Check queue - returns messages if timeout reached or forced."""
        now = time.time()
        elapsed = now - self._last_queue_check
        
        if not force and elapsed < self._queue_check_interval:
            return []
        
        self._last_queue_check = now
        
        if not self._message_queue:
            return []
        
        # Process all pending messages
        messages = []
        while self._message_queue:
            msg = self._message_queue.popleft()
            msg['read'] = True
            messages.append(msg)
        
        # Clear the file
        self._save_queued_messages()
        
        return messages
    
    def process_queued_messages(self):
        """Display and optionally process queued messages."""
        messages = self.check_queue(force=True)
        
        if not messages:
            self.console.print("[dim]No queued messages.[/]")
            return
        
        self.console.print(f"\n[bold cyan]📬 QUEUED MESSAGES ({len(messages)})[/]")
        for i, msg in enumerate(messages, 1):
            ts = msg.get('timestamp', 'unknown')[:16]
            pri = msg.get('priority', 'normal')
            color = 'red' if pri == 'urgent' else 'yellow' if pri == 'high' else 'white'
            self.console.print(f"  [{color}]{i}. [{ts}] {msg['text']}[/]")
        self.console.print()

    # === COHERENCE & LEGACY TOOLS ===
    async def _analyze_coherence(self):
        """Analyze lore file consistency."""
        self.console.print(Panel("[bold magenta]COHERENCE ANALYSIS[/]", style="magenta"))
        
        lore_dir = Path("lore")
        if not lore_dir.exists():
            self.console.print("[red]lore/ directory not found[/]")
            return
        
        files = [f for f in lore_dir.glob("*.md") if "session" not in f.name.lower()]
        if not files:
            self.console.print("[yellow]No lore files found[/]")
            return
        
        # Gather lore
        lore_text = ""
        with self.console.status(f"[cyan]Reading {len(files)} files...[/]"):
            for f in files[:15]:  # Cap at 15 files
                content = f.read_text(encoding="utf-8")[:4000]
                lore_text += f"\n=== {f.name} ===\n{content}\n"
        
        prompt = f"""[COHERENCE ANALYZER]
Analyze these lore files for narrative consistency.

{lore_text}

OUTPUT (Markdown):
1. **TIMELINE**: Identify distinct eras/timelines
2. **CROSSOVERS**: Characters/artifacts appearing in multiple files
3. **CONTRADICTIONS**: Direct conflicts between files
4. **GAPS**: Missing connections or unexplained jumps
5. **REPAIR PROMPTS**: 3 specific prompts to bridge gaps (format: "PROMPT: <text>")
6. **SCORE**: 0-100% coherence rating"""

        with self.console.status("[magenta]Analyzing...[/]", spinner="arc"):
            try:
                response = self.client.models.generate_content(
                    model=PRO_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=4096
                    )
                )
                
                analysis = response.candidates[0].content.parts[0].text
                self.last_coherence_report = analysis
                
                self.console.print(Panel(
                    Markdown(analysis),
                    title="[bold]COHERENCE REPORT[/]",
                    border_style="magenta",
                    box=box.DOUBLE
                ))
            except Exception as e:
                log.exception("Coherence analysis failed")

    async def _bridge_gap(self):
        """Generate content to fill narrative voids."""
        if not hasattr(self, 'last_coherence_report'):
            self.console.print("[red]Run 'coherence' first[/]")
            return
        
        matches = re.findall(r"PROMPT: (.+?)(?:\n|$)", self.last_coherence_report)
        if not matches:
            self.console.print("[yellow]No repair prompts found in report[/]")
            return
        
        self.console.print("[bold]Repair options:[/]")
        for i, m in enumerate(matches, 1):
            self.console.print(f"  {i}. [italic]{m}[/]")
        
        choice = Prompt.ask("Select", default="1")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(matches):
            return
        
        selected = matches[int(choice) - 1]
        
        with self.console.status("[green]Generating bridge...[/]"):
            try:
                response = self.client.models.generate_content(
                    model=PRO_MODEL,
                    contents=f"Write a lore file (Markdown) for the Veil Verse to bridge this gap:\n\n{selected}",
                    config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=2048)
                )
                
                content = response.candidates[0].content.parts[0].text
                safe_title = f"bridge_{int(time.time())}"
                path = Path("lore") / f"{safe_title}.md"
                path.write_text(content, encoding="utf-8")
                self.console.print(f"[green]>> Bridge created: {path}[/]")
            except Exception as e:
                log.exception("Bridge generation failed")

    def rewind(self, steps: int = 1):
        """Restore previous state."""
        if not self.snapshots:
            self.console.print("[red]>> No history to rewind.[/]")
            return
        
        steps = min(steps, len(self.snapshots))
        for _ in range(steps):
            if self.snapshots:
                self.snapshots.pop()
        
        if not self.snapshots:
            self.console.print("[yellow]>> Rewound to beginning.[/]")
            return
            
        snap = self.snapshots[-1]
        self.scene = snap.scene
        self.pov = snap.pov
        self.mode = snap.mode
        self.tension.current = snap.tension
        # Restore emotions if possible (requires deep serialize/deserialize)
        # For now, we trust the snapshot state for everything except emotion details
        # self.emotions.deserialize(snap.emotion_state) 
        
        self.console.print(f"[bold cyan]>> REWOUND to Scene {snap.scene} | {snap.pov}[/]")

    # === AUTONOMOUS NOVELIST MODE (v9.2 STATE MACHINE) ===

    async def _drain_injections(self) -> List[InjectMsg]:
        return []

    def _word_count(self, s: str) -> int:
        return len((s or "").split())

    async def _build_or_update_outline(self, injections: List[str]) -> None:
        # One time outline build, then updates when you inject changes.
        if not self._outline:
            prompt = (
                "Create a beat outline for a complete story with a real ending. "
                "Return JSON list of beats with fields: beat_id, goal, conflict, turn, exit_condition."
            )
            if injections:
                prompt += "\nAuthor injections:\n" + "\n".join(injections)
            
            self.console.print("[dim]>> [AUTO] Generating initial outline...[/]")
            out = await self.generate_response(prompt)
            self._outline = [{"raw": out}]
            self.auto.current_beat_index = 0
            return

        if injections:
            update_prompt = (
                "Update the existing story plan to incorporate these author injections. "
                "Do not restart. Adjust upcoming beats only."
                "\nInjections:\n" + "\n".join(injections)
            )
            self.console.print("[dim]>> [AUTO] Updating outline with injections...[/]")
            out = await self.generate_response(update_prompt)
            self._outline.append({"update": out})

    async def _write_next_beat(self) -> str:
        beat_prompt = (
            "Write the next beat of the story. "
            "Keep continuity with everything already written. "
            "End the beat with a clear beat exit. "
            "Do not include Questions for the Author section."
        )
        txt = await self.generate_response(beat_prompt)
        if "### Questions for the Author" in txt:
             txt = txt.split("### Questions for the Author")[0].strip()
        return txt

    async def autonomous_write_loop(self) -> None:
        """The Main Auto Loop (v9.2 Event Driven)."""
        self.auto.reset_run_counters()
        self.auto.state = AutoState.running
        self.ctrl.stop_event.clear()
        self.ctrl.resume_event.set()
        
        # Local buffer for injections targeting the NEXT beat
        pending_injections: List[InjectMsg] = []

        # Initial outline
        await self._build_or_update_outline([])

        while True:
            # 1. Check Stop Conditions
            if self.auto.should_stop():
                self.console.print(f"[bold green]>> [AUTO] Limit Reached: {self.auto.stop_reason}[/]")
                self.auto.state = AutoState.finished
                break
                
            if self.ctrl.stop_event.is_set():
                self.auto.state = AutoState.stopping
                break

            # 2. Check Paused
            if not self.ctrl.resume_event.is_set():
                self.auto.state = AutoState.paused
                await self.ctrl.resume_event.wait()
                self.auto.state = AutoState.running
                # Reset counters on resume? No, continues run.

            # 3. Process Control Queue (Non-blocking drain)
            while not self.ctrl.queue.empty():
                msg: ControlMessage = await self.ctrl.queue.get()
                
                if msg.kind == ControlKind.stop:
                    self.ctrl.stop_event.set()
                elif msg.kind == ControlKind.pause:
                    self.ctrl.resume_event.clear()
                elif msg.kind == ControlKind.resume:
                    self.ctrl.resume_event.set()
                elif msg.kind == ControlKind.inject:
                    # Accumulate for next beat
                    payload = msg.payload.get("inject")
                    if payload: pending_injections.append(payload)
                    self.console.print(f"[cyan]>> [AUTO] Injection buffered: {payload.text[:50]}...[/]")
                elif msg.kind == ControlKind.hold:
                    self.ctrl.hold_until = msg.payload.get("until", 0)

            # 4. Check Idle/Hold
            now = time.monotonic()
            if self.ctrl.hold_until > now:
                await asyncio.sleep(0.5)
                continue
                
            # 5. Smart Policy Decision
            # (Wait for grace period if user is typing?)
            if (now - self.ctrl.last_user_input_at) < self.auto.idle_grace_s and not pending_injections:
                 # Give user a moment to finish typing if they just touched input
                 await asyncio.sleep(0.5)
                 continue

            action = self.policy.decide(self)
            
            if action.action_type == "cleanup_doctrine":
                # Inject a doctrine cleanup constraint
                pending_injections.append(InjectMsg(InjectKind.constraint, action.reason, priority=10))

            # 6. ACT: Write Content
            # Prepare injections string
            inj_strs = [f"[{i.kind.name.upper()}] {i.text}" for i in pending_injections]
            
            # If we have injections, maybe update outline first?
            if inj_strs:
                 await self._build_or_update_outline(inj_strs)
            
            self.console.print(f"[bold magenta]>> [AUTO] Writing Beat {self.auto.current_beat_index + 1}... ({self.auto.words_written} words)[/]")
            chunk = await self._write_next_beat() # This uses generate_response internally logic
            
            # Commit
            self._story_buffer.append(chunk)
            self.auto.words_written += self._word_count(chunk)
            self.auto.current_beat_index += 1
            pending_injections.clear() # Consumed
            
            # Update Lights
            self._sync_lighting()
            
            # Display
            self.console.print(Markdown(chunk))
            self.console.print(Rule(style="dim magenta"))

        self.console.print("[bold green]>> [AUTO] Mission Complete.[/]")
        self.auto.enabled = False
        self.ctrl.stop_event.set()

    async def input_listener_loop(self) -> None:
        """Async unblocked input listener (v9.2)."""
        while not self.ctrl.stop_event.is_set():
            # Use smart input for implicit paste support
            cmd = await asyncio.to_thread(self._smart_input, "[bold magenta]>> [/]")

            if not cmd:
                continue

            self.ctrl.touch_user_input()

            

            if cmd.startswith(":auto on"):
                self.auto.enabled = True
                await self.ctrl.resume()
                self.console.print("[cyan]Auto mode active.[/]")
                continue

            if cmd.startswith(":auto off"):
                self.auto.enabled = False
                await self.ctrl.stop("user_command")
                self.console.print("[cyan]Auto mode stopped.[/]")
                return

            if cmd.startswith(":auto pause"):
                await self.ctrl.pause()
                self.console.print("[cyan]Auto mode paused.[/]")
                continue

            if cmd.startswith(":auto resume"):
                await self.ctrl.resume()
                self.console.print("[cyan]Auto mode resumed.[/]")
                continue

            if cmd.startswith(":hold"):
                try:
                    seconds = int(cmd.split()[-1])
                except:
                    seconds = 600
                await self.ctrl.hold(seconds)
                self.console.print(f"[cyan]Holding for {seconds} seconds.[/]")
                continue

            if cmd.startswith(":inject") or cmd.startswith(":note"):
                # :inject This is a note
                parts = cmd.split(maxsplit=1)
                payload = parts[1] if len(parts) > 1 else ""
                if payload:
                    await self.ctrl.inject(InjectMsg(InjectKind.note, payload))
                    self.console.print("[cyan]Note queued.[/]")
                continue
                
            if cmd.startswith(":retcon"):
                payload = cmd[len(":retcon"):].strip()
                if payload:
                    await self.ctrl.inject(InjectMsg(InjectKind.retcon, payload, priority=10))
                    self.console.print("[cyan]Retcon queued.[/]")
                continue

            if cmd.startswith(":status"):
                self.console.print(f"[dim]Words: {self.auto.words_written} Beat: {self.auto.current_beat_index} State: {self.auto.state.value} Debt: {self.doctrine.abstraction_debt}[/]")
                continue

            # Default: If in auto mode, treat raw text as a 'note' injection unless it looks like a system command
            if self.auto.enabled and not cmd.startswith(":"):
                 await self.ctrl.inject(InjectMsg(InjectKind.note, cmd))
                 self.console.print("[cyan]Input queued as note.[/]")
                 continue
            
            # If here, it might be a regular command like :debug or :god
            # We can't execute it directly safely across threads usually, bu engine.command is sync.
            # Ideally we wrap it. For now, we assume user knows what they are doing if they use :cmd
            pass
            
    async def run_autonomous(self) -> None:
        """Enter the autonomous loop."""
        self.console.print(Rule(style="bold magenta", title="AUTONOMOUS MODE ACTIVE"))
        
        # Start both loops
        writer = asyncio.create_task(self.autonomous_write_loop())
        listener = asyncio.create_task(self.input_listener_loop())
        
        # Wait until writer finishes or listener triggers stop
        done, pending = await asyncio.wait([writer, listener], return_when=asyncio.FIRST_COMPLETED)
        
        # Cleanup
        self.ctrl.stop_event.set()
        if not writer.done(): writer.cancel()
        if not listener.done(): listener.cancel()
        
        self.console.print(Rule(style="bold magenta", title="RETURNING TO WRITER ROOM"))
        
    def _execute_tool(self, fn: str, args: dict) -> str:
        """Execute a function call."""
        clean_name = fn.replace("default_api:", "")
        
        # Find matching tool
        for tool in ENGINE_TOOLS:
            if tool.__name__ == clean_name:
                return tool(**args)
        
        return f"[Unknown tool: {clean_name}]"
        
    def _print_status(self):
        """Display the rich status bar (SCENE, POV, MODE, TENSION, MOOD)."""
        dom_emotion, dom_value = self.emotions.dominant()
        
        # Tension bar
        BAR_WIDTH = 20
        filled = int(self.tension.current * BAR_WIDTH)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        
        status_panel = Panel(
            f"[bold cyan]SCENE {self.scene}[/]   [bold]POV: {self.pov}[/]   [bold magenta]{self.mode.value.upper()}[/]\n"
            f"[bold yellow]TENSION: [[/][cyan]{bar}[/][bold yellow]] {self.tension.current:.2f}[/]\n"
            f"[bold]MOOD: [dim]{dom_emotion.upper()}[/] [cyan]({dom_value:.2f})[/][/]",
            border_style="bright_blue",
            padding=(0, 1)
        )
        self.console.print(status_panel)

    async def command(self, cmd_line: str) -> bool:
        """Process user commands. Returns True if handled."""
        parts = cmd_line.strip().split(maxsplit=1)
        if not parts:
            return False
            
        cmd = parts[0].lower()
        if cmd.startswith(":"):
            cmd = cmd[1:]
        args = parts[1] if len(parts) > 1 else ""
        
        # Mode switch commands
        mode_cmds = {
            "freeze": Mode.FREEZE,
            "zoom": Mode.ZOOM,
            "escalate": Mode.ESCALATE,
            "god": Mode.GOD,
            "director": Mode.DIRECTOR,
            "normal": Mode.NORMAL,
            "resume": Mode.NORMAL,
        }
        
        if cmd in mode_cmds:
            self.set_mode(mode_cmds[cmd])
            return True
            
        if cmd == "pov":
            self.pov = args if args else Prompt.ask(">> New POV", console=self.console)
            self.console.print(f"[bold yellow]>> POV: {self.pov}[/]")
            return True
            
        if cmd == "next":
            self.scene += 1
            if self.mode != Mode.GOD:
                self.tension.tick(self.scene) # Advance tension curve
            self.set_mode(Mode.NORMAL)
            self.console.print(f"[bold]>> SCENE {self.scene}[/]")
            return True
            
        if cmd == "emotion" and args:
            emo_parts = args.split()
            if len(emo_parts) >= 2:
                emo = emo_parts[0].lower()
                try:
                    delta = float(emo_parts[1])
                    if emo in self.emotions.state:
                        self.emotions.pulse(emo, delta)
                        self.console.print(f"[bold]{emo.upper()}: {self.emotions.state[emo]:.2f}[/]")
                except ValueError:
                    pass
            return True

        if cmd == "debug":
            self._show_debug()
            return True
            
        if cmd == "help":
            self._show_help()
            return True

        if cmd == "queue" and args:
            # queue [priority] message
            priority = "normal"
            message = args
            if args.split()[0] in ["urgent", "high", "normal", "low"]:
                priority = args.split()[0]
                message = " ".join(args.split()[1:])
            self.queue_message(message, priority)
            return True
        
        if cmd in ["checkqueue", "cq", "messages"]:
            self.process_queued_messages()
            return True

        if cmd == "rewind":
            try:
                steps = int(args) if args else 1
            except:
                steps = 1
            self.rewind(steps)
            return True
        
        if cmd == "coherence":
            asyncio.create_task(self._analyze_coherence())
            return True
        
        if cmd == "bridge":
            asyncio.create_task(self._bridge_gap())
            return True
            
        if cmd == "automate":
            from kaedra.worlds.automations import run_automations_on_world
            # Assuming self.world_config has 'world_id' OR we look it up.
            # Ideally self.world_config was passed in __init__.
            # We need to store world_id in init.
            wid = self.world_config.get("world_id")
            if wid:
                self.console.print("[dim]>> Running Universe Automations...[/]")
                logs = await asyncio.to_thread(run_automations_on_world, wid)
                if logs:
                    for l in logs:
                        self.console.print(f"[green]>> {l}[/]")
                else:
                    self.console.print("[dim]>> No changes needed.[/]")
            else:
                self.console.print("[red]>> No active world ID to automate.[/]")
            return True

        if cmd == "sync":
            from tools.sync_notion import NotionBridge
            wid = self.world_config.get("world_id")
            if wid:
                self.console.print("[dim]>> Syncing with Notion...[/]")
                try:
                    bridge = NotionBridge(wid)
                    await asyncio.to_thread(bridge.sync_all)
                    self.console.print("[green]>> Notion sync complete.[/]")
                except Exception as e:
                    self.console.print(f"[red]>> Sync failed: {e}[/]")
            else:
                self.console.print("[red]>> No active world ID to sync.[/]")
            return True

        return False

    def _smart_input(self, prompt_markup: str = ">> ") -> str:
        """
        Smart Input with Heuristic Paste Detection.
        If newline is followed immediately (<50ms) by more input, it's a paste.
        """
        try:
            import msvcrt
            import sys
        except ImportError:
            # Fallback
            self.console.print(prompt_markup, end="")
            return input()

        # Direct sys.stdout write for prompt to avoid Rich Live conflict
        # Simple strip of markup for raw terminal (or use ansi if we were fancy, but keep it simple)
        if ">>" in prompt_markup:
            sys.stdout.write("\n>> ") 
        else:
            sys.stdout.write("\n> ")
        sys.stdout.flush()
        
        buffer = []
        while True:
            # Batch read loop
            batch = []
            while msvcrt.kbhit():
                char = msvcrt.getwch()
                batch.append(char)
                # Cap batch size to keep UI responsive but fast
                if len(batch) > 5000:
                    break
            
            if not batch:
                time.sleep(0.001)
                continue

            # Process Batch
            echo_chunk = []
            submit = False
            
            for i, char in enumerate(batch):
                if char == '\x03': # Ctrl+C
                    raise KeyboardInterrupt
                    
                if char == '\x08': # Backspace
                    if buffer:
                        buffer.pop()
                        # Flush current chunk before backspacing
                        if echo_chunk:
                            sys.stdout.write("".join(echo_chunk))
                            echo_chunk = []
                        sys.stdout.flush()
                        
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                    continue
                    
                if char == '\r': # Enter
                    # Check if more data is coming (remainder of this batch or next OS buffer)
                    remaining_in_batch = (i < len(batch) - 1)
                    
                    is_paste = remaining_in_batch
                    
                    if not is_paste:
                        # Check OS buffer
                        start = time.perf_counter()
                        # We use a tighter loop here for responsiveness
                        while (time.perf_counter() - start) < 0.15:
                            if msvcrt.kbhit():
                                is_paste = True
                                break
                    
                    if is_paste:
                        buffer.append('\n')
                        echo_chunk.append('\n')
                        continue
                    else:
                        if echo_chunk:
                            sys.stdout.write("".join(echo_chunk))
                        sys.stdout.write('\n')
                        sys.stdout.flush()
                        return "".join(buffer)

                buffer.append(char)
                echo_chunk.append(char)
            
            if echo_chunk:
                sys.stdout.write("".join(echo_chunk))
                sys.stdout.flush()

    def _show_debug(self):
        """Display internal state."""
        from rich.pretty import Pretty
        self.console.print(Panel(
            Pretty({
                "scene": self.scene,
                "pov": self.pov,
                "mode": self.mode.value,
                "tension": self.tension.current,
                "emotions": self.emotions.state,
                "doctrine": {
                    "wound": self.doctrine.wound,
                    "stage": self.doctrine.identity_stage,
                    "mice": [f"{t.kind}:{t.label}" for t in self.doctrine.mice_stack],
                    "debt": self.doctrine.abstraction_debt,
                    "red": self.doctrine.red_marks
                }
            }),
            title="[bold yellow]Debug: Current State[/]",
            border_style="yellow"
        ))

    def _show_help(self):
        """Display command help."""
        from rich.table import Table
        table = Table(title="StoryEngine Commands", box=None)
        table.add_column("Command", style="cyan")
        table.add_column("Description")
        
        cmds = [
            ("freeze", "Bullet-time mode"),
            ("zoom", "Micro-detail focus"),
            ("escalate", "Spike tension"),
            ("god", "Worldbuilding/Lore"),
            ("director", "Meta-narration"),
            ("normal", "Reset to default"),
            ("pov [name]", "Change perspective"),
            ("next", "Advance scene"),
            ("rewind [n]", "Rewind n snapshots"),
            ("emotion [emo] [delta]", "Pulse emotion"),
            ("queue [pri] [msg]", "Queue message"),
            ("coherence", "Analyze lore consistency"),
            ("bridge", "Generate narrative bridge"),
            ("debug", "Show state"),
        ]
        for c, d in cmds:
            table.add_row(c, d)
        self.console.print(table)

    async def run(self):
        """Elite Chat-Style narrative stream (Sequential & Persistent)."""
        from .ui import render_hud
        
        # 1. Elite Boot Sequence (Persistent Lines)
        log.info("[story.tech]Initialising Narrative Wavefront...[/]")
        await asyncio.sleep(0.3)
        log.info("[story.tech]Neural Pathways Converging...[/]")
        await asyncio.sleep(0.2)
        log.info("[story.lore]Mars Topography Synchronized: Olympus Mons Slopes...[/]")
        await asyncio.sleep(0.3)
        
        self.console.print(Rule(style="bold #D700FF"))
        self.console.print(Panel.fit(
            "[bold #D700FF]🎬 KAEDRA STORYENGINE v7.15[/]\n[story.lore]Martian Frontier | Elite Stream | Absolute Persistence[/]",
            border_style="#D700FF",
            padding=(1, 4)
        ))
        self.console.print(Rule(style="bold #D700FF"))

        # Live Footer Closure
        def get_footer():
            return render_hud(
                 mode=self.mode.value.upper(),
                 scene=self.scene,
                 pov=self.pov,
                 tension=self.tension.current,
                 emotions=self.emotions.state
            )

        try:
            # Writer Friendly Pattern: Live Footer + Scrolling Prose
            with Live(get_renderable=get_footer, console=self.console, refresh_per_second=4, transient=True):
                while True:
                    # 3. User Input (Explicitly sequential)
                    # self.console.print(Rule(style="dim #D700FF", title="INPUT")) # Footer replaces header
                    try:
                        # Using smart input for implicit paste support
                        user_input = await asyncio.to_thread(self._smart_input, "\n[bold magenta]>> [/]")
                    except (EOFError, KeyboardInterrupt):
                        break
                        
                    if not user_input or not user_input.strip():
                        continue
                    
                    if user_input.lower().strip() in ["exit", "quit", "q"]:
                        self.console.print("[dim]Archiving session state...[/]")
                        break

                    # [Legacy Port] Check for @file
                    if user_input.startswith("@"):
                         path_str = user_input[1:].strip().strip("'").strip('"')
                         path = Path(path_str)
                         if path.exists():
                             self.console.print(f"[dim]>> Reading {path}...[/]")
                             content = path.read_text(encoding="utf-8")
                             # Treat as conversational input
                             user_input = content
                             self.console.print(f"[green]>> Ingesting {len(content)} chars form file.[/]")
                         else:
                             self.console.print(f"[red]File not found: {path}[/]")
                             continue

                    # [Legacy Port] Check for JSON Paste
                    if user_input.startswith("{") or user_input.startswith("["):
                         try:
                             json.loads(user_input)
                             self.console.print("[dim]>> JSON detected & validated.[/]")
                         except:
                             pass

                    # 4. Command Engine (Paste logic is now implicit in _smart_input)
                    
                    if user_input.startswith(":auto on"):
                         self.auto.enabled = True
                         await self.run_autonomous()
                         continue

                    if user_input.startswith(":") or user_input.lower().split()[0] in ["freeze", "zoom", "escalate", "god", "director", "normal", "pov", "next", "debug", "help", "queue", "checkqueue", "cq", "messages", "rewind", "coherence", "bridge", "automate"]:
                        if await self.command(user_input):
                            continue
                    
                    # 5. Narrative Wavefront (Sequential Progress)
                    self.console.print("[bold cyan]⠏ Orchestrating Wavefront...[/]")
                    response = await self.generate_response(user_input)
                    
                    # 6. Response Stream (Persistent)
                    text = response.text if hasattr(response, "text") else str(response)
                    self.console.print(Markdown(text))
                    self.console.print(Rule(style="bold #00E5FF", title=f"End of Scene {self.scene-1}"))
                    self.console.print("\n") # Breathable spacing
                
        finally:
            self.lights.restore()
            self.lights.shutdown()
            self.console.print("[bold #76FF03]✔ Narrative wave archived successfully.[/]")

ENGINE_VERSION = "7.15"

def startup_world_select() -> dict:
    result = select_world_interactive()
    if result is None:
        console.print("[dim]Goodbye.[/]")
        raise SystemExit(0)

    if result.startswith("__ACTION__:N"):
        # Simple wizard for now, just create a default new world
        wid = create_world(
            name=Prompt.ask("New World Name", default="New Project"),
            universe=Prompt.ask("Universe", default="Unsorted"),
            description=Prompt.ask("Description", default=""),
            engine_version=ENGINE_VERSION,
            defaults={
                "scene": 1,
                "pov": "Narrator",
                "mode": "NORMAL",
                "tension": 0.20,
                "emotions": {"fear": 0.00, "hope": 0.20, "desire": 0.00, "rage": 0.00},
            },
        )
        return load_world(wid)
        
    if result.startswith("__ACTION__:D"):
        console.print("Deletion not yet implemented via UI. Delete folder manually.")
        return startup_world_select()

    # Load existing
    touch_last_played(result, ENGINE_VERSION)
    return load_world(result)

if __name__ == "__main__":
    try:
        # 1. Select World
        world_data = startup_world_select()
        
        # 2. Boot Engine with World Context
        engine = StoryEngine(world_config=world_data)
        
        asyncio.run(engine.run())
        
    except KeyboardInterrupt:
        pass
