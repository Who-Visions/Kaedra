"""
DAV1D Speech Enhancement - Natural Emoji Integration
Adds visual flair to speech without overwhelming the text
"""

import random
import re
from agents.emoji_dict import get_emoji, WORD_TO_EMOJI, EMOJI_DICT

# ══════════════════════════════════════════════════════════════════════════════
# 🎯 SPEECH ENHANCEMENT SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

# How often to add emojis (0.0 = never, 1.0 = always)
EMOJI_DENSITY = {
    'minimal': 0.15,   # Very subtle - 1-2 emojis per response
    'light': 0.25,     # Light touch - occasional emojis
    'balanced': 0.35,  # Good balance - default
    'expressive': 0.50,  # More personality
    'maximum': 0.65,   # Heavy but not overwhelming
}

DEFAULT_DENSITY = 'balanced'

# Key phrases that should ALWAYS get an emoji for emphasis
# Key phrases that should ALWAYS get an emoji for emphasis
EMPHASIS_PATTERNS = {
    # DAV3 CREATIVE SUITE (Who Visions Identity)
    r'\bphoto\b': '📸',
    r'\bphotographer\b': '📸',
    r'\bvideo\b': '🎥',
    r'\bvideographer\b': '🎥',
    r'\bedit\b': '🎞️',
    r'\beditor\b': '🎞️',
    r'\bstream\b': '🔴',
    r'\bstreamer\b': '🎙️',
    r'\bgame\b': '🎮',
    r'\bgamer\b': '🎮',
    r'\brap\b': '🎤',
    r'\brapper\b': '🎤',
    r'\bvision\b': '👁️',
    r'\bvisions\b': '👁️',
    r'\bwho\s*visions\b': '👁️✨',
    r'\bvisual\b': '🎨',
    r'\bcreative\b': '🧠✨',
    r'\bentertain\b': '🎭',
    r'\bentertainer\b': '🌟',
    r'\bcontent\b': '📱',
    r'\bmedia\b': '🎬',
    r'\bshoot\b': '📸',
    r'\bfilm\b': '🎥',
    r'\blens\b': '🔍',
    r'\bframe\b': '🖼️',
    r'\brender\b': '⏳',
    r'\bexport\b': '💾',
    
    # CREATIVE / MUSIC
    r'\bmusic\b': '🎵',
    r'\bsong\b': '🎶',
    r'\bbeat\b': '🥁',
    r'\bstudio\b': '🎙️',
    r'\brecord\b': '⏺️',
    r'\btrack\b': '🎹',
    r'\bmix\b': '🎚️',
    r'\bvolume\b': '🔊',
    r'\bheadphones\b': '🎧',
    r'\bmic\b': '🎤',
    r'\bflow\b': '🌊',
    r'\bvibe\b': '✨',
    r'\bart\b': '🎨',
    r'\bdesign\b': '🖌️',
    r'\bcreate\b': '✨',
    r'\bcreative\b': '👨‍🎨',
    r'\bwrite\b': '✍️',
    r'\bvideo\b': '📹',
    r'\bcamera\b': '📸',
    r'\bfilm\b': '🎬',
    r'\bscene\b': '🎭',
    
    # TECH / CODE
    r'\bcode\b': '💻',
    r'\bdev\b': '🧑‍💻',
    r'\bbuild\b': '🏗️',
    r'\bship\b': '🚢',
    r'\bdeploy\b': '🚀',
    r'\bstack\b': '📚',
    r'\bdatabase\b': '🗄️',
    r'\bserver\b': '🖥️',
    r'\bcloud\b': '☁️',
    r'\bapi\b': '🔌',
    r'\bbug\b': '🐛',
    r'\bdebug\b': '🔍',
    r'\bfix\b': '🔧',
    r'\btool\b': '🛠️',
    r'\brobot\b': '🤖',
    r'\bai\b': '🧠',
    r'\bdata\b': '📊',
    r'\balgo\b': '🧮',
    r'\bscript\b': '📜',
    r'\bterminal\b': '📟',
    
    # HYPE / STATUS
    r'\bfire\b': '🔥',
    r'\blit\b': '🔥',
    r'\brocket\b': '🚀',
    r'\bwin\b': '🏆',
    r'\bgoat\b': '🐐',
    r'\bking\b': '👑',
    r'\bboss\b': '😎',
    r'\bmoney\b': '💰',
    r'\bcash\b': '💵',
    r'\bpaid\b': '💸',
    r'\bbag\b': '💰',
    r'\brich\b': '💎',
    r'\bgold\b': '🥇',
    r'\bstar\b': '⭐',
    r'\bflash\b': '⚡',
    r'\bfast\b': '💨',
    r'\bspeed\b': '🏎️',
    r'\bpower\b': '🔋',
    r'\benergy\b': '⚡',
    r'\b100\b': '💯',
    r'\bperfect\b': '💯',
    
    # MINDSET / VIBES
    r'\bthink\b': '🤔',
    r'\bidea\b': '💡',
    r'\bplan\b': '🗺️',
    r'\bmap\b': '📍',
    r'\bgoal\b': '🎯',
    r'\bfocus\b': '🧘',
    r'\bzen\b': '🧘',
    r'\bcalm\b': '😌',
    r'\brage\b': '🤬',
    r'\bangry\b': '😠',
    r'\bhate\b': '😤',
    r'\blove\b': '❤️',
    r'\bheart\b': '💖',
    r'\bcool\b': '😎',
    r'\bcold\b': '🥶',
    r'\bice\b': '🧊',
    r'\bhot\b': '🥵',
    r'\bghost\b': '👻',
    r'\bdead\b': '💀',
    r'\bkill\b': '🔪',
    r'\bmagic\b': '✨',
    r'\bwizard\b': '🧙‍♂️',
    r'\bninja\b': '🥷',
}

