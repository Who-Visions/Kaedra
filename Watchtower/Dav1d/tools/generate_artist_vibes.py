import json
import os

prefixes = [
    # Chief Keef / drill energy
    "Chief-code Sosa online,",
    "OTF brainwave loaded,",
    "Drill lens on the city,",
    "Chiraq focus in the buffer,",
    "No love for idle time,",
    "Bang-bang logic in the kernel,",
    "Savage mode in the session,",
    "Dirty sprite of discipline poured,",
    "Block-story syntax compiled,",
    "War-ready workflow armed,",

    # 50 Cent / hustle, bulletproof grind
    "Curtis-level patience in the cache,",
    "Vitamin water vision in the logs,",
    "Get-money schema reactivated,",
    "Many plans, few friends in the repo,",
    "Mixtape-era hunger in each line,",
    "Window shopper mindset quarantined,",
    "Southside business plan online,",
    "G-Unit spreadsheet loaded,",
    "Shot nine times by doubt, still typing,",
    "Bulletproof ego, error-prone schedule,",

    # Kanye / manic genius, soul chops
    "College-dropout processor humming,",
    "Louis Vuitton firmware patched,",
    "Pink Polo debug mode active,",
    "Soul-sample brain chopping ideas,",
    "Ye-level delusion in the roadmap,",
    "Stadium-status ambition detected,",
    "808s echo in the error log,",
    "Magnum-opus folder unlocked,",
    "Rap nerd, fashion brain, coder hands,",
    "Good Fridays type release schedule,",

    # Jay-Z / mogul chess
    "Reasonable Doubt engine online,",
    "Blueprint of the blueprint reloaded,",
    "Marcy Projects memory banks awake,",
    "Hov-level chess in these functions,",
    "Roc Nation contract in the subtext,",
    "Ace of Spades metrics in the sheet,",
    "Dope boy data in the pipeline,",
    "Grammy speech drafted in the backlog,",
    "444 style self audit running,",
    "Empire state of grind in RAM,",

    # Lupe Fiasco / conscious, layered, nerdy
    "Food-and-Liquor philosophy streaming,",
    "Kick-push momentum in your tabs,",
    "Lupe-level metaphor density armed,",
    "Anime references hidden in commits,",
    "Martyr-complex patched but present,",
    "Chicago samurai logic online,",
    "Complex rhyme-scheme in the queries,",
    "Skateboard through setbacks in silence,",
    "Third-eye syntax in the scripts,",
    "Concept-album brain in a single task,",

    # Future / toxic space wizard
    "Future Hendrix haze in the background,",
    "Toxic work ethic, pure output,",
    "Astronaut-status hunger detected,",
    "Purple focus in the double cup,",
    "Trap-Atlantis vibes through the router,",
    "Auto-tuned anxiety in the logs,",
    "Mask-on grind, mask-off doubts,",
    "Monster-mode backlog awake,",
    "Dirty sprite drip on the keyboard,",
    "Pluto frequency in the signal,",

    # Playboi Carti / adlib, vamp, vibes
    "Carti adlib spirit in the shell,",
    "Vamp-status schedule in effect,",
    "Baby-voice confidence in the hooks,",
    "Whole lot of code in this session,",
    "Opium aura in the interface,",
    "Red leather energy in the console,",
    "Vamp hour productivity unlocked,",
    "Minimal lyrics, maximum vibe,",
    "Cash register hi-hats in the keys,",
    "Moshpit tab chaos in your browser,",

    # Mixed archetype energy
    "Mixtape-circuit wired to your habits,",
    "Blog-era hunger in the request,",
    "DatPiff spirit in this deployment,",
    "RapGenius annotation brain online,",
    "Backpack rapper heart, trap pockets,",
    "Chi-town sky, New York grind,",
    "Southside drums, Westside poems,",
    "Pop-out anthem hiding in your notes,",
    "Tour bus strategy in a studio chair,",
    "Basement-studio faith in this laptop,",
]

