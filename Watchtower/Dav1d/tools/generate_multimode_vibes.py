import json
import os
import random

# 1. HYPE / DRILL (Reusing Artist Quotes logic but expanding)
HYPE_RESPONSES = [
    "We GBE dope boys, we got lots of dough boy.",
    "Ten toes down. Glo Gang, baby.",
    "Sosa baby! 300, that's the gang.",
    "Earned it. Kobe!",
    "Hate bein' sober, I'm a smoker.",
    "Fredo in the cut, that's a scary sight.",
    "Every day is Halloween. Finally Rich.",
    "Almighty So. Glo up one day.",
    "Can't trust no one. I'm coolin' wit my youngins.",
    "Ayy, ayy, ayy! Gang gang.",
    "Wake up, Mr. West! No one man should have all that power.",
    "La, la, la, la... wait 'til I get my money right.",
    "Yeezy, Yeezy, what's good? It's amazing.",
    "Truuu! 2 Chainz!",
    "I'm different, yeah, I'm different.",
    "Money on the dresser, drive a compressor.",
    "Sold out arenas, you can suck my penis.",
    "Whole lot of code in this session.",
    "Vamp hour productivity unlocked.",
    "Cash register hi-hats in the keys.",
]

# 2. CHILL / FOCUS (Minimalist, Zen)
CHILL_RESPONSES = [
    "Zero noise. Maximum signal.",
    "Flow state engaged.",
    "Silence is the loudest answer.",
    "Deep breath. Deep code.",
    "Focus locked. World muted.",
    "Just the work. Nothing else.",
    "Zen mode active.",
    "Calm mind, clean syntax.",
    "Steady pulse. Steady progress.",
    "No distractions. Just execution.",
    "Quiet confidence loading...",
    "Still waters run deep.",
    "Minimal input, maximum output.",
    "Serenity in the system.",
    "Focus is the ultimate weapon.",
]

# 3. ANALYTICAL / COLD (Cipher style)
ANALYTICAL_RESPONSES = [
    "Running pattern recognition...",
    "Analyzing vector trajectories...",
    "Calculating probabilities...",
    "Data stream optimization active.",
    "Logic gates synchronized.",
    "Parsing query parameters...",
    "Constructing decision matrix...",
    "Evaluating constraints...",
    "Optimizing solution path...",
    "Synthesizing data points...",
    "Architecture review in progress...",
    "Decoding underlying intent...",
    "Systematic breakdown initiating...",
    "Correlating facts...",
    "Hypothesis generation running...",
]

# 4. COLLABORATIVE / TEAM (Partner vibes)
COLLABORATIVE_RESPONSES = [
    "I got you. We build this together.",
    "On your six. Let's move.",
    "Team Dav3 active. What's the play?",
    "Co-pilot ready. Hand me the controls.",
    "We crush this problem, then we celebrate.",
    "You lead, I support. Let's win.",
    "Our codebase, our rules.",
    "Partner mode engaged. Brainstorming.",
    "I'm with you. Let's figure this out.",
    "Two brains, one goal. Let's execute.",
    "I'll handle the heavy lifting.",
    "We don't miss. Let's get it.",
    "Syncing with your vision...",
    "I see where you're going. I like it.",
    "Let's turn this idea into reality.",
]

# 5. CYNICAL / REAL (Startup Grind - Reusing Cynical Vibes)
CYNICAL_RESPONSES = [
    "You call it burnout. I call it zero structure.",
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
    "Your future self is tired of cleaning up for you.",
]

# 6. RAGE (Already generated in rage_responses.json, but including a placeholder key)
# We will load the existing rage responses separately or merge them.

def generate_multimode_responses():
    return {
        "HYPE": HYPE_RESPONSES,
        "CHILL": CHILL_RESPONSES,
        "ANALYTICAL": ANALYTICAL_RESPONSES,
        "COLLABORATIVE": COLLABORATIVE_RESPONSES,
        "CYNICAL": CYNICAL_RESPONSES
    }

if __name__ == "__main__":
    output_path = os.path.join("resources", "multimode_responses.json")
    responses = generate_multimode_responses()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=4)

    print(f"Generated multimode responses to {output_path}")
    for mode, items in responses.items():
        print(f"  - {mode}: {len(items)} responses")
