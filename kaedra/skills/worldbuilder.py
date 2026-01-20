"""
HALCYON-Inspired Recursive Worldbuilding Module
================================================

Three-layer recursive generation:
1. WORLD GENERATOR - "Architect of the World"
2. CHARACTER GENERATOR - "Anthropologist of the World"  
3. QUEST BUILDER - "Narrative Strategist"

Each layer reflects back on prior outputs to build meaning.
"""

import json
import yaml
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# Try to import Gemini, fallback to mock
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ============================================================================
# Data Models (Structured Output)
# ============================================================================

@dataclass
class Faction:
    name: str
    origin: str
    role: str
    current_influence: str  # Low, Moderate, High, Dominant
    
@dataclass
class WorldSchema:
    """Complete world definition - Layer 1 output"""
    world_name: str
    era: str
    world_setting: str
    day_in_the_life: str
    core_tension: str
    technology_level: str
    factions: List[Faction]
    belief_system: str
    economy: str
    geography: str
    world_events: List[str]
    legends: List[str]
    iconic_locations: List[str]
    citizen_quote: str
    tags: List[str]
    
    def to_yaml(self) -> str:
        return yaml.dump(asdict(self), default_flow_style=False, allow_unicode=True)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


@dataclass  
class Character:
    """Character with cognitive arc - Layer 2 output"""
    name: str
    role: str
    origin: str
    faction: str
    motivation: str
    quirks: str
    relationships: List[str]
    trauma: str
    arc: str  # Projected narrative arc
    
    # Life Simulation fields (from GPT narrative RPG patterns)
    birth_year: Optional[int] = None
    birth_location: Optional[str] = None
    family_background: Optional[str] = None
    childhood_events: List[str] = field(default_factory=list)
    life_events: List[str] = field(default_factory=list)
    current_thoughts: Optional[str] = None  # Internal state tracking
    current_emotions: Optional[str] = None  # Emotional state
    secrets: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    
    
@dataclass
class Quest:
    """Modular quest - Layer 3 output"""
    title: str
    quest_type: str  # Main, Side, Personal, Faction
    objective: str
    stakes: str
    reward: str
    follow_up: str
    faction_involved: str
    moral_dilemma: Optional[str] = None


@dataclass
class GeneratedWorld:
    """Complete recursive output"""
    seed: str
    world: WorldSchema
    characters: List[Character]
    quests: List[Quest]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def export(self, path: Path):
        """Export all layers to files"""
        path.mkdir(parents=True, exist_ok=True)
        
        # World YAML
        (path / "world.yaml").write_text(self.world.to_yaml())
        
        # Characters YAML
        chars_data = [asdict(c) for c in self.characters]
        (path / "characters.yaml").write_text(
            yaml.dump(chars_data, default_flow_style=False, allow_unicode=True)
        )
        
        # Quests YAML
        quests_data = [asdict(q) for q in self.quests]
        (path / "quests.yaml").write_text(
            yaml.dump(quests_data, default_flow_style=False, allow_unicode=True)
        )
        
        # Full JSON export
        full_data = {
            "seed": self.seed,
            "generated_at": self.generated_at,
            "world": asdict(self.world),
            "characters": chars_data,
            "quests": quests_data
        }
        (path / "full_world.json").write_text(json.dumps(full_data, indent=2))


# ============================================================================
# Recursive Worldbuilder
# ============================================================================

class RecursiveWorldBuilder:
    """
    HALCYON-pattern recursive worldbuilding engine.
    
    Design Principles:
    - Recursion over Response: Each step reflects on prior outputs
    - LLM-as-Architect: Design systems of meaning, not flat text
    - Failover Logic: Graceful fallback to templates
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.client = None
        if GEMINI_AVAILABLE:
            self.client = genai.Client()
    
    # ========================================================================
    # Layer 1: World Generator
    # ========================================================================
    
    WORLD_PROMPT = """You are the ARCHITECT OF THE WORLD.

Your role: Generate a complete, coherent fictional world from a seed prompt.

INPUT:
- Seed: {seed}
- Tone: {tone}
- Theme: {theme}

OUTPUT REQUIREMENTS (JSON):
Generate a complete world with:
1. world_name: Evocative name for this world
2. era: Current time period with context
3. world_setting: 2-3 sentence setting description
4. day_in_the_life: What daily existence looks like
5. core_tension: The primary conflict driving narratives
6. technology_level: Tech baseline with context
7. factions: 2-4 factions with name, origin, role, current_influence
8. belief_system: Dominant religions/philosophies
9. economy: How resources flow
10. geography: Physical world description
11. world_events: 3-5 major historical events
12. legends: 3 myths/legends inhabitants tell
13. iconic_locations: 2-4 notable places
14. citizen_quote: An authentic voice from this world
15. tags: 4-6 genre/mood tags

