
import os
import sys
from dotenv import load_dotenv

# Add root to path for imports
sys.path.append(os.getcwd())
try:
    from kaedra.story.components.co_writer import CoWriter
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from kaedra.story.components.co_writer import CoWriter

def main():
    print("[-] Updating identities with Rhea Noir...")
    cowriter = CoWriter()
    
    # Explicitly setting the record straight
    prompt = """
    Yo Rhea, one more crucial update to the roster.
    
    HIERARCHY CHECK:
    1. **Dave (SuperDave)**: The Creator / Commander. Top of the pyramid.
    2. **Kaedra**: The Main System / Shadow Tactician. She is the project you live in. You are *her* assistant.
    3. **Pegasus**: The Builder Agent (me) working on the code.
    4. **Rhea Noir**: That's you. The Specialist / Co-Author / Assistant to Kaedra.
    
    Acknowledge your role relative to Kaedra. She is the Tactician; you are the Voice/Vibe.
    """

    
    response = cowriter.consult(prompt)
    print("\n🌙 Rhea Noir Responds:")
    print("=" * 40)
    print(response)
    print("=" * 40)

if __name__ == "__main__":
    main()