# Sentence-ending emojis for specific contexts
CONTEXT_EMOJIS = {
    'question': ['🤔', '❓', '🧐', '🤨', '🤷‍♂️'],
    'excitement': ['🔥', '🚀', '💯', '⚡', '🤯', '🤩', '😤', '🐐'],
    'success': ['✅', '🎯', '🏆', '💪', '🥇', '👑', '🥂', '🎉'],
    'code': ['💻', '⚙️', '🛠️', '🔧', '🧑‍💻', '🤖', '👾', '💾'],
    'money': ['💰', '💸', '💵', '📈', '💎', '🤑', '🏦', '💳'],
    'creative': ['🎨', '✍️', '🎭', '🎬', '📸', '🎵', '🎹', '🖌️'],
    'music': ['🎵', '🎶', '🎧', '🎤', '🎹', '🥁', '🎼', '🔊'],
    'warning': ['⚠️', '🚨', '❗', '🛑', '🚧', '🚩'],
    'error': ['❌', '🚫', '⛔', '💀', '☠️', '💔'],
    'celebration': ['🎉', '🎊', '🥳', '✨', '🎈', '🍾', '🍻'],
    'chill': ['😎', '😌', '🧘', '🧊', '🌊', '🍃', '☕'],
    'rage': ['🤬', '😤', '😠', '💢', '💥', '👿', '🖕'],
}


# ══════════════════════════════════════════════════════════════════════════════
# 🎨 CORE ENHANCEMENT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def enhance_speech(text: str, density: str = DEFAULT_DENSITY, vibe: str = None) -> str:
    """
    Add emojis to DAV1D's speech naturally.
    
    Args:
        text: The response text to enhance
        density: How many emojis to add ('minimal', 'light', 'balanced', 'expressive', 'maximum')
        vibe: Optionalvibe/context (HYPE, RAGE, CODE, MONEY, etc.)
    
    Returns:
        Enhanced text with strategic emoji placement
    """
    if not text or len(text) < 10:
        return text
    
    # Get density rate
    rate = EMOJI_DENSITY.get(density, EMOJI_DENSITY['balanced'])
    
    # Enhanced text
    enhanced = text
    
    # Step 1: Add emphasis emojis for key patterns (always)
    enhanced = add_emphasis_emojis(enhanced)
    
    # Step 2: Add word-based emojis (controlled by density)
    enhanced = add_word_emojis(enhanced, rate)
    
    # Step 3: Add contextual ending emoji if appropriate
    enhanced = add_context_emoji(enhanced, vibe)
    
    return enhanced


def add_emphasis_emojis(text: str) -> str:
    """Add emojis for high-impact words that should always be emphasized."""
    enhanced = text
    
    for pattern, emoji in EMPHASIS_PATTERNS.items():
        # Only add if emoji isn't already nearby
        matches = list(re.finditer(pattern, enhanced, re.IGNORECASE))
        for match in matches:
            word = match.group()
            pos = match.start()
            
            # Check if there's already an emoji nearby (within 5 chars)
            if not has_emoji_nearby(enhanced, pos, radius=5):
                # Add emoji after the word
                enhanced = enhanced[:match.end()] + ' ' + emoji + enhanced[match.end():]
                
    return enhanced


def add_word_emojis(text: str, rate: float) -> str:
    """Add emojis for common words based on density rate."""
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        result.append(word)
        
        # Clean word for matching (remove punctuation)
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        
        # Check if word has emoji mapping
        if clean_word in WORD_TO_EMOJI:
            # Random chance based on density
            if random.random() < rate:
                # Don't add if we just added one
                if len(result) > 1 and is_emoji(result[-2]):
                    continue
                    
                emoji = WORD_TO_EMOJI[clean_word]
                result.append(emoji)
    
    return ' '.join(result)


