from config import RESOURCES_DIR, Colors

def load_profile(name: str) -> str:
    """Loads agent profile from text file."""
    try:
        profile_path = RESOURCES_DIR / "profiles" / f"{name}.txt"
        if profile_path.exists():
            with open(profile_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"{Colors.GOLD}[WARN] Could not load profile {name}: {e}{Colors.RESET}")
    
    # Fallback minimal profile if file missing
    return f"You are {name.upper()}. Be helpful."

# Load all profiles
DAV1D_PROFILE = load_profile("dav1d")
CIPHER_PROFILE = load_profile("cipher")
ECHO_PROFILE = load_profile("echo")
NANO_PROFILE = load_profile("nano")
GHOST_PROFILE = load_profile("ghost")