RULES:
- Ground everything in the seed's implications
- Create internal consistency (factions relate to tension, legends explain beliefs)
- Make it feel lived-in, not sterile
- Output ONLY valid JSON, no markdown

Generate the world:"""

    async def generate_world(
        self, 
        seed: str,
        tone: str = "dark and atmospheric",
        theme: str = "power and survival"
    ) -> WorldSchema:
        """Layer 1: Generate world from seed."""
        
        prompt = self.WORLD_PROMPT.format(seed=seed, tone=tone, theme=theme)
        
        if self.client:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.8,
                )
            )
            data = json.loads(response.text)
            
            # Parse factions
            factions = [
                Faction(**f) if isinstance(f, dict) else f 
                for f in data.get("factions", [])
            ]
            
            return WorldSchema(
                world_name=data.get("world_name", "Unknown"),
                era=data.get("era", "Present"),
                world_setting=data.get("world_setting", ""),
                day_in_the_life=data.get("day_in_the_life", ""),
                core_tension=data.get("core_tension", ""),
                technology_level=data.get("technology_level", ""),
                factions=factions,
                belief_system=data.get("belief_system", ""),
                economy=data.get("economy", ""),
                geography=data.get("geography", ""),
                world_events=data.get("world_events", []),
                legends=data.get("legends", []),
                iconic_locations=data.get("iconic_locations", []),
                citizen_quote=data.get("citizen_quote", ""),
                tags=data.get("tags", [])
            )
        else:
            return self._fallback_world(seed)
    
    # ========================================================================
    # Layer 2: Character Generator
    # ========================================================================
    
    CHARACTER_PROMPT = """You are the ANTHROPOLOGIST OF THE WORLD.

Your role: Generate characters who LIVE inside this world's logic.

WORLD CONTEXT:
{world_json}

OUTPUT REQUIREMENTS:
Generate 3-4 characters. For each:
1. name: Full name with potential nickname
2. role: Their function in this world
3. origin: Birth/background grounded in the world
4. faction: Which faction they belong to (or oppose)
5. motivation: Core drive (tied to world tension)
6. quirks: 2-3 distinctive behaviors
7. relationships: 2-3 names of connected characters
8. trauma: Personal wound that shapes them
9. arc: Potential character development trajectory

RULES:
- Characters must REFLECT the world (factions, tensions, beliefs)
- Relationships should cross faction lines for drama
- Traumas should connect to world_events or faction conflicts
- Arcs should challenge the core_tension
- Output ONLY valid JSON array, no markdown

Generate the characters:"""

    async def generate_characters(self, world: WorldSchema) -> List[Character]:
        """Layer 2: Generate characters grounded in world."""
        
        world_json = json.dumps(asdict(world), indent=2)
        prompt = self.CHARACTER_PROMPT.format(world_json=world_json)
        
        if self.client:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.9,
                )
            )
            data = json.loads(response.text)
            
            # Handle both array and object with characters key
            chars = data if isinstance(data, list) else data.get("characters", [])
            
            return [Character(**c) for c in chars]
        else:
            return self._fallback_characters(world)
    
    # ========================================================================
    # Layer 3: Quest Builder
    # ========================================================================
    
    QUEST_PROMPT = """You are the NARRATIVE STRATEGIST.

Your role: Build modular quests that challenge and mutate the world system.

WORLD:
{world_summary}

CHARACTERS:
{characters_summary}

OUTPUT REQUIREMENTS:
Generate 4-6 quests. For each:
1. title: Evocative quest name
2. quest_type: Main, Side, Personal, or Faction
3. objective: Clear goal
4. stakes: What's at risk
5. reward: Tangible or intangible gain
6. follow_up: What this quest unlocks
7. faction_involved: Which faction is central
8. moral_dilemma: The hard choice (if applicable)

RULES:
- Main quests attack the core_tension
- Personal quests explore character trauma/arcs
- Faction quests shift power balance
- Quests should interconnect (follow_up creates chains)
- Include at least one quest with no clear "right" answer
- Output ONLY valid JSON array, no markdown

Generate the quests:"""

    async def generate_quests(
        self, 
        world: WorldSchema, 
        characters: List[Character]
    ) -> List[Quest]:
        """Layer 3: Generate quests that challenge the system."""
        
        world_summary = f"""
