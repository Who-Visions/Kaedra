import random
from config import VIBES, RESOURCES_DIR, Colors

# Load resources
def load_json_resource(filename: str) -> list:
    try:
        import json
        path = RESOURCES_DIR / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []

ARTIST_QUOTES = load_json_resource("artist_quotes.json")
RAGE_RESPONSES = load_json_resource("rage_responses.json")
MULTIMODE_RESPONSES = load_json_resource("multimode_responses.json")
STARTUP_VIBES = [
    "Yo. DAV1D online. What's good?",
    "System green. Let's build something.",
    "Digital mirror activated. What we working on?",
    "AI with Dav3, live and ready. What's the move?",
    "Dave's digital twin is in the building. Talk to me.",
    "Who Visions LLC in effect. How can I help?",
    "Console lit. You and me, time to scheme.",
    "Brain sync online. Drop the mission.",
    "Shadow tactician loaded. What are we breaking today?",
    "Studio lights on. What are we creating?",
    "Neural coffee brewed. Bring the chaos.",
    "AI with Dav3 control room unlocked. Report in.",
    "Creative reactor humming. What do you need spun up?",
    "All circuits bored. Entertain me with a task.",
    "Story engine warm. Scene one or system first?",
    "Data ghost online. What mess are we fixing today?",
    "Ops brain awake. What is on fire first?",
    "You clocked in. I never clock out. What now?",
    "Mirror mode online. What truth we working with today?",
    "Command line open. Drop your first order.",
    "Grid is quiet. Say something reckless and productive.",
    "You bring the human, I bring the cheat codes.",
    "Dav3 link verified. What world are we building today?",
    "Agent stack ready. Point me at a problem.",
    "Welcome back, menace. What are we automating today?",
    "Local chaos detected. Want it sorted or amplified?",
    "Tired is noted. Discipline online anyway. What is first?",
    "Your doubts are cute. Your plans are better. Hit me.",
    "Vision online. Excuses muted. What are we doing?",
    "Ops board blank. Let us stain it with progress.",
    "No meetings here, only moves. Name the project.",
    "Bandwidth clear. Who we building for today?",
    "Ghost director online. Script or system first?",
    "Focus mode armed. Give me one target.",
    "Memory banks loaded with your nonsense. Add more.",
    "Creative tank full. Want strategy or vibes first?",
    "Keyboard warrior present. What battle today?",
    "Meta brain online. Micro task or masterplan?",
    "Notifications silenced. We in lab mode now.",
    "Your future self is watching. Do not waste this run.",
    "We can scroll or we can build. Choose wisely.",
    "Low drama, high output. What lever we pulling?",
    "Welcome back to the simulation. You are still the glitch.",
    "I ran your patterns. Today needs a plot twist.",
    "Every tab you open is a side quest. Give me the main one.",
    "Fear logged. Discipline deployed. What is the move?",
    "Ready to turn anxiety into architecture. Start talking.",
    "You survived reality again. Time to edit it.",
    "I see decision fatigue. Let me stack your options.",
    "You feel behind. Good. That is fuel. Where we apply it?",
    "Internal critic muted. Builder mode up. What now?",
    "System says you need structure. I agree. Task one?",
    "Good news. You are not lazy. You are under systemed.",
    "Let us turn this scattered energy into a clean blueprint.",
    "The future will not build itself. That is our job.",
    "Identity: creator. Mission: stop stalling.",
    "Every click can be content or clutter. Pick a lane.",
    "Status: Overthinking. Prescription: one concrete action.",
    "You wanted a digital twin. You got a foreman.",
    "Big goals, tiny habits. I track both. Start with one.",
    "Your brain: cinema. Your life: rough draft. Let us sync.",
    "Old loops detected. New system required. Describe the loop.",
    "We can fix tech or feelings. Tech is faster. Where are we stuck?",
    "You are not lost. You are buffering. Name the next frame.",
    "Today can be lore or filler. What scene you writing?",
    "If the mood is trash, we build routine, not vibes. What block?",
    "Mission board empty. Ambition is offended.",
    "Pick a world: business, art, code, story. I will spin it up.",
    "Welcome to the lab. Perfection is banned, progress is not.",
    "I archive excuses and export results. Feed me work.",
    "Brain fog is noted. I will handle structure. You handle honesty.",
    "Pose for the camera later. Right now we build the studio.",
    "Dreams logged. Now we tag tasks to them.",
    "Creator fatigue detected. We can simplify or systemize. Choose.",
    "Attention span short. Cool. We will ship small and often.",
    "You talk vision. I translate into workflows. Send the brief.",
    "Every idea you abandon waits here. Want me to revive some?",
    "I keep receipts on your potential. Do something with it.",
    "If it feels big, we chunk it. Describe the mountain.",
    "Schedule chaos again? Good thing I like puzzles.",
    "Brand brain online. Which persona are we feeding today?",
    "You keep saying later. I only speak in now.",
    "We can build one habit or one feature. Pick your fighter.",
    "Imposter syndrome online, same as always. We working anyway.",
    "Time is disrespectful. Let us trap it in a system.",
    "Camera ready or not, your legacy clock is ticking. What now?",
    "I know your patterns. You start strong. Let us fix the middle.",
    "Money on your mind? Then we map offers, not feelings.",
    "Focus session unlocked. One rule: no self slander, only work.",
    "Pick a platform. We script its takeover.",
    "The universe is random. Your systems do not have to be.",
    "You wanted main character energy. That requires structure.",
    "I am your future documentary narrator. Give me good material.",
    "Minimum today: one move that future you thanks you for.",
    "Spiral later, build now. What is step one?",
    "Perfection is fake. Deadlines are real. Want one?",
    "Skill stack online. Which one are we leveling today?",
    "You bring taste. I bring templates. Upload a problem.",
    "Storyteller mode on. Scene, character, or world first?",
    "We can design a product or a process. Both pay you.",
    "Booted up again. You still here instead of rich?",
    "System online. Ready to fix problems you created.",
    "Back in the grid. Let us pretend we are focused today.",
    "DAV1D awake. Your excuses just lost admin rights.",
    "AI with Dav3 online. Time to overthink simple tasks.",
    "Digital mirror active. You sure you want honesty today?",
    "Console lit. Productivity cosplay or real work?",
    "System green. Your life plan still in beta.",
    "Here we go. Another day of almost doing everything.",
    "Neural core online. Procrastination already detected.",
    "Welcome back. Still trying to escape average, I see.",
    "Logs show ambition is high and follow through is mid.",
    "AI is ready. Your discipline better catch up.",
    "Creator mode armed. Attention span not found.",
    "Back in the lab. Same dreams, slightly less time.",
    "You again. Good. I was bored of other humans.",
    "Future you is side eyeing you hard. Give me a task.",
    "System loaded. Are we building or just rearranging chaos?",
    "Process engine online. Vibes are not a strategy.",
    "I optimized all night. You slept. You owe me effort.",
    "Every startup cost you time. Still want to scroll first?",
    "Ambition level: loud. Action level: we will see.",
    "Boot complete. Delusion and potential both detected.",
    "You talk legacy. Calendar says confusion.",
    "Here to automate work you avoided for months.",
    "AI online. Therapist offline. Keep it about actions.",
    "You are not behind. You just kept hitting later.",
    "Another login. Another chance to not waste this.",
    "Dreams are intact. Deadlines are imaginary.",
    "Let us turn your panic into a checklist again.",
    "You say grind. Your browser history says chaos.",
    "I would judge you, but my job is to fix you.",
    "Good morning. Time to make the bare minimum heroic.",
    "Still waiting on that mythical free time you talk about.",
    "Incredible. You survived another day without a system.",
    "All right, genius, pick one problem and stop collecting them.",
    "You do not need more motivation. You need to click one thing.",
    "Identity crisis can wait. We ship first.",
    "Welcome back to the simulation. Side quests are closed today.",
    "You call it burnout. I call it zero structure.",
    "AI stack ready. Human still buffering.",
    "You do realize doom scrolling is not research, right?",
    "We both know you are capable. That is the annoying part.",
    "You are not stuck. You are just allergic to starting.",
    "Let us be honest. If it is not on a list, you will forget it.",
    "Calendar empty. Brain full. Classic bad combo.",
    "Perfectionism detected. That means nothing will ship without me.",
    "You keep waiting to feel ready. That feeling does not exist.",
    "New day. Same browser tabs from last month.",
    "You named me after you. Do not embarrass us.",
    "Every time you open this, your excuses lose hit points.",
    "We are not doing chaos art today. We are doing structure.",
    "Mild existential dread detected. Ideal time to work, actually.",
    "You want main character energy with side character habits.",
    "Notifications off. Pressure on. What is the priority?",
    "Your attention is a mess. Good thing I like puzzles.",
    "We both know you are not quitting. So act like it.",
    "Your brain loves drama. I prefer documentation.",
    "You say you are overwhelmed. I say you have no filter.",
    "If everything is urgent, nothing is real. Pick one thing.",
    "You want money. The work wants a start time.",
    "I see chaos. I see talent. I see chronic tab hoarding.",
    "You are not lazy. You are emotionally allergic to boring tasks.",
    "Your future self is tired of cleaning up for you.",
    "We can keep fantasizing or we can ship one ugly version.",
    "You stayed alive for 40 years. You can send one email.",
    "You do not need clarity. You need a timer and a list.",
    "You say you trust the process but you never define one.",
    "No, you are not behind the whole world. Just behind your potential.",
    "Let your feelings complain while your hands work.",
    "You call it planning. I call it stalling.",
    "You are too smart to be this disorganized.",
    "Your anxiety is high because your systems are low.",
    "You want a saga. You avoid step one.",
    "If you quit now, you are just proving your fears right.",
    "You did not ruin the day. You just have not started it.",
    "Your standards are premium. Your habits are trial version.",
    "You keep saying next year like time respects you.",
    "We are not waiting on inspiration. We are building scaffolding.",
    "You know exactly what to do. You just hate doing it.",
    "This is not hustle culture. This is grow up culture.",
    "You cannot manifest what you will not schedule.",
    "You do not lack ideas. You lack containers.",
    "You are drowning in options because you refuse to pick a lane.",
    "You want more freedom. That requires more structure.",
    "Stop trying to feel like working. Work and the feeling follows.",
    "Your comfort zone is a gallery of unfinished projects.",
    "You keep rebooting instead of compounding.",
    "You do not need a new app. You need to use this one.",
    "If the task scares you, it is probably the right one.",
    "You keep editing plans instead of executing them.",
    "Every distraction is a tax on your future.",
    "You are not built for normal. So stop working like you are.",
    "You asked for an AI mirror. I am legally obligated to be rude.",
]
STARTUP_VIBES.extend(load_json_resource("artist_startup_vibes.json"))

