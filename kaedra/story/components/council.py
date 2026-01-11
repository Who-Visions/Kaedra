import asyncio
import aiohttp
import json
import random
from pathlib import Path
from typing import List, Optional, Any, Dict

from google.genai import types
from rich.console import Console

from kaedra.story.config import FLASH_MODEL

class CouncilManager:
    """Manages the Fleet Review and Democratic Voting protocols."""

    def __init__(self, client, console: Console, retry_policy=None, lights=None):
        self.client = client
        self.console = console
        self.retry_policy = retry_policy
        self.lights = lights

    async def run_session(self, history: List[Any], focus: str = None) -> None:
        """Invoke The Fleet for critique and evaluation (Karpathy llm-council Protocol)."""
        fleet_path = Path("kaedra/config/fleet.json")
        if not fleet_path.exists():
            # Fallback path logic or just fail gracefully
             if Path("kaedra/story/config/fleet.json").exists(): # speculative
                 fleet_path = Path("kaedra/story/config/fleet.json")
             else:
                 self.console.print("[red]>> Fleet configuration not found.[/]")
                 return

        try:
            with open(fleet_path, "r", encoding="utf-8") as f:
                fleet_data = json.load(f)
        except Exception as e:
             self.console.print(f"[red]>> Fleet config error: {e}[/]")
             return

        members = fleet_data.get("board_members", [])
        self.console.print(f"\n[bold yellow]📡 ACTIVATING THE BOARD: {fleet_data.get('fleet_name')}[/]")
        self.console.print(f"[dim]Focus: {focus or 'Narratological Audit (Jahn/Bork)'}[/]\n")

        # [LIGHTS] Set The Board Atmosphere
        if self.lights:
            self.console.print("[dim]>> [LIGHTS] Setting Board Atmosphere (Fire 25% + Flame)...[/]")
            self.lights.fire_mode(brightness=0.25)

        # Gather context
        context_text = ""
        for turn in history:
            if isinstance(turn, dict):
                role = turn.get("role", "user")
                parts = turn.get("parts", [])
                text = " ".join([p.get("text", "") for p in parts])
                context_text += f"{role.upper()}: {text}\n"
            else:
                # Assuming Content object (google.genai.types.Content)
                # handle turn.parts which is list of Part objects
                for part in turn.parts:
                    if hasattr(part, 'text') and part.text:
                        context_text += f"{turn.role.upper()}: {part.text}\n"

        opinions = {}
        
        # --- STAGE 1: FIRST OPINIONS ---
        self.console.print("[bold cyan]STAGE 1: GATHERING INDIVIDUAL CRITIQUES (FLASH)[/]")
        stage1_config = types.GenerateContentConfig(
            temperature=0.7,
            thinking_config=types.ThinkingConfig(thinking_level="minimal", include_thoughts=False)
        )

        async with aiohttp.ClientSession() as session:
            for member in members:
                if self.lights and member.get("color"):
                    self.lights.breathe(color=member["color"], cycles=1, period=1.0)
                
                critique = None
                with self.console.status(f"[bold cyan]{member['name']} is thinking...[/]", spinner="dots"):
                    if not member.get("endpoint"):
                        # Local Simulation
                        prompt = f"""
                        [AGENT: {member['name']} | ROLE: {member['role']}]
                        TASK: Conduct a NARRATOLOGICAL AUDIT (Jahn V6.0).
                        
                        PROTOCOL:
                        1. FCD Intent: What is the creative intelligence doing?
                        2. Focalization: OV, PIV, or DIV?
                        3. Audio/Visual Code: Diegetic vs Nondiegetic?
                        4. S/Z Codes: ACT, HER, SYM, SEM, REF.
                        5. Goof Audit: Logic or continuity slips?
                        
                        CONTEXT:
                        {context_text}
                        
                        Provide a sharp 2-3 sentence audit.
                        """
                        async def _local_gen():
                             resp = await asyncio.to_thread(
                                self.client.models.generate_content, 
                                model=FLASH_MODEL, contents=prompt, config=stage1_config
                             )
                             return resp.text.strip()

                        try:
                            if self.retry_policy:
                                critique = await self.retry_policy.execute_async(_local_gen)
                            else:
                                critique = await _local_gen()
                        except Exception as e:
                            critique = "Failed to simulate."
                    else:
                        # Remote Cloud Run call
                        async def _remote_gen():
                             session_focus = focus or "Lexia Analysis (S/Z Codes)"
                             payload = {"context": context_text, "focus": session_focus, "agent_id": member["id"]}
                             async with session.post(member["endpoint"], json=payload, timeout=12) as r:
                                 if r.status != 200: raise Exception(f"Error {r.status}")
                                 data = await r.json()
                                 return data.get("response", "No response.")

                        try:
                            if self.retry_policy:
                                critique = await self.retry_policy.execute_async(_remote_gen)
                            else:
                                critique = await _remote_gen()
                        except Exception as e:
                            critique = f"Connection failed: {e}"
                
                opinions[member['id']] = {"name": member['name'], "role": member['role'], "text": critique}
                self.console.print(f"   [green]✅ {member['name']} submitted critique.[/]")


        # --- STAGE 2: DEMOCRATIC VOTING ---
        self.console.print("\n[bold magenta]STAGE 2: DEMOCRATIC VOTING & RANKING (FLASH)[/]")
        
        judges_ids = ["dav1d", "unk", "kam"]
        judges = [m for m in members if m['id'] in judges_ids]
        
        id_to_agent = {f"AGENT_{i+1}": mid for i, mid in enumerate(opinions.keys())}
        anonymized_block = "\n".join([f"{tag}: {opinions[mid]['text']}" for tag, mid in id_to_agent.items()])

        stage2_config = types.GenerateContentConfig(
            temperature=0.5,
            thinking_config=types.ThinkingConfig(thinking_level="low", include_thoughts=False)
        )

        for judge in judges:
            if self.lights and judge.get("color"):
                self.lights.breathe(color=judge["color"], cycles=1, period=1.0)

            self.console.print(f"[dim]>> Judge {judge['name']} is deliberating...[/]")
            vote_prompt = f"""
            [JUDGE: {judge['name']} | ROLE: {judge['role']}]
            DEMOCRATIC COUNCIL PROTOCOL (NAACL 2025).
            
            COUNCIL OPINIONS:
            {anonymized_block}
            
            STORY CONTEXT:
            {context_text}
            
            TASK:
            1. RANK: List the top 3 (e.g., RANKING: AGENT_X, AGENT_Y, AGENT_Z).
            2. ANALYSIS: Briefly why #1 is superior.
            3. BIAS CHECK: Note if any agent seems to be "yes-ma'aming" or hallucinating.
            """
            
            vote_text = ""
            with self.console.status(f"[bold magenta]{judge['name']} is casting ballot...[/]", spinner="aesthetic"):
                for attempt in range(5):
                    try:
                        resp = await asyncio.to_thread(
                            self.client.models.generate_content, 
                            model=FLASH_MODEL, 
                            contents=vote_prompt,
                            config=stage2_config
                        )
                        vote_text = resp.text.strip()
                        if vote_text: break
                    except:
                        await asyncio.sleep(1)

            self.console.print(Panel(vote_text, title=f"[bold]{judge['name']}'s Ballot[/]", border_style=judge.get("color", "white")))
            self.console.print("\n")
