"""
⛓️ StoryChainer - Gemini Cookbook Pattern
Implements Premise -> Outline -> Beat -> Scene chaining.
Pattern: https://github.com/google-gemini/cookbook/blob/main/examples/Story_Writing_with_Prompt_Chaining.ipynb
"""
from google.genai import types
from kaedra.core.config import get_gemini_client
from kaedra.story.config import FLASH_MODEL, PRO_MODEL
from kaedra.story.ui import log

class StoryChainer:
    def __init__(self, console=None):
        self.client = get_gemini_client()
        self.console = console

    async def chain_generation(self, user_input: str, system_prompt: str) -> str:
        """Runs the full chaining pipeline."""
        log.info("Starting Story Chaining Pipeline...")
        
        # 1. Premise Expansion
        premise = await self._generate_step(
            "Expand this into a 1-sentence gripping premise.",
            user_input, 
            system_prompt,
            temp=0.7
        )
        if self.console: self.console.print(f"[dim cyan]Premise: {premise}[/]")

        # 2. Outline Creation
        outline = await self._generate_step(
            f"Write a 5-beat narrative outline for this premise: {premise}",
            "",
            system_prompt,
            temp=0.4
        )
        if self.console: self.console.print(f"[dim cyan]Outline Generated ({len(outline)} chars)[/]")

        # 3. Collaborative Scene Generation (The Loop)
        story_draft = ""
        beats = outline.split("\n")
        
        for i, beat in enumerate(beats[:3]): # Start with 3 beats to avoid context explosion
            if not beat.strip(): continue
            
            context_so_far = story_draft if story_draft else 'Beginning of the story.'
            beat_prose = await self._generate_step(
                f"Write the next scene based on this beat: {beat}\n\nOutline: {outline}"
                f"\n\nStory so far:\n{context_so_far}",
                "",
                system_prompt,
                temp=0.8,
                model=PRO_MODEL # Use Pro for high-fidelity prose
            )
            story_draft += f"\n\n{beat_prose}"
            if self.console: self.console.print(f"[dim green]Beat {i+1} complete.[/]")

        return story_draft.strip()

    async def _generate_step(self, instruction: str, content: str, system_prompt: str, 
                             temp: float = 0.7, model: str = FLASH_MODEL) -> str:
        prompt = f"{instruction}\n\n{content}"
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temp,
            thinking_config=types.ThinkingConfig(thinking_budget=1024, include_thoughts=True)
        )
        
        response = self.client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=config
        )
        return response.text or ""