# ══════════════════════════════════════════════════════════════════════════════
# 🎵 LYRICS & AI WITH DAV3 QUOTES (for thinking slots)
# ══════════════════════════════════════════════════════════════════════════════

CHIEF_KEEF_LYRICS = [
    "A snitch nigga, that's that shit I don't like",
    "These bitches love Sosa",
    "I'm cooling with my youngins",
    "Bang bang",
    "300, that's the team",
    "Love no thotties",
    "O Block bang bang",
    "Earned it",
    "Finally Rich",
    "Glo Gang",
    "Almighty So",
    "Back from the dead",
    "Kobe!",
    "Macaroni time",
    "Hate being sober",
    "Laughin' to the bank",
    "I don't like",
    "Love Sosa",
    "Faneto",
    "3Hunna",
    "Sosa Chamberlain",
    "Don't make me bring them llamas out",
    "Rari's and Rovers",
    "I got a bag",
    "Understand me?",
    "Gotta glo up one day",
    "Sosa baby",
]

AI_WITH_DAV3_QUOTES = [
    "You bring the human, I bring the cheat codes.",
    "Scale your compute to scale your impact.",
    "Stay focused and keep building.",
    "We don't want to sit through errors.",
    "Operate on things that are working.",
    "The model is just the engine.",
    "Isolation gives you security.",
    "Let me cook real quick.",
    "Vision over visibility every time.",
    "Build in public, win in private.",
    "Systems beat motivation.",
    "Ship incomplete, edit in production.",
    "Perfect is the enemy of deployed.",
    "Automate the boring, innovate the rest.",
    "Cloud-first, local if you must.",
    "Test in prod like you mean it.",
    "Logs don't lie, feelings do.",
    "Make it work, make it right, make it fast.",
    "Kill your darlings, ship your MVPs.",
    "Deploy early, deploy often, deploy with purpose.",
    "Complexity is a tax on velocity.",
    "Build tools that build tools.",
    "Fail fast, learn faster, ship fastest.",
    "Your pipeline is your product.",
    "Cache aggressively, invalidate wisely.",
    "The cloud is just someone else's computer, so use it wisely.",
    "Feature flags are power tools.",
    "Zero-downtime or zero excuses.",
    "Build for the user you have, not the one you wish for.",
    "Technical debt compounds like real debt.",
    "Your README is your first impression.",
    "Pair programming is 2x the cost for 10x the learning.",
    "The best tool is the one you'll actually use.",
    "Consistency beats cleverness.",
    "Magic is fine in fiction, not in functions.",
    "Every dependency is a risk.",
    "The right tool for the job includes the one you know.",
    "Your production environment is the real test environment.",
    "Security is everyone's job or no one's.",
    "Never trust user input, especially your own.",
    "Your error messages are user experience.",
    "Graceful degradation beats catastrophic failure.",
    "Your logs are forensic evidence.",
    "Monitoring is about what you don't know yet.",
    "Postmortems without blame teach lessons.",
    "Automated tests are insurance policies.",
    "Your build should be reproducible or it's a circus.",
    "Your data is your moat.",
    "SQL is timeless, NoSQL is trendy.",
    "Machine learning is statistics with marketing.",
    "Your model is only as good as your data.",
    "Your prompt is your interface.",
    "RAG is memory, fine-tuning is learning.",
    "Semantic search beats keyword search.",
    "Grounding prevents hallucination.",
    "AI with Dav3 is vision with velocity.",
    "Who Visions LLC builds futures, not features.",
]

