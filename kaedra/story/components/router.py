import json
from typing import Dict, Any, List, Optional
from google.genai import types
from kaedra.story.config import FLASH_MODEL

class EngineRouter:
    """Handles intent routing and structured planning."""

    def __init__(self, client):
        self.client = client

    def route(self, user_input: str) -> Dict[str, Any]:
        """Classify task and plan generation strategy."""
        text = user_input or ""
        
        router_prompt = f"""
Return JSON only.

Decide what the user actually wants right now.

intents:
- "plan": give build steps, structure, options, questions. NO scene prose.
- "scene": write the next scene or beat in narrative form.
- "research": gather facts or lore (usually needs tools).
- "command": user is issuing an engine command.

Rules:
1) If the user input is short (under 120 chars) AND lacks an explicit verb like
   write, scene, go, action, screenplay, continue, draft,
   then intent MUST be "plan".
2) If the user includes "write" or "scene" or "go" or "action", intent is "scene".
3) If the user asks to pull from Notion, files, databases, or "lore bible", intent is "research" and needs_tools true.
4) Output must include:
   - intent: plan|scene|research|command
   - should_write_scene: boolean
   - needs_tools: boolean
   - variant_plan: {{ "tiers": ["minimal"|"low"|"medium"|"high"], "per_tier": int }}

User input:
{text}
"""
        config = types.GenerateContentConfig(
             response_mime_type="application/json",
             temperature=0.1,
             thinking_config=types.ThinkingConfig(thinking_level="low", include_thoughts=False),
        )
        try:
            resp = self.client.models.generate_content(
                model=FLASH_MODEL,
                contents=router_prompt,
                config=config
            )
            j = json.loads(resp.text)

            # Hard safety fallback if router is sloppy
            intent = j.get("intent", "plan")
            should_write = bool(j.get("should_write_scene", False))
            if intent != "scene":
                should_write = False

            j["intent"] = intent
            j["should_write_scene"] = should_write
            if "variant_plan" not in j:
                j["variant_plan"] = {"tiers": ["low"], "per_tier": 1}
            return j
        except Exception:
            return {
                "intent": "plan",
                "should_write_scene": False,
                "needs_tools": False,
                "variant_plan": {"tiers": ["low"], "per_tier": 1},
            }

    async def create_plan(self, user_input: str, system_prompt: str, plan: Dict) -> str:
        """Generate structured build steps (Planner Mode)."""
        planner_prompt = f"""
You are in PLANNER MODE.
Do NOT write narrative prose.
Return a practical build plan the author can execute.

Output format (Markdown):
1) Interpretation (1 to 2 sentences)
2) What we need to define next (5 to 9 bullets)
3) Canon seed pack (facts to lock) (3 to 7 bullets)
4) Options (A, B, C) with risks
5) Next actions (numbered, concrete)
6) Questions for the Author (3 to 5)

User input:
{user_input}
"""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt + "\n\n" + "[MODE OVERRIDE]\nPLANNER MODE ONLY.",
            temperature=0.4,
            max_output_tokens=1200,
            thinking_config=types.ThinkingConfig(thinking_level="low", include_thoughts=False),
        )
        
        # Async wrap if needed, though client.models.generate_content is actually sync in some versions.
        # But engine.py treated it as sync-in-async. 
        # Wait, in engine.py: `resp = self.client.models.generate_content(...)` was mocked as sync call primarily.
        # But `_fleet_review` used `await asyncio.to_thread`.
        # `_planner_response` in current engine.py is defined as `async` but calls `self.client` synchronously without await.
        # This blocks the event loop! Good thing I'm refactoring.
        # I should use `asyncio.to_thread` here to be safe.
        
        import asyncio
        resp = await asyncio.to_thread(
             self.client.models.generate_content,
             model=FLASH_MODEL,
             contents=[types.Content(role="user", parts=[types.Part(text=planner_prompt)])],
             config=config,
        )
        return (resp.text or "").strip()
