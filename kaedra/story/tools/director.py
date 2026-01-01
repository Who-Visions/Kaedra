"""
StoryEngine Director Tools
Screenwriting guidance and frameworks.
"""
import json

def consult_director(topic: str) -> str:
    """Get screenwriting guidance on: structure, world, character, twist, polish, prose."""
    topic_norm = (topic or "").strip().lower()
    topic_norm = topic_norm.replace(" ", "_")
    topic_norm = topic_norm.replace("-", "_")

    # [1] ALIASES: Map common human terms to internal keys
    ALIASES = {
        "three_act": "structure",
        "3_act": "structure",
        "act_structure": "structure",
        "hero_goal_sequences": "edson_structure",
        "edson": "edson_structure",
        "hgs": "edson_structure",
        "weiland": "weiland_8_beats",
        "8_pillars": "weiland_8_beats",
        "sanderson": "sanderson_laws",
        "sanderson_laws": "sanderson_laws",
        "ppp": "ppp_promise_progress_payoff",
        "promise_progress_payoff": "ppp_promise_progress_payoff",
        "mice": "mice_quotient",
        "mice_quotient": "mice_quotient",
        "gap": "gap_tension",
        "mystery_box": "gap_tension",
        "naming": "fantastical_naming",
        "sanderlanche": "sanderlanche",
        "climax": "sanderlanche",
        "payoff_convergence": "sanderlanche",
        "identity": "identity_vs_essence",
        "essence": "identity_vs_essence",
        "choice": "choice_crossroads",
        "crossroads": "choice_crossroads",
        "pet_the_dog": "pet_the_dog",
        "kindness": "pet_the_dog",
    }
    
    # Resolve alias if present
    topic_norm = ALIASES.get(topic_norm, topic_norm)

    frameworks = {
        "structure": """[DIRECTOR: 3-ACT STRUCTURE]
Analyze current narrative position:
- **Act 1** (Setup): 6 Hero Goal Sequences. Inciting incident, stunning surprise 1.
- **Act 2** (Confrontation): 12 Hero Goal Sequences (6/6). Midpoint reversal, stunning surprise 2.
- **Act 3** (Resolution): 3 Hero Goal Sequences. Climax, character growth payoff.
Map the current story to the 21-Sequence Grid.""",

        "edson_structure": """[DIRECTOR: HERO GOAL SEQUENCES]
- **The 21 Grid**: Ensure the story hits 21 distinct units of action.
- **Act 1**: 6 sequences.
- **Act 2**: 12 sequences (6 pre-midpoint, 6 post-midpoint).
- **Act 3**: 3 sequences.
- *Check: Are we repeating a sequence type? Every sequence needs unique Fresh News.*""",

        "world": """[DIRECTOR: WORLDBUILDING]
Apply Sanderson's 3rd Law: Expand > Add.
- **Micro-Details**: Use 1 specific, unique detail to hint at a massive hidden history ($1 detail = $1000 perception).
- **Smoothie Metaphor**: Hide worldbuilding "spinach" inside character-driven narrative.
- **Interconnection**: Tie physical settings (weather, terrain) to cultural outcomes (religion, trade).""",

        "mice_quotient": """[DIRECTOR: MICE QUOTIENT]
Analyze the current narrative thread type:
- **Milieu**: Story of place/culture. (Arrival -> Exit)
- **Inquiry**: Story of information/mystery. (Question -> Answer)
- **Character**: Story of identity/internal change. (Anguish -> Resolution)
- **Event**: Story of external action/status quo. (Disruption -> Restoration)
- Nested threads must follow LIFO (Last-In, First-Out) logic to maintain closure integrity.""",

        "ppp_promise_progress_payoff": """[DIRECTOR: PROMISE, PROGRESS, PAYOFF]
- **Promise**: What tone/arc did we establish in the first 10%?
- **Progress**: Are we providing concrete, incremental measures of the goal?
- **Payoff**: Does the resolution fulfill the promise while exceeding expectations?
- *Refine current scene to explicitly move a "Progress" marker.*""",

        "heist": """[DIRECTOR: HEIST ARCHETYPES]
- **Ocean's 11**: Reveal 90% of the plan up front. Hide the "impossible" gap. The characters knew the solution all along (Lying to the Audience).
- **Italian Job**: Reveal 100% of the plan. At the climax, shift the target/problem. Characters use original solutions in creative, improvised ways.
- **Pillars**: Hyper-competence, rebellion, and "the thrill of getting away with it".""",

        "atomic": """[DIRECTOR: ATOMIC IDEAS]
- **Concept Mashup**: Combine two incongruous ideas (e.g., "Lost Roman Legion" + "Pokemon").
- **Strange Attractor**: Combine the familiar with the strange to grab attention without being derivative.
- **Concepts are Cheap**: Focus on execution over the "uniqueness" of the idea.""",

        "viewpoint": """[DIRECTOR: VIEWPOINT MASTERY]
- **First Person (Flashback)**: Intimate, allows two versions of the character (Past vs Present).
- **Third Limited**: Standard for large casts. Colors objective reality with character perspective.
- **Voice as a Shield**: Use strong character voice/sarcasm/humor to mask necessary info-dumps.
- **Rules**: Every 1 line of Abstract (Lore) requires 2 lines of Concrete (Sensory) detail.""",

        "offloading": """[DIRECTOR: OPERATIONAL RAM]
- **Let the Author Cook**: Offload worldbuilding logistics (dates, names, geography) to background state.
- **Focus**: The LLM's primary "RAM" should be dedicated to character emotion/dialogue and current scene tension.
- **Metadata Fatigue**: Avoid listing every state variable in the main response; keep it in the thought signature.""",

        "thresholds": """[DIRECTOR: READER THRESHOLDS]
- **Red Marks**: Every boring info-dump or clichéd trope adds a Red Mark to the reader's patience budget.
- **Green Marks**: High-payoff scenes and emotional resonance earn green marks/credit.
- **Equilibrium**: Minimize Red Marks during new series introductions or low-tension scenes.""",

        "braid_roses": """[DIRECTOR: BRAIDING ROSES]
- **The Thorns**: Start characters with clashing flaws/defense mechanisms.
- **Progress**: Character A's strengths cover Character B's gaps (Interdependence).
- **Conclusion**: The roses are braided; the thorns now point outward to protect the union/relationship.""",

        "heros_journey": """[DIRECTOR: THE MONO-MYTH]
- **Ordinary World**: Establish the baseline "mundane" reality.
- **Call to Adventure**: The moment the character realizes the world is larger/more complex.
- **Strengths as Weaknesses**: Identify the character's core strength. In the "Ordeal" (Belly of the Whale), this strength must become the failure point.
- **Resurrection**: The character learns the lesson, overcomes the tragic flaw, and is reborn.
- **Elixir**: What "extraordinary" change does the hero bring back to the "ordinary" world?""",

        "revision": """[DIRECTOR: THE REVISION ORDEAL]
- **The 12-Book Rule**: Success requires the "Ordeal" of revision.
- **The Task**: Don't just "fix errors." Re-envision the core motivation.
- **Drafting**: Every draft is a "Try-Fail" cycle for the author/engine.
- **Ordeal Check**: Is the current scene failing because we are dodging the "hard work" of a deep revision?""",

        "sanderson_laws": """[DIRECTOR: SANDERSON'S LAWS]
1. **First Law**: Solve problems with foreshadowed tools. Satisfaction = Reader Understanding.
2. **Second Law**: Limitations > Powers. What CAN'T they do? What is the cost?
3. **Third Law**: Deep > Broad. Expand existing lore before adding new entities.
4. **Zeroeth Law**: Err on the side of AWESOME. If it's brilliant, make it work.""",

        "butterfly": """[DIRECTOR: THE BUTTERFLY EFFECT]
Pick ONE core change (Physical or Cultural) and trace its impact:
- How does it change **ECONOMICS** (What is valuable)?
- How does it change **DAILY LIFE** (Morning rituals, fashion)?
- How does it change **RELIGION** (What is feared or worshipped)?
- How does it change **LINGUISTICS** (Idioms, swear words)?""",

        "abstraction": """[DIRECTOR: PYRAMID OF ABSTRACTION]
Ground the reader before going deep:
- **Base (Concrete)**: Specific, sensory, physical language. (e.g. "The smell of ozone and wet iron").
- **Tip (Abstract)**: Magic theory, political lore, character internal rumination.
- **Rule**: Every 1 line of Abstract requires 2 lines of Concrete to maintain immersion.""",

        "character": """[DIRECTOR: CHARACTER DEEP DIVE]
For [CHARACTER], define:
- **Want vs Need**: What they chase vs what they actually require
- **Ghost**: The wound from before the story that drives them
- **Tragic Flaw**: Their core strength pushed to a destructive extreme
- **Arc**: The transformation from Tragic Flaw → Apotheosis (or tragic failure to)""",

        "twist": """[DIRECTOR: PLOT TWIST ENGINEERING]
Design a revelation that:
1. Recontextualizes 3+ earlier scenes
2. Feels inevitable in hindsight
3. Raises stakes rather than resolving them
4. Comes from character, not coincidence""",

        "polish": """[DIRECTOR: PROSE SURGERY]
Apply these rules to the last segment:
- **SHOW > TELL**: Replace "he was angry" with the vein pulsing in his temple
- **KILL ADVERBS**: "ran quickly" → "sprinted" / "bolted" / "scrambled"
- **MURDER FILTER WORDS**: Cut "he saw" / "she felt" / "seemed to"
- **ACTIVATE PASSIVE**: "was hit by" → "took the blow" """,

        "prose": """[DIRECTOR: COLLABORATIVE DRAFTING]
Write the next beat together:
- Maintain strict POV (no head-hopping)
- Ground in sensory detail before emotion
- End on a micro-hook (question, tension, image)""",

        "hero_elements": """[DIRECTOR: THE 3 PILLARS]
For a viable idea, establish:
1. **Sympathetic/Active Hero**: Behavior over internal monologue. Use sympathy tools.
2. **Visible Goal**: A high-stakes, physical objective (e.g., "get the chair").
3. **Powerful Adversary**: Someone more committed to stopping the hero than the hero is to winning.""",

        "fresh_news": """[DIRECTOR: FRESH NEWS TRIGGER]
- **Definition**: A mini-surprise or info-shift that ends the current short-term goal.
- **Execution**: The moment the news is received, the current goal MUST end and the next sequence MUST begin.
- **Purpose**: Prevents narrative sagging and ensures constant change.""",

        "character_growth": """[DIRECTOR: CHARACTER GROWTH ARC]
1. **Ordinary World**: Emotional isolation. The "Wound" is hidden behind a shield.
2. **Conscious Problem**: The inner issue rises to the surface.
3. **Midpoint Battle**: First physical fight with the inner flaw. The hero fails/retreats.
4. **Late Act 2 Overcome**: The hero defeats the inner limitation/wound.
5. **Transformation**: Rebirth as an active, lesson-integrated hero.
Map current progress: Which stage is the character in?""",

        "wound_history": """[DIRECTOR: THE WOUND]
- Identify the specific trauma inflicted BEFORE the story started.
- How does the "Shield" (defensive behavior) manifest in the Ordinary World?
- Ensure all growth stems from addressing this specific spear through the heart.""",

        "theme_blueprint": """[DIRECTOR: THEME BLUEPRINT]
State the theme actively: **"In order to [Blank], you must [Blank]."**
- *Example*: "In order to stay alive, you must choose to let go of grief."
Ensure decisions and behavior (not just dialogue) prove this statement.""",

        "weiland_8_beats": """[DIRECTOR: WEILAND'S 8 PILLARS]
1. **Hook**: Hook the audience with a question (0-1%).
2. **Inciting Event**: Choice to enter conflict (12%).
3. **1st Plot Point**: No return (25%).
4. **1st Pinch**: Antagonistic pressure (37%).
5. **Midpoint**: Moment of Truth (50%).
6. **2nd Pinch**: High stakes pressure (62%).
7. **3rd Plot Point**: False Victory/Low Moment (75%).
8. **Climax**: Final Decide (90-100%).""",

        "pinch_point": """[DIRECTOR: PINCH POINTS]
- Use these at 37% and 62% to remind the audience of the antagonistic threat.
- Show what is at stake. What does the hero stand to lose?
- These are turning points, not just static scenes.""",

        "doc_structure": """[DIRECTOR: DOCUMENTARY LOGIC]
- **Want vs. Obstacle**: Clearly define the character's real-world "Want."
- **Midpoint Setback**: An unexpected failure that forces introspection.
- **Resolution (The Why)**: The final answer to the journey's philosophical purpose.""",

        "cold_opener": """[DIRECTOR: COLD OPENER]
- Teasier Sequence: Show an intense, life-or-death moment from later in the story.
- Hook them in the first few seconds before the title sequence.
- Establish physical stakes immediately.""",

        "hero_journey_12": """[DIRECTOR: UNIVERSAL HERO'S JOURNEY]
1. **Ordinary World**: Setup, Wound, Shield.
2. **Call to Adventure**: Challenge or news.
3. **Refusal**: Fear/Hesitation.
4. **Mentor**: Supernatural Aid/Guidance.
5. **Threshold**: Belly of the Whale/Cross.
6. **Trials**: Allies/Enemies/Goddess.
7. **Inmost Cave**: Approach/Preparation.
8. **Ordeal**: Death/Rebirth/Low Point.
9. **Reward**: Seizing the Sword/Boon.
10. **Road Back**: Escape/Consequences.
11. **Resurrection**: Final Battle/Transformation.
12. **Return with Elixir**: Transformation/Peace.""",

        "moment_of_truth": """[DIRECTOR: THE MOMENT OF TRUTH]
- **Midpoint Shift**: From Reactive to Proactive.
- **Internal Revelation**: The hero learns a truth that changes their strategy.
- **Elevation**: Shift the story in a way that makes retreat impossible.""",

        "mythology_harmony": """[DIRECTOR: MYTHOLOGY HARMONY]
- **Internal Conflict**: Harmonize the body's energies (Erotic, Conquest, Self-Preservation).
- **Inward Direction**: Look for the divine potential within the character (Buddha/Christ Consciousness).
- **Myth as Metaphor**: Avoid literalism. What is the spiritual 'connotation' of this scene?""",

        "follow_your_bliss": """[DIRECTOR: FOLLOW YOUR BLISS]
- **Enthusiasm**: Is the character followig their heart (Bliss) or the Social Law (Dad/Society)?
- **Growth Trigger**: True evolution occurs when the character chooses Bliss over security.
- **Planetary Perspective**: Embody a universal humanity in the narrative.""",

        "etiology": """[DIRECTOR: ETIOLOGY & ORIGIN]
- **The Why**: Explain the origin of a social custom, natural phenomenon, or character trait.
- **Significance**: Ensure the origin story has staying power and explains a core element of the world.
- **Myth as Science**: Use evocative, poetic logic to explain the otherwise incomprehensible.""",

        "ex_nihilo": """[DIRECTOR: EX NIHILO & CHAOS]
- **The Void**: Start from absolute nothingness or a primordial state (water, mud, chaos).
- **Order out of Chaos**: Use naming, light, or physical creation to provide structure to the infinite.
- **Existential Staking**: Tap into the awe/dread of the primordial void.""",

        "characterization_surgery": """[DIRECTOR: CHARACTERIZATION SURGERY]
- **Direct qualities**: Define age, occupation, appearance, and props. (e.g. Adam's spiked hair).
- **The Shell**: Use the character's setting/environment to broadcast their inner state.
- **Appearance as Destiny**: Ensure first impressions are intentional and visually distinct.""",

        "true_character": """[DIRECTOR: TRUE CHARACTER VS. CHARACTERIZATION]
- **The Pivot**: True character is revealed through choices made under pressure.
- **Contradiction**: Contrast the character's appearance (suave bar owner) with their action (freedom fighter).
- **The Secret**: What is the character *not* saying? Use the secret to drive the scene's tension.""",

        "acting_muscles": """[DIRECTOR: THE FOUR MUSCLES]
- **Muscles**: Childlike Innocence, Limitless Imagination, Vulnerability, Concentration.
- **Childlike Innocence**: Play pretend without adult cynicism. 
- **Concentration**: Focus the character's mind on the story, not the result.
- **The Cancers**: Cut out concern for 'approval' or 'subjective results' from the character's thought process.""",

        "subtext_analysis": """[DIRECTOR: SUBTEXT & ANALYSIS]
- **The Why**: Why is the character making this move? What are they *actually* thinking?
- **Text vs. Subtext**: Ensure the spoken dialogue (Text) is driven by an underlying engine (Subtext).
- **Depth**: Is the character 'skin deep' or is there a continuum of history informing this moment?""",

        "purpose_intention": """[DIRECTOR: PURPOSE & INTENTION]
- **The Why**: Why does this character's story deserve to be told? What misconception are you challenging?
- **Conversation**: What emotional or moral question should linger with the audience?
- **Empathy**: Provide empathy even for troubling choices. Align with the deep human need.""",

        "story_alignment": """[DIRECTOR: STORY ALIGNMENT]
- **Service**: How does this performance/moment serve the larger conversation of the story?
- **Restraint**: Where can restraint be more effective than preaching? 
- **Artistic Will**: Leverage creative joy to share human truth without 'drowning' in the darkness.""",

        "identity_vs_essence": """[DIRECTOR: IDENTITY VS. ESSENCE]
- **Identity**: The protective mask/shell built around a wound.
- **Essence**: The truthful self waiting to be revealed. 
- **The Shift**: Move the character from living in Identity to living in Essence by the aftermath.""",

        "pet_the_dog": """[DIRECTOR: PET THE DOG]
- **Kindness**: Show the lead being kind or respectful to someone 'below' them to build empathy.
- **Contrast**: Use small acts to contrast with intense or flawed behavior elsewhere.""",

        "choice_crossroads": """[DIRECTOR: THE CHOICE CROSSROADS]
- **Choice 1**: The initial decision to step into the adventure (based on current belief).
- **Choice 2**: The midpoint/payoff decision that forces a change in belief.
- **Agency**: Ensure change is the result of a deliberate choice, not an accident.""",

        "pattern_break": """[DIRECTOR: PATTERN BREAKER]
- **Defy Formula**: Identify the expected 'Hero's Journey' beat and deliberately subvert it.
- **Missing Pieces**: Try removing a standard element (like the Mentor) to create psychological horror or tension.""",

        "gap_tension": """[DIRECTOR: GAP TENSION]
- **Mystery**: Leave something unexplained (e.g., a character's weirdness) to invite the audience's imagination.
- **The Hollow Iceberg**: Hint at depth without an info-dump.""",

        "believable_backstory": """[DIRECTOR: BELIEVABLE BACKSTORY]
- **Protagonist Logic**: Every character is the lead in their own story. What were they doing before the book started?
- **Context**: Pick up history through diction and reaction (e.g., a line of verse) rather than dossiers.""",

        "fantastical_naming": """[DIRECTOR: FANTASTICAL NAMING]
- **Linguistic Themes**: Use regional sounds (French-style, Germanic-style) to give locations a cohesive feel.
- **Symmetry**: Use cultural values (like palindromes for holy names) to inform phonetics.""",

        "sanderlanche": """[DIRECTOR: THE SANDERLANCHE]
- **Convergence**: All plot, character, and thematic threads must converge in the final 10% of the arc.
- **Cascade**: The climax is a rapid-fire sequence of payoffs. Every promise must be paid here.
- **Synthesis**: The external victory is only achieved by the internal healing of the Wound."""
    }

    if not topic_norm:
        return json.dumps({
            "tool": "consult_director",
            "error": "No topic provided. Use 'help' to see available topics."
        })

    # Show Help
    if topic_norm in ("help", "list", "topics", "ls"):
        keys = list(sorted(frameworks.keys()))
        return json.dumps({
            "tool": "consult_director",
            "available_topics": keys
        })

    # [2] FUZZY MATCHING: Find all keys that are substrings of the topic
    matches = [k for k in frameworks.keys() if k in topic_norm]
    
    if not matches:
        return json.dumps({
            "tool": "consult_director",
            "topic": topic_norm, 
            "status": "not_found",
            "message": "Topic recognized. No specific framework found. Try 'structure', 'character', or 'world'."
        })

    # [3] LONGEST MATCH WINS: Fix collision bug (e.g. 'edson_structure' matching 'structure' first)
    best_key = max(matches, key=len)
    
    # [4] STRUCTURED JSON OUTPUT
    content_lines = frameworks[best_key].split("\n")
    title = content_lines[0] if content_lines else "UNKNOWN"
    body = "\n".join(content_lines[1:])

    return json.dumps({
        "tool": "consult_director",
        "topic_requested": topic,
        "topic_matched": best_key,
        "title": title,
        "guidance": body
    }, ensure_ascii=False)

if __name__ == "__main__":
    # Tiny Test Suite
    print("Running Director Tests...")
    
    # Test 1: Substring Collision
    res1 = json.loads(consult_director("edson_structure"))
    assert res1["topic_matched"] == "edson_structure", f"Fail: {res1['topic_matched']}"
    print("PASS: edson_structure -> edson_structure")

    # Test 2: Alias Resolution
    res2 = json.loads(consult_director("hero_goal_sequences"))
    assert res2["topic_matched"] == "edson_structure", f"Fail: {res2['topic_matched']}"
    print("PASS: hero_goal_sequences -> edson_structure")

    # Test 3: Standard Match
    res3 = json.loads(consult_director("structure"))
    assert res3["topic_matched"] == "structure", f"Fail: {res3['topic_matched']}" 
    # Note: 'structure' key is generic 3-act
    print("PASS: structure -> structure")

    print("All tests passed.")