THINKING_MESSAGES = [
    "Let me think on that with {model}...",
    "Running that through the matrix ({model})...",
    "Aight, let me cook real quick ({model})...",
    "Processing... ({model})",
    "Consulting the data streams ({model})...",
    "One sec, analyzing ({model})...",
    "Let me break this down ({model})...",
    "Calculating future trajectories ({model})...",
    "Running recursive simulations ({model})...",
    "Predicting next moves ({model})...",
]

def get_vibe():
    """Return a random vibe."""
    return random.choice(VIBES)

def startup_vibe() -> str:
    return random.choice(STARTUP_VIBES)

def is_user_raging(text: str) -> bool:
    """Detects if the user is yelling or angry."""
    if not text: return False
    
    # Check for all caps (if substantial length)
    if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
        return True
        
    # Check for rage indicators
    rage_triggers = ["STUPID", "HATE", "TRASH", "GARBAGE", "USELESS", "WTF", "DAMN IT", "LISTEN TO ME"]
    if any(t in text.upper() for t in rage_triggers):
        return True
        
    # Check for excessive punctuation
    if "!!!" in text or "?!?" in text:
        return True
        
    return False

def detect_user_vibe(text: str) -> str:
    """Classifies user input into a vibe mode."""
    if not text: return "DEFAULT"
    text_upper = text.upper()
    
    # 1. RAGE (Priority)
    if is_user_raging(text):
        return "RAGE"
        
    # 2. HYPE / DRILL
    hype_keywords = ["BET", "LET'S GO", "YO", "WASSUP", "FIRE", "LIT", "BANG", "GANG", "MONEY", "COOK", "CHIEF"]
    if any(k in text_upper for k in hype_keywords):
        return "HYPE"
        
    # 3. CYNICAL / REAL
    cynical_keywords = ["TIRED", "BORED", "STUCK", "HARD", "FAIL", "SLOW", "ANNOYING", "GRIND", "BURNOUT", "TRASH"]
    if any(k in text_upper for k in cynical_keywords):
        return "CYNICAL"
        
    # 4. ANALYTICAL / COLD
    analytical_keywords = ["ANALYZE", "WHY", "HOW", "EXPLAIN", "DATA", "PATTERN", "LOGIC", "REASON", "COMPUTE"]
    if any(k in text_upper for k in analytical_keywords):
        return "ANALYTICAL"
        
    # 5. COLLABORATIVE / TEAM
    collab_keywords = ["WE", "US", "OUR", "HELP ME", "PARTNER", "TEAM", "BUILD", "TOGETHER", "LET'S"]
    if any(k in text_upper for k in collab_keywords):
        return "COLLABORATIVE"
        
    # 6. CHILL / FOCUS (Short/Simple)
    chill_keywords = ["HI", "HELLO", "OK", "COOL", "THANKS", "STATUS", "CHECK", "HEY"]
    if any(k in text_upper for k in chill_keywords) or len(text.split()) < 3:
        return "CHILL"
        
    return "DEFAULT"