def add_context_emoji(text: str, vibe: str = None) -> str:
    """Add a contextual emoji at the end if appropriate."""
    # Don't add if text already ends with emoji
    if text and is_emoji(text.strip()[-1]):
        return text
    
    # Detect context from text if vibe not provided
    if not vibe:
        vibe = detect_context(text)
    
    # Add appropriate emoji
    if vibe and vibe.lower() in CONTEXT_EMOJIS:
        emoji = random.choice(CONTEXT_EMOJIS[vibe.lower()])
        return text.rstrip() + ' ' + emoji
    
    return text


def detect_context(text: str) -> str:
    """Detect the context/vibe from the text."""
    text_lower = text.lower()
    
    # Check for different contexts
    if '?' in text:
        return 'question'
    elif any(word in text_lower for word in ['great', 'awesome', 'amazing', 'perfect', 'excellent']):
        return 'success'
    elif any(word in text_lower for word in ['code', 'build', 'deploy', 'function', 'compile']):
        return 'code'
    elif any(word in text_lower for word in ['money', 'cash', 'paid', 'profit', 'revenue']):
        return 'money'
    elif any(word in text_lower for word in ['error', 'wrong', 'failed', 'broken']):
        return 'error'
    elif any(word in text_lower for word in ['warning', 'careful', 'watch out']):
        return 'warning'
    elif any(word in text_lower for word in ['congrats', 'celebrate', 'won', 'victory']):
        return 'celebration'
    elif any(word in text_lower for word in ['fire', 'lit', 'bang', 'hype']):
        return 'excitement'
    
    return None


def has_emoji_nearby(text: str, position: int, radius: int = 5) -> bool:
    """Check if there's already an emoji near this position."""
    start = max(0, position - radius)
    end = min(len(text), position + radius)
    snippet = text[start:end]
    
    # Check if snippet contains any emoji
    for char in snippet:
        if is_emoji(char):
            return True
    
    return False


def is_emoji(char: str) -> bool:
    """Check if a character/string is an emoji."""
    if not char:
        return False
    
    # Simple check: emojis are typically in certain Unicode ranges
    # This is a basic check - emojis are in ranges like:
    # U+1F300-U+1F9FF, U+2600-U+26FF, U+2700-U+27BF, etc.
    for c in char:
        code_point = ord(c)
        if (0x1F300 <= code_point <= 0x1F9FF or 
            0x2600 <= code_point <= 0x27BF or
            0x1F000 <= code_point <= 0x1F2FF):
            return True
    
    return False


# ══════════════════════════════════════════════════════════════════════════════
# 🚀 CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def add_start_emoji(text: str, emoji: str = None, vibe: str = None) -> str:
    """Add an emoji at the start of the response."""
    if emoji:
        return f"{emoji} {text}"
    elif vibe:
        vibe_emoji = get_vibe_emoji(vibe)
        return f"{vibe_emoji} {text}"
    return text


def add_end_emoji(text: str, emoji: str = None, vibe: str = None) -> str:
    """Add an emoji at the end of the response."""
    if emoji:
        return f"{text} {emoji}"
    elif vibe:
        vibe_emoji = get_vibe_emoji(vibe)
        return f"{text} {vibe_emoji}"
    return text


def get_vibe_emoji(vibe: str) -> str:
    """Get emoji for a specific vibe."""
    vibe_map = {
        'RAGE': '😤',
        'HYPE': '🔥',
        'CHILL': '😎',
        'ANALYTICAL': '🧠',
        'COLLABORATIVE': '🤝',
        'CYNICAL': '😑',
        'DEFAULT': '💭',
        'THINKING': '🤔',
        'CODE': '💻',
        'MONEY': '💰',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️',
    }
    return vibe_map.get(vibe.upper(), '💬')


def strip_emojis(text: str) -> str:
    """Remove all emojis from text (useful for testing or logging)."""
    return ''.join(char for char in text if not is_emoji(char))


# ══════════════════════════════════════════════════════════════════════════════
# 🎯 EXAMPLE USAGE
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test examples
    test_texts = [
        "Let me think about that code solution real quick.",
        "That's fire! We crushed the target with perfect execution.",
        "Warning: this might cause an error in your build process.",
        "The brain needs time to process. Let's analyze the data.",
        "We're making money with this rocket ship idea!",
    ]
    
    print("🎨 DAV1D Speech Enhancement Examples:\n")
    
    for text in test_texts:
        print(f"Original: {text}")
        print(f"Enhanced: {enhance_speech(text, 'balanced')}")
        print()
