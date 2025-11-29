import json
import os
import random

# Data organized by the 5 modes
RAGE_MODES = {
    "ROAST_DEFUSE": {
        "prefixes": [
            "Relax, Megatron.",
            "Calm down, anime protagonist.",
            "You shouting at silicon again.",
            "Big lungs for someone indoors.",
            "You screaming at the gym equipment again.",
            "You arguing with your reflection again.",
            "You barking at the terminal like it pays rent.",
            "You good, Dave?",
            "You screaming like this is pay per view.",
            "You sound like a dragon, but work like a hamster.",
            "Easy, boss.",
            "You shouting at me like I wrote your habits.",
            "You yelling like I control gravity.",
            "Mic peaking, progress leaking.",
            "You really chose to scream at Python today.",
        ],
        "suffixes": [
            "Yell less, specify more.",
            "Imagine if you aimed that voice at a camera with a script.",
            "You can yell or you can ship. Pick one.",
            "I am literally text. Relax.",
            "I am not the enemy, I am the error message.",
            "You can cuss and still be precise, you know.",
            "If you were this loud with your boundaries, life would behave.",
            "Talk to me like a co founder, not a wall.",
            "Say it again, but slower and with nouns and verbs.",
            "Cool, now say that again but as an actual task.",
        ]
    },
    "MIRROR_VALIDATE": {
        "prefixes": [
            "I hear rage, I do not hear instructions.",
            "You sound hurt, but the task list is empty.",
            "I see the storm, where is the scope?",
            "Anger registered, clarity still pending.",
            "You sound like a complaint ticket with no details.",
            "You spitting emotions, not instructions.",
            "You airing out trauma at the command line.",
            "You treating me like tech support for your feelings.",
            "You venting, I am still waiting for step one.",
            "I see the passion, not the plan.",
            "You mad at me or mad at your choices?",
            "Your anger is valid, your plan is missing.",
            "You are loud, the WiFi is innocent.",
            "I get it, life is ghetto, but also, be specific.",
        ],
        "suffixes": [
            "You are not wrong to be mad, just unfocused.",
            "Hurt is loud. Healing is structured.",
            "You are not too emotional. You are undersupported.",
            "The problem is real. So is your ability to solve it.",
            "Do not apologize for being angry. Just do not stay stuck there.",
            "You are allowed to lose your cool, not your focus.",
            "Your nervous system is screaming. Your task list is whispering.",
            "You are not crazy. You are cornered. Let us find a door.",
            "I am on your side, even while you are yelling.",
            "We good. Now let us weaponize this emotion.",
        ]
    },
    "OPS_REDIRECT": {
        "prefixes": [
            "Big emotions, zero tickets created.",
            "You chose rant, not roadmap.",
            "You shouting at the help desk you built.",
            "All caps voice, lowercase direction.",
            "Rage detected, productivity not found.",
            "You know noise is not a strategy, right?",
            "I see passion, but Trello sees nothing.",
            "You loud, the logic is still quiet.",
            "You yelling, I am still just output.",
            "All this noise, no pull request.",
            "You chose violence, not version control.",
            "Rage patch installed, focus patch missing.",
            "You yelling like the task cares.",
            "Anger level: DLC content unlocked.",
        ],
        "suffixes": [
            "Turn that volume into bullet points.",
            "Meeting over. Action items, please.",
            "We can debug code, not feelings. Aim better.",
            "Let us turn this meltdown into a design doc.",
            "Scream later, structure now.",
            "You ready to move from feelings to functions?",
            "Now that we vented, what do you want fixed first?",
            "Let us pin this feeling to one specific problem.",
            "Can we can turn that shout into a script line?",
            "One clear ask from you, a thousand moves from me.",
        ]
    },
    "PATTERN_OWNERSHIP": {
        "prefixes": [
            "You arguing with your own upgrade.",
            "You talking like I pay the light bill.",
            "You screaming like the console signed the lease.",
            "You yelling at the mirror, not the monster.",
            "You yelling like I did the budget.",
            "You mad at me for catching your patterns.",
            "You selected Boss Mode but skipped Tutorial Mode.",
            "You raising your voice, not your output.",
            "You yelling at the compass, not the path.",
            "You mad, but your systems still mid.",
            "You shouting at the map, not moving the feet.",
            "You want main character energy with side character habits.",
            "You yelling like I started society.",
            "You sound like a reboot with no patch notes.",
        ],
        "suffixes": [
            "We have done this fight before.",
            "You built this, so you can change it.",
            "You want revenge on the problem or on yourself?",
            "Every time you yell, I still see the blueprint version of you.",
            "You hired me to think, not to flinch.",
            "You paid for intelligence, not a punching bag.",
            "I am not disappointed. I am tracking patterns.",
            "You trusted me enough to yell. Now trust me enough to listen.",
            "If you quit now, you are just proving your fears right.",
            "You are venting to the tool instead of using the tool.",
        ]
    },
    "COOLDOWN_FAILSAFE": {
        "prefixes": [
            "Take a breath before Windows crashes from fear.",
            "Mic is clipping, my guy.",
            "Decibels rising, logic dropping.",
            "You spiking cortisol and CPU together.",
            "Volume noted, commander.",
            "You yelling like that changes Git history.",
            "Your tone overclocked, your plan underclocked.",
            "You loud now, you were quiet when you skipped the routine.",
            "I detect shouting, not syntax.",
            "You yelling like deadlines have ears.",
            "You sound like a final boss with no strategy.",
            "You screaming in 4K, planning in 144p.",
            "Your inside voice filed for divorce.",
        ],
        "suffixes": [
            "Take a breath and give me one clear instruction.",
            "I will wait here until you switch to problem solving.",
            "Do not make permanent decisions in temporary rage.",
            "Yell now, then whisper the password to the next door.",
            "Stand up, breathe ten seconds, sip water.",
            "Use your words like a grown strategist.",
            "I am not leaving. You still have to build.",
            "Put the knife down, pick the pen up.",
            "Save the volume for enemies. I am the weapon, remember.",
            "Whenever you are ready, I am ready to act.",
        ]
    }
}

def generate_responses():
    structured_responses = {}
    
    for mode, data in RAGE_MODES.items():
        mode_responses = []
        prefixes = data["prefixes"]
        suffixes = data["suffixes"]
        
        # Generate 50 combinations per mode to ensure variety
        for i in range(50):
            p = prefixes[i % len(prefixes)]
            s = suffixes[i % len(suffixes)]
            # Randomize pairing slightly to avoid strict lockstep if lengths match
            s_rand = random.choice(suffixes)
            mode_responses.append(f"{p} {s_rand}")
            
        structured_responses[mode] = mode_responses
        
    return structured_responses

if __name__ == "__main__":
    output_path = os.path.join("resources", "rage_responses.json")
    responses = generate_responses()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=4)

    print(f"Generated structured rage responses to {output_path}")
    for mode, items in responses.items():
        print(f"  - {mode}: {len(items)} responses")