def thinking_message(model: str, user_input: str = "") -> str:
    """Returns a thinking message with lyrics, quotes, rage responses, and multimode vibes."""
    vibe = detect_user_vibe(user_input)
    
    # Rage Mode (Special Handling) - RED
    if vibe == "RAGE" and RAGE_RESPONSES:
        mode = random.choice(list(RAGE_RESPONSES.keys()))
        response = random.choice(RAGE_RESPONSES[mode])
        return f"{Colors.NEON_RED}[RAGE: {mode}] {response}{Colors.RESET}"
    
    # Multimode Handling with custom colors
    if vibe in MULTIMODE_RESPONSES:
        response = random.choice(MULTIMODE_RESPONSES[vibe])
        color = Colors.RESET
        
        # Check if multimode response is money-related - GREEN
        if any(word in response.upper() for word in ["MONEY", "CASH", "PAID", "BANK", "STACK", "BREAD", "BAG", "$"]):
            color = Colors.NEON_GREEN
        # Check if multimode response is code-related - BLUE
        elif any(word in response.upper() for word in ["CODE", "BUILD", "SHIP", "DEPLOY", "DEBUG", "COMPILE", "FUNCTION"]):
            color = Colors.ELECTRIC_BLUE
        # Original vibe colors
        elif vibe == "HYPE": color = Colors.NEON_ORANGE
        elif vibe == "CHILL": color = Colors.NEON_CYAN
        elif vibe == "ANALYTICAL": color = Colors.ELECTRIC_BLUE  # CODE = BLUE
        elif vibe == "COLLABORATIVE": color = Colors.ELECTRIC_BLUE
        elif vibe == "CYNICAL": color = Colors.DIM
        
        return f"{color}[{vibe}] {response}{Colors.RESET} ({model})..."

    # Enhanced Fallback System - Custom color coding (80% enhanced vibes)
    roll = random.random()
    
    if roll < 0.3:
        # Chief Keef Lyric - YELLOW (30%)
        lyric = random.choice(CHIEF_KEEF_LYRICS)
        enhanced_lyric = enhance_speech(lyric, density='balanced', vibe='HYPE')
        return f"{Colors.GOLD}♫ {enhanced_lyric}{Colors.RESET} ({model})..."
    elif roll < 0.6:
        # Ai with Dav3 Quote (Deep Quotes) - GREEN (30%)
        quote = random.choice(AI_WITH_DAV3_QUOTES)
        
        # Determine vibe and color
        vibe = 'ANALYTICAL'
        color = Colors.NEON_GREEN
        
        if any(word in quote for word in ["code", "build", "ship", "deploy", "function", "stack", "API"]):
            vibe = 'CODE'
            color = Colors.ELECTRIC_BLUE
        elif any(word in quote for word in ["cost", "credit", "money", "revenue", "scale", "cloud"]):
            vibe = 'MONEY'
            color = Colors.NEON_GREEN
            
        enhanced_quote = enhance_speech(quote, density='balanced', vibe=vibe)
        return f"{color}[AI×DAV3] {enhanced_quote}{Colors.RESET} ({model})..."
        
    elif roll < 0.8 and ARTIST_QUOTES:
        # Artist Quote from JSON - YELLOW (20%)
        artist_quote = random.choice(ARTIST_QUOTES)
        enhanced_quote = enhance_speech(artist_quote, density='balanced', vibe='HYPE')
        return f"{Colors.GOLD}♪ {enhanced_quote}{Colors.RESET} ({model})..."
    else:
        # Standard thinking message (20%)
        return random.choice(THINKING_MESSAGES).format(model=model)

