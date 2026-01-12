"""
LoreEditor - Interactive Command for Rich Notion Editing
Ensures content generation is grounded in existing lore (RAG).
Integrates Smart Router for Model Tiering (Flash/Pro + Thinking).
"""
import sys
import time
from dataclasses import dataclass
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from kaedra.story.tools.notion import get_entity, update_page_content, search_universe, list_universe_pages, NotionService

# Config & Types
try:
    from google import genai
    from google.genai import types
    from kaedra.core.config import PROJECT_ID
    # Fallback constants if config file missing
    FLASH_MODEL = "gemini-2.0-flash-exp"
    PRO_MODEL = "gemini-2.0-pro-exp"
except ImportError:
    genai = None
    types = None
    PROJECT_ID = None

@dataclass
class TierSpec:
    name: str
    model: str
    thinking_level: str # 'minimal', 'low', 'medium', 'high'
    description: str

class LoreEditor:
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.tiers = {
            "minimal": TierSpec("minimal", FLASH_MODEL, "minimal", "Fast Draft (Flash)"),
            "low":     TierSpec("low",     FLASH_MODEL, "low",     "Standard Draft (Flash)"),
            "medium":  TierSpec("medium",  FLASH_MODEL, "medium",  "Thoughtful Expansion (Flash)"),
            "high":    TierSpec("high",    FLASH_MODEL, "high",    "Deep Reasoning (Flash)"),
            "ultra":   TierSpec("ultra",   PRO_MODEL,   "high",    "Maximum Intelligence (Pro)"),
        }

        # Initialize Vertex Client for Drafting
        if genai:
            try:
                self.client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
            except Exception as e:
                self.console.print(f"[red]Warning: Client init failed: {e}[/]")
                self.client = None
        else:
            self.client = None
            self.console.print("[red]Warning: gemini/vertex not loaded. Drafting will be simulated.[/]")

    def run(self, entity_name: str = None):
        """Main Interactive Loop."""
        self.console.clear()
        self.console.print("[bold cyan]📚 Kaedra Lore Editor (Smart Router Enabled)[/]")

        # 1. Select Entity
        if not entity_name:
            entity_name = Prompt.ask("Enter Entity Name (or '?' for list)", default="The Shadow Blade")

        if entity_name == "?":
            self.console.print(list_universe_pages())
            entity_name = Prompt.ask("Enter Entity Name", default="The Shadow Blade")

        # 2. Rich View (The "Read" Phase)
        self.console.print(f"\n[dim]Fetching '{entity_name}'...[/]")
        content = get_entity(entity_name)

        if "not found" in content.lower() and "Error" in content:
            self.console.print(f"[red]{content}[/]")
            return

        self.console.print(Panel(Markdown(content), title=f"📄 {entity_name}", border_style="cyan"))

        # 3. Expansion Loop
        while True:
            action = Prompt.ask(
                "\n[bold]Action[/]",
                choices=["expand", "refine", "search", "quit"],
                default="expand"
            )

            if action == "quit":
                break

            if action == "search":
                q = Prompt.ask("Search query")
                res = search_universe(q)
                self.console.print(Panel(res, title=f"Search: {q}"))
                continue

            if action == "expand":
                self._handle_expansion(entity_name, content)


    def _handle_expansion(self, entity_name: str, current_content: str):
        """Grounded drafting workflow with Tier Selection."""
        topic = Prompt.ask("What do you want to add? (e.g. 'Origin story about the Void')")

        # Tier Selection
        tier_choice = Prompt.ask(
            "Select Intelligence Tier",
            choices=list(self.tiers.keys()),
            default="medium"
        )
        tier = self.tiers[tier_choice]

        # A. Context Retrieval (RAG Lite)
        self.console.print("[dim]🔎 Checking for related lore...[/]")
        # (Future: Semantic Search)

        # B. Draft Generation
        self.console.print(f"[bold yellow]✍️ Drafting with {tier.name.upper()} ({tier.model} | Thinking: {tier.thinking_level})...[/]")

        prompt = f"""
You are a Lore Keeper for the VeilVerse.
Your goal is to WRITE A NEW SECTION for the page '{entity_name}'.

Current Content:
{current_content}

User Instruction:
{topic}

Rules:
1. CONSISTENCY: Do not contradict the Current Content.
2. STYLE: Cinematic, high-biotech/magic hybrid (Arcane-Cyberpunk).
3. FORMAT: Use Markdown (## Headers, **Bold** keys).
4. GROUNDING: Only use established lore. If you introduce a new concept, mark it as [New Lore].

Output ONLY the new content block.
"""
        new_text = self._generate_text(prompt, tier)

        # C. Review
        self.console.print("\n[bold]Proposed Addition:[/]")
        title_lines = f"Draft ({tier.name.upper()})"
        self.console.print(Panel(Markdown(new_text), title=title_lines, style="yellow"))

        # D. Commit
        if Confirm.ask("Append this to Notion?", default=True):
            res = update_page_content(entity_name, new_text)
            self.console.print(f"[green]{res}[/]")

            # Update local state?
            # current_content += "\n\n" + new_text # Ideally, but string is immutable
            # For simpler loop, we can just say "Done".

    def _generate_text(self, prompt: str, tier: TierSpec) -> str:
        if not self.client:
            return "[Mock] Generated content about " + prompt[:20] + "..."

        try:
            # Configure Thinking
            config = types.GenerateContentConfig(
                temperature=0.7,
                thinking_config=types.ThinkingConfig(
                    thinking_level=tier.thinking_level,
                    include_thoughts=False # Thoughts hidden for final output, but model uses them
                )
            )

            resp = self.client.models.generate_content(
               model=tier.model,
               contents=prompt,
               config=config
            )
            return resp.text
        except Exception as e:
            return f"[Error generating with {tier.model}: {e}]"

if __name__ == "__main__":
    editor = LoreEditor()
    editor.run()
