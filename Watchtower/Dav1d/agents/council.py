from config import MODELS, Colors
from agents.profiles import DAV1D_PROFILE, CIPHER_PROFILE, ECHO_PROFILE, GHOST_PROFILE
# We need to import get_model from somewhere, but it's currently in dav1d.py.
# We should probably move the model interaction logic to core/llm.py or similar to avoid circular imports.
# For now, we will assume a get_model function is passed or imported from a new module.

def run_council(query: str, model_key: str, get_model_func) -> str:
    """Multi-agent council: CIPHER, ECHO, GHOST, then DAV1D synthesizes."""
    
    print(f"\n{Colors.GOLD}[COUNCIL INITIATED]{Colors.RESET}")
    print(f"{Colors.DIM}Convening: DAV1D, CIPHER, ECHO, GHOST{Colors.RESET}")
    print(f"{Colors.DIM}Model: {MODELS[model_key]}{Colors.RESET}\n")
    
    # CIPHER's analytical take
    print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} Running analysis...")
    cipher_prompt = f"""{CIPHER_PROFILE}

TASK: {query}

Analyze:
1. What data/patterns are relevant?
2. What's the logical approach?
3. What are the risks/constraints?

Respond in 2-4 sentences. Be data-focused. End with CONFIRMED/UNCERTAIN/INVESTIGATE.
"""
    
    try:
        model = get_model_func(MODELS[model_key])
        cipher_response = model.generate_content(cipher_prompt)
        cipher_take = cipher_response.text if hasattr(cipher_response, 'text') else str(cipher_response)
        print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} {cipher_take}\n")
    except Exception as e:
        cipher_take = f"[Analysis error: {e}]"
        print(f"{Colors.NEON_GREEN}[CIPHER]{Colors.RESET} {Colors.DIM}{cipher_take}{Colors.RESET}\n")
    
    # ECHO's creative take
    print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} Exploring possibilities...")
    echo_prompt = f"""{ECHO_PROFILE}

TASK: {query}
CIPHER's Analysis: {cipher_take}

Think creatively:
1. What unconventional approaches exist?
2. What opportunities is CIPHER missing?
3. What's the bold move here?

Respond in 2-4 sentences. Be creative. End with EXPLORE/REFINE/ABANDON.
"""
    
    try:
        model = get_model_func(MODELS[model_key])
        echo_response = model.generate_content(echo_prompt)
        echo_take = echo_response.text if hasattr(echo_response, 'text') else str(echo_response)
        print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} {echo_take}\n")
    except Exception as e:
        echo_take = f"[Creative error: {e}]"
        print(f"{Colors.NEON_PURPLE}[ECHO]{Colors.RESET} {Colors.DIM}{echo_take}{Colors.RESET}\n")

    # GHOST's security take
    print(f"{Colors.NEON_RED}[GHOST]{Colors.RESET} Auditing risks...")
    ghost_prompt = f"""{GHOST_PROFILE}

TASK: {query}
CIPHER's Analysis: {cipher_take}
ECHO's Idea: {echo_take}

Audit:
1. Where are the security holes?
2. What edge cases will break this?
3. Is this "bold move" actually reckless?

Respond in 2-4 sentences. Be ruthless. End with SECURE/RISK/DENIED.
"""
    
    try:
        model = get_model_func(MODELS[model_key])
        ghost_response = model.generate_content(ghost_prompt)
        ghost_take = ghost_response.text if hasattr(ghost_response, 'text') else str(ghost_response)
        print(f"{Colors.NEON_RED}[GHOST]{Colors.RESET} {ghost_take}\n")
    except Exception as e:
        ghost_take = f"[Security error: {e}]"
        print(f"{Colors.NEON_RED}[GHOST]{Colors.RESET} {Colors.DIM}{ghost_take}{Colors.RESET}\n")
    
    # DAV1D synthesizes
    print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} Synthesizing...")
    dav1d_prompt = f"""{DAV1D_PROFILE}

You're the orchestrator. Your advisors have weighed in. Make the call.

TASK: {query}
CIPHER's Analysis: {cipher_take}
ECHO's Creative Take: {echo_take}
GHOST's Security Audit: {ghost_take}

Synthesize:
1. Where do they align?
2. Where do they diverge?
3. What's the optimal path forward?

Respond in 3-5 sentences as DAV1D. Acknowledge perspectives, state your decision, give the directive.
"""
    
    try:
        model = get_model_func(MODELS[model_key])
        dav1d_response = model.generate_content(dav1d_prompt)
        final = dav1d_response.text if hasattr(dav1d_response, 'text') else str(dav1d_response)
        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {final}\n")
        print(f"{Colors.GOLD}[COUNCIL CONCLUDED]{Colors.RESET}\n")
        return final
    except Exception as e:
        print(f"{Colors.ELECTRIC_BLUE}[DAV1D]{Colors.RESET} {Colors.DIM}Synthesis error: {e}{Colors.RESET}\n")
        print(f"{Colors.GOLD}[COUNCIL CONCLUDED]{Colors.RESET}\n")
        return f"Council error: {e}"