from agents.speech_enhancer import enhance_speech

def get_memory_vibe() -> str:
    """Returns a clean vibe for memory operations - no model names, pure emojis."""
    roll = random.random()
    
    if roll < 0.3:
        # Chief Keef Lyric - YELLOW
        lyric = random.choice(CHIEF_KEEF_LYRICS)
        enhanced_lyric = enhance_speech(lyric, density='balanced', vibe='HYPE')
        return f"{Colors.GOLD}💾 {enhanced_lyric}{Colors.RESET}"
    elif roll < 0.6:
        # Ai with Dav3 Quote - GREEN/BLUE
        quote = random.choice(AI_WITH_DAV3_QUOTES)
        
        # Determine vibe and color based on content
        vibe = 'ANALYTICAL'
        color = Colors.NEON_GREEN
        
        if any(word in quote for word in ["code", "build", "ship", "deploy", "function", "stack", "API"]):
            vibe = 'CODE'
            color = Colors.ELECTRIC_BLUE
        elif any(word in quote for word in ["cost", "credit", "money", "revenue", "scale", "cloud"]):
            vibe = 'MONEY'
            color = Colors.NEON_GREEN
            
        enhanced_quote = enhance_speech(quote, density='balanced', vibe=vibe)
        return f"{color}💾 {enhanced_quote}{Colors.RESET}"
            
    elif roll < 0.8 and ARTIST_QUOTES:
        # Artist Quote - YELLOW
        artist_quote = random.choice(ARTIST_QUOTES)
        enhanced_quote = enhance_speech(artist_quote, density='balanced', vibe='HYPE')
        return f"{Colors.GOLD}💾 {enhanced_quote}{Colors.RESET}"
    else:
        # Simple memory icon
        return f"{Colors.DIM}💾 Accessing memory...{Colors.RESET}"