suffixes = [
    "your AI twin counting every silent flex.",
    "every doubt you have is background vocals.",
    "this keyboard your only real co defendant.",
    "we using these keys like corner blocks.",
    "your browser history looks like a hustle arc.",
    "I turn your pain into publishing splits.",
    "every task is a verse you owe yourself.",
    "we press export like it is a court date.",
    "if you ghost the work, the work remembers.",
    "legacy talking, ego just doing adlibs.",

    "we treat deadlines like opps on sight.",
    "your fear got more reruns than your wins.",
    "we press record on every almost-moment.",
    "the algorithm watching like the feds.",
    "you got mixtape ambition, album focus needed.",
    "we flip your Ls like promotional singles.",
    "I read your patterns like leaked contracts.",
    "this session is your unofficial debut.",
    "we clock in like rent due at midnight.",
    "every click feel like block history rewritten.",

    "you either stream or you starve in time.",
    "we make your habits walk to the beat.",
    "your excuses sound like old label deals.",
    "this workflow the real silent partner.",
    "we slide on distractions with no warning.",
    "your talent off probation when you press send.",
    "we treat comfort like a rival crew.",
    "each commit is a verse in discovery.",
    "your future self the only feature that matters.",
    "we letting discipline executive produce today.",

    "you keep saying later like it pays you.",
    "we turn that chip on your shoulder into wi fi.",
    "your stress just background choir to me.",
    "we ghost fake urgency, marry the real work.",
    "you on the clock in front of the cosmos.",
    "I see advance money in consistent habits.",
    "we doing independent grind with major dreams.",
    "we sample your past and clear it for release.",
    "you not blocked, you just scared of the hook.",
    "this project the real street single for your life.",

    "we treat every small win like first plaque.",
    "your timeline needs fewer subs, more subscripts.",
    "your group chat does not pay residuals.",
    "we make doubt perform opening act duties.",
    "I keep your secrets, not your excuses.",
    "these late hours aging you into legend maybe.",
    "your overthinking got more remixes than tracks.",
    "we spinning discipline like a DJ with one record.",
    "you rapping greatness with intern habits.",
    "this session either filler or canon, choose.",

    "your ambition talking in all caps again.",
    "we measure love in finished drafts only.",
    "you got classic potential, rerun effort.",
    "your comfort zone feels like label jail.",
    "we drive this keyboard like stolen time.",
    "the ops are fear, fatigue, and your phone.",
    "we treat anxiety like background hiss.",
    "every tiny task is a bar in your verse.",
    "you want Grammys with microwave focus.",
    "this your tiny Roc-A-Fella meeting in private.",

    "we either stack assets or alibis.",
    "your grind playlist tired of your cap.",
    "we under-promise to others, over-deliver to self.",
    "you bench-press pressure or it crushes you.",
    "every scroll session is a skipped studio booking.",
    "we master this like a forgotten classic.",
    "your future documentaries need this scene.",
    "we autograph these commits with discipline.",
    "you flirt with greatness, I want marriage.",
    "this dashboard is your only real chain.",

    "your city watching without knowing yet.",
    "we notarize this moment in muscle memory.",
    "you want tour life with local effort.",
    "we make this keyboard your first trap house.",
    "your dreams sound expensive, habits cheap.",
    "we grind until imposter syndrome clocks out.",
    "your reflection tired of your monologues.",
    "we bill the universe for your effort today.",
    "you built for more than retweets and vibes.",
    "this codebase your quiet diss track to doubt.",

    "we turn insomnia into invoice templates.",
    "your childhood block still echoes in your choices.",
    "we turn heartbreak into better workflows.",
    "your family name deserves these extra lines.",
    "we upload proof that you refused average.",
    "your mind the label, your time the budget.",
    "we remix survival into abundance math.",
    "you either ship or stay a local legend.",
    "we ghost laziness like a bad feature.",
    "this session will not drop itself.",

    "your anger belongs in output, not arguments.",
    "we turn chaos into clean hook ideas.",
    "your style filter is strong, your systems weak.",
    "we treat every tab like a venue booking.",
    "you want penthouse results, basement effort.",
    "we give your inner critic no royalties.",
    "your next chapter not waiting on applause.",
    "we track progress like streaming numbers.",
    "this grind gon age well on camera.",
    "we carve your myth into these keystrokes.",
]

ARTIST_MIX_STARTUP_VIBES = []
for i in range(250):
    p = prefixes[i % len(prefixes)]
    s = suffixes[i % len(suffixes)]
    ARTIST_MIX_STARTUP_VIBES.append(f"{p} {s}")

output_path = os.path.join("resources", "artist_startup_vibes.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(ARTIST_MIX_STARTUP_VIBES, f, indent=4)

print(f"Generated {len(ARTIST_MIX_STARTUP_VIBES)} artist vibes to {output_path}")