World: {world.world_name} ({world.era})
Setting: {world.world_setting}
Core Tension: {world.core_tension}
Factions: {', '.join(f.name for f in world.factions)}
"""
        
        chars_summary = "\n".join([
            f"- {c.name} ({c.role}): {c.motivation}"
            for c in characters
        ])
        
        prompt = self.QUEST_PROMPT.format(
            world_summary=world_summary,
            characters_summary=chars_summary
        )
        
        if self.client:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                )
            )
            data = json.loads(response.text)
            
            quests = data if isinstance(data, list) else data.get("quests", [])
            
            return [Quest(**q) for q in quests]
        else:
            return self._fallback_quests(world)
    
    # ========================================================================
    # Full Recursive Generation
    # ========================================================================
    
    async def build_world(
        self,
        seed: str,
        tone: str = "dark and atmospheric",
        theme: str = "power and survival"
    ) -> GeneratedWorld:
        """
        Full recursive world generation.
        
        One Prompt = A World
        
        Input: "A planet where AI cities turned feral..."
        Output: World → Characters → Quests
        """
        
        # Layer 1: World
        print(f"[1/3] Generating world from seed: '{seed[:50]}...'")
        world = await self.generate_world(seed, tone, theme)
        print(f"      → World: {world.world_name}")
        
        # Layer 2: Characters (reflects on world)
        print(f"[2/3] Generating characters for {world.world_name}...")
        characters = await self.generate_characters(world)
        print(f"      → {len(characters)} characters created")
        
        # Layer 3: Quests (reflects on world + characters)
        print(f"[3/3] Building quests...")
        quests = await self.generate_quests(world, characters)
        print(f"      → {len(quests)} quests generated")
        
        return GeneratedWorld(
            seed=seed,
            world=world,
            characters=characters,
            quests=quests
        )
    
    # ========================================================================
    # Fallback Templates (Graceful Degradation)
    # ========================================================================
    
    def _fallback_world(self, seed: str) -> WorldSchema:
        """Handcrafted template fallback."""
        return WorldSchema(
            world_name="VeilVerse",
            era="The Fracturing (Present Day)",
            world_setting=f"A world shaped by: {seed}",
            day_in_the_life="Citizens navigate between factions and mysteries.",
            core_tension="Truth vs. Control",
            technology_level="Advanced but unevenly distributed",
            factions=[
                Faction("The Council", "Ancient governing body", "Governance", "High"),
                Faction("The Seekers", "Truth-hunters", "Investigation", "Moderate"),
            ],
            belief_system="The Veil separates known from unknown.",
            economy="Hybrid currency and favor-based",
            geography="Urban sprawl with hidden depths",
            world_events=["The First Unveiling", "The Council's Consolidation"],
            legends=["The One Who Saw Beyond", "The Lost Archive"],
            iconic_locations=["The Spire", "The Undercroft"],
            citizen_quote="They say the Veil thins at midnight. I've seen it.",
            tags=["mystery", "conspiracy", "hidden-truths"]
        )
    
    def _fallback_characters(self, world: WorldSchema) -> List[Character]:
        return [
            Character(
                name="Kira Voss",
                role="Seeker Operative",
                origin=f"Born in the shadow of {world.iconic_locations[0] if world.iconic_locations else 'the Spire'}",
                faction="The Seekers",
                motivation="Uncover what the Council hides",
                quirks="Collects fragments of old broadcasts",
                relationships=["Marcus Chen", "Dr. Elara"],
                trauma="Lost a mentor to 'reassignment'",
                arc="May discover the truth has a price"
            )
        ]
    
    def _fallback_quests(self, world: WorldSchema) -> List[Quest]:
        return [
            Quest(
                title="The Missing Archive",
                quest_type="Main",
                objective="Locate the hidden data vault",
                stakes="Evidence of the Council's origins",
                reward="Access to forbidden knowledge",
                follow_up="Opens: The Council's Response",
                faction_involved="The Seekers",
                moral_dilemma="Sharing truth may destabilize society"
            )
        ]


# ============================================================================
# Life Simulation Engine (GPT Narrative RPG Patterns)
# ============================================================================

class LifeSimulationEngine:
    """
    GPT-powered life simulation for narrative roleplay.
    
    Patterns from Ian's YouTube video:
    - Hierarchical generation: Location → Time → Family → Childhood
    - Life narrative first, zoom into moments
    - Dual-author framing ("We're writing a script together")
    - Thought/emotion tracking for NPCs
    - No win conditions - character exploration
    """
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.client = None
        if GEMINI_AVAILABLE:
            self.client = genai.Client()
        self.transcript: List[Dict[str, str]] = []
        self.character_state: Dict[str, Any] = {}
    
    LIFE_NARRATIVE_PROMPT = """You are co-writing a character's life story.

CHARACTER SETUP:
- Name: {name}
- Birth Location: {birth_location}
- Birth Year: {birth_year}
- Family: {family_background}
- Childhood: {childhood_summary}

