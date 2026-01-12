
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("startup_debug")

print("[*] Simulating Reasoning Engine Startup...")

try:
    # 1. Add current dir to path (mimics cloud environment)
    sys.path.append(os.getcwd())
    print(f"[*] CWD: {os.getcwd()}")
    print(f"[*] Python Path: {sys.path}")

    # 2. Attempt strict imports of core dependencies
    print("[*] Importing core dependencies...")
    import google.genai
    import google.api_core
    import pydantic
    print("[+] Core dependencies loaded.")

    # 3. Attempt to import the Agent module
    print("[*] Importing kaedra.agents.kaedra_agent...")
    from kaedra.agents.kaedra import KaedraAgent
    print("[+] Agent module imported.")

    # 4. Attempt Instantiation (Lazy)
    print("[*] Instantiating KaedraAgent (Lazy Mode)...")
    from kaedra.services.prompt import PromptService
    agent = KaedraAgent(prompt_service=PromptService())
    print("[+] Agent instantiated.")

    # 5. Check serialization safety
    print("[*] Checking picklability...")
    import pickle
    try:
        dumped = pickle.dumps(agent)
        print(f"[+] Pickle successful. Size: {len(dumped)} bytes")
        
        # 6. Unpickle (Simulation of Worker Startup)
        print("[*] Unpickling agent (Worker Simulation)...")
        restored_agent = pickle.loads(dumped)
        print("[+] Agent restored.")
        
    except Exception as e:
        print(f"[!] PICKLE ERROR: {e}")
        raise e

    print("[SUCCESS] Startup Simulation Passed.")

except ImportError as e:
    print(f"[!] IMPORT ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[!] RUNTIME ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
