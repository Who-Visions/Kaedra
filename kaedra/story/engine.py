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
    
    def __init__(self):
        self.console = console
        
        # Core State
        self.scene = 1
        self.pov = "Narrator"
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
            # If candidate_count is not supported by installed definition, we can't use it easily without loop
            # Fallback to single generation
            del cfg_kwargs["candidate_count"]
            config = types.GenerateContentConfig(**cfg_kwargs)
            # Todo: implement manual loop if critical. For now we accept single.

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
        
        # Update scene
        if self.mode != Mode.GOD:
            self.scene += 1
        
        # Ensure Author Questions
        final_text = self._ensure_author_questions(final_text)
                
        # Post-Turn Doctrine Scoring (Update State)
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

    def command(self, cmd_line: str) -> bool:
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
            
        return False

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
            ("emotion [emo] [delta]", "Pulse emotion"),
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

        try:
            while True:
                # 2. HUD Line (Sequential Status)
                hud = render_hud(
                    mode=self.mode.value.upper(),
                    scene=self.scene,
                    pov=self.pov,
                    tension=self.tension.current,
                    emotions=self.emotions.state
                )
                self.console.print(hud)
                
                # 3. User Input (Explicitly sequential)
                self.console.print(Rule(style="dim #D700FF", title="INPUT"))
                try:
                    # Using council.input for maximum reliability in input visibility
                    user_input = self.console.input("[bold magenta]>> [/]")
                except (EOFError, KeyboardInterrupt):
                    break
                    
                if not user_input or not user_input.strip():
                    continue
                
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    self.console.print("[dim]Archiving session state...[/]")
                    break
                
                # 4. Command Engine
                if user_input.startswith(":") or user_input.lower().split()[0] in ["freeze", "zoom", "escalate", "god", "director", "normal", "pov", "next", "debug", "help"]:
                    if self.command(user_input):
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

if __name__ == "__main__":
    engine = StoryEngine()
    try:
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        pass