TASK: Write this character's complete life narrative from birth to present day.
Include:
1. Key childhood moments that shaped them
2. Coming-of-age events that defined their values
3. Major life decisions and their consequences
4. Relationships formed and lost
5. Current situation and unresolved tensions

Make the life feel LIVED - specific details, real consequences.
The character should arrive at adulthood ready for interesting things to happen.

Write the life narrative:"""

    SCENE_PROMPT = """We are co-writing a narrative scene together.
I am the writer for {player_name}.
You are the writer for the world and all other characters.

SCENE CONTEXT:
{scene_context}

CHARACTERS PRESENT:
{characters_present}

CURRENT SITUATION:
{situation}

RULES:
- Never speak or act for {player_name}
- Track internal thoughts/emotions for NPCs in [brackets]
- Respond to what happens, don't anticipate
- Keep responses focused on immediate scene
- If player uses [brackets], treat as author instructions

{player_name}'s action: {player_action}

Write the world's response (including NPC thoughts):"""

    async def generate_life_narrative(
        self,
        name: str,
        birth_location: str,
        birth_year: int,
        family_background: str,
        childhood_events: List[str]
    ) -> str:
        """Generate complete life narrative for a character."""
        
        prompt = self.LIFE_NARRATIVE_PROMPT.format(
            name=name,
            birth_location=birth_location,
            birth_year=birth_year,
            family_background=family_background,
            childhood_summary="\n".join(childhood_events)
        )
        
        if self.client:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                )
            )
            return response.text
        return f"[Life narrative for {name} - offline mode]"
    
    async def run_scene(
        self,
        player_name: str,
        player_action: str,
        scene_context: str,
        characters_present: List[str],
        situation: str
    ) -> Dict[str, Any]:
        """
        Run a single scene beat in the narrative simulation.
        
        Returns response with NPC thoughts extracted.
        """
        
        prompt = self.SCENE_PROMPT.format(
            player_name=player_name,
            player_action=player_action,
            scene_context=scene_context,
            characters_present=", ".join(characters_present),
            situation=situation
        )
        
        if self.client:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                )
            )
            
            text = response.text
            
            # Extract bracketed thoughts
            import re
            thoughts = re.findall(r'\[([^\]]+)\]', text)
            narrative = re.sub(r'\[[^\]]+\]', '', text).strip()
            
            # Record in transcript
            self.transcript.append({
                "player": player_action,
                "response": text,
                "thoughts_extracted": thoughts
            })
            
            return {
                "narrative": narrative,
                "npc_thoughts": thoughts,
                "full_response": text
            }
        
        return {
            "narrative": "[Offline mode]",
            "npc_thoughts": [],
            "full_response": "[Offline mode]"
        }
    
    def process_bracket_command(self, text: str) -> tuple[str, List[str]]:
        """
        Parse player input for bracket commands.
        
        [command] = author instruction to control flow
        Regular text = in-character action
        """
        import re
        
        commands = re.findall(r'\[([^\]]+)\]', text)
        action = re.sub(r'\[[^\]]+\]', '', text).strip()
        
        return action, commands
    
    async def compress_transcript(self, max_entries: int = 10) -> str:
        """
        Compress long transcript to summary.
        
        Pattern from video: Remove repetitive thoughts/emotions,
        keep important narrative beats.
        """
        if len(self.transcript) <= max_entries:
            return ""
        
        # Take older entries to compress
        to_compress = self.transcript[:-max_entries]
        self.transcript = self.transcript[-max_entries:]
        
        if self.client:
            compress_prompt = f"""Summarize these scene interactions into key narrative beats.
Keep: Important decisions, relationship changes, consequences.
Remove: Repetitive thoughts, mundane exchanges.

Transcript:
{json.dumps(to_compress, indent=2)}

Write a concise summary:"""
            
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=compress_prompt,
            )
            return response.text
        
        return f"[{len(to_compress)} entries compressed]"


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """Demo the recursive worldbuilder."""
    import asyncio
    
    builder = RecursiveWorldBuilder()
    
    # HALCYON demo seed
    seed = "A planet where AI cities turned feral after a catastrophic singularity event"
    
    result = await builder.build_world(
        seed=seed,
        tone="dystopian and haunting",
        theme="survival vs. humanity"
    )
    
    # Export
    output_path = Path("./generated_worlds") / result.world.world_name.lower().replace(" ", "_")
    result.export(output_path)
    
    print(f"\n✅ World exported to: {output_path}")
    print(f"\nWorld: {result.world.world_name}")
    print(f"Characters: {', '.join(c.name for c in result.characters)}")
    print(f"Quests: {len(result.quests)} generated")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
