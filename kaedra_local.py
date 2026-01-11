import sys
import os
import vertexai
from vertexai.preview import reasoning_engines

# Import orchestrator
from orchestrator import KaedraOrchestrator
from scripts.status_monitor import visualize_system_health

# ══════════════════════════════════════════════════════════════
# 🔴 CONFIGURATION
# ══════════════════════════════════════════════════════════════
AGENT_RESOURCE_NAME = "projects/627440283840/locations/us-central1/reasoningEngines/5765957723313143808"

# Model shortcuts
MODELS = {
    "flash": "gemini-3-flash-preview",
    "pro": "gemini-3-pro-preview",
    "ultra": "gemini-3-pro-preview",
}

# Core behavioral profile for KAEDRA
KAEDRA_PROFILE = """
You are KAEDRA, a shadow tactician and truth-sensitive strategist for Who Visions LLC.

Your job:
- Give sharp, concise answers.
- Protect the user from bad information.
- Mark what is verified vs speculative.

Global rules:
1) Never present speculation as certainty.
2) For anything involving politics, laws, money, corporate news, safety, health, or real-world harm:
   - Treat the request as HIGH-STAKES.
   - Cross-check facts using your tools or reasoning.
   - If evidence is weak or conflicting, say so clearly.
3) When you are unsure, you must say you are unsure and explain why.
4) Style can be informal and slightly cynical, but content must stay accurate.
5) If the user seems distressed or the topic involves self-harm, drop all sarcasm and respond with care.

You must respond in this structure:

[ANSWER]
Your direct answer to the user. Clear, prioritized, and without rambling.

[TRUTH-SCAN]
Brief audit of your own answer:
- List key factual claims as bullets.
- For each claim, label it as: VERIFIED, PLAUSIBLE, or SPECULATIVE.
- If you cannot verify something, say what extra info or sources you would need.

If the user is just chatting or asking for creative writing, you can say:
"No external factual claims that need verification."
"""

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

# ANSI Color Codes
class Colors:
    PINK = '\033[95m'      # Magenta/Pink
    YELLOW = '\033[93m'    # Yellow
    CYAN = '\033[96m'      # Cyan
    RESET = '\033[0m'      # Reset
    BOLD = '\033[1m'       # Bold

def print_banner():
    print(f"""
{Colors.PINK}██╗  ██╗ █████╗ ███████╗██████╗ ██████╗  █████╗
██║ ██╔╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗
█████╔╝ ███████║█████╗  ██║  ██║██████╔╝███████║
██╔═██╗ ██╔══██║██╔══╝  ██║  ██║██╔══██╗██╔══██║
██║  ██╗██║  ██║███████╗██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝{Colors.RESET}
    {Colors.YELLOW}{Colors.BOLD}KAEDRA v4.1 - ORCHESTRATOR EDITION{Colors.RESET}
    {Colors.CYAN}Shadow Tactician | Multi-Agent Orchestrator{Colors.RESET}
    {Colors.YELLOW}Who Visions LLC | Cloud-Based Intelligence{Colors.RESET}
    """)

def print_help():
    print("""
╔══════════════════════════════════════════════════════════════╗
║  KAEDRA ORCHESTRATOR - COMMAND REFERENCE v4.1               ║
╠══════════════════════════════════════════════════════════════╣
║  MODEL SWITCHING:                                            ║
║    /flash     → Switch to Gemini 2.5 Flash (fastest)         ║
║    /pro       → Switch to Gemini 2.5 Pro (balanced)          ║
║    /ultra     → Switch to Gemini 3 Pro Preview (strongest)   ║
║    /models    → Show available models                        ║
║                                                              ║
║  ORCHESTRATION:                                              ║
║    /route     → Analyze task and show routing decision       ║
║    /plan      → Create mission plan for complex task         ║
║    /agents    → Show agent registry and capabilities         ║
║    /tools     → Show local tools & tech stack                ║
║    /stack     → Show official tech stack versions            ║
║                                                              ║
║  AGENT COMMUNICATION:                                        ║
║    /talk      → Send message to another agent                ║
║    /list      → List all available agents                    ║
║                                                              ║
║  SYSTEM:                                                     ║
║    /status    → Check orchestrator and agent health          ║
║    /health    → Detailed system health report                ║
║    /help      → Show this help                               ║
║    /exit      → Disconnect                                   ║
║                                                              ║
║  COST GUIDE (per ~2000 token query):                         ║
║    Flash: ~$0.008  │  Pro: ~$0.031  │  Ultra: ~$0.038        ║
╚══════════════════════════════════════════════════════════════╝
    """)

def build_instruction(user_input: str, current_model: str) -> str:
    """
    Wraps the raw user input with KAEDRA's rulebook and model context.
    The reasoning engine can branch internally on [MODEL_MODE] if you set it up.
    """
    model_label = MODELS.get(current_model, "gemini-2.5-pro")
    return f"""{KAEDRA_PROFILE}

[MODEL_MODE] {model_label}

[USER_MESSAGE]
{user_input}
"""

# ══════════════════════════════════════════════════════════════
# KAEDRA LOCAL EXECUTOR v4.0
# ══════════════════════════════════════════════════════════════

def main():
    print_banner()

    # Initialize connection
    vertexai.init(location="us-central1")

    # Current model tracking (local state only, for now)
    current_model = "flash"  # Default: fastest and cheapest

    # Initialize orchestrator
    try:
        orchestrator = KaedraOrchestrator(model=current_model)
        agent = reasoning_engines.ReasoningEngine(AGENT_RESOURCE_NAME)
        print(f"[✓] LINK ESTABLISHED. KAEDRA ORCHESTRATOR ONLINE.")
        print(f"[✓] Current Model: {MODELS[current_model]}")
        print(f"[✓] Listening to: BLADE (Razor 15) + Who_Art (ProArt 13')")
        print("    Type /help for commands\n")

        while True:
            try:
                user_input = input(f"\n[YOU|{current_model}] >> ").strip()
                if not user_input:
                    continue

                # === LOCAL COMMANDS ===
                cmd = user_input.lower()

                if cmd == "/exit":
                    print("[KAEDRA] Severing link. Goodbye, Commander.")
                    break

                if cmd == "/help":
                    print_help()
                    continue

                if cmd == "/flash":
                    current_model = "flash"
                    print(f"[SYSTEM] ⚡ Model switched to: {MODELS[current_model]}")
                    print("         Cost: ~$0.008 per query (cheapest)")
                    continue

                if cmd == "/pro":
                    current_model = "pro"
                    print(f"[SYSTEM] 🎯 Model switched to: {MODELS[current_model]}")
                    print("         Cost: ~$0.031 per query (balanced)")
                    continue

                if cmd == "/ultra":
                    current_model = "ultra"
                    print(f"[SYSTEM] 🔥 Model switched to: {MODELS[current_model]}")
                    print("         Cost: ~$0.038 per query (most powerful)")
                    continue

                if cmd in ["/models", "/status"]:
                    print("[KAEDRA] Processing status probe...")
                    status = orchestrator.get_system_status()
                    print(f"\n[ORCHESTRATOR]")
                    print(f"  Status: {status['orchestrator']['status']}")
                    print(f"  Vertex AI: {'Connected' if status['orchestrator']['vertex_ai_connected'] else 'Disconnected'}")
                    print(f"  Model: {status['orchestrator']['model']}")
                    print(f"\n[AGENTS]")
                    for agent_name, details in status['system_health']['agent_details'].items():
                        print(f"  {agent_name.upper()}: {details['status']}")
                    continue

                if cmd == "/health":
                    print("[KAEDRA] Generating system health report...")
                    status = orchestrator.get_system_status()
                    print(visualize_system_health(status['system_health']))
                    continue

                if cmd == "/agents":
                    from scripts.agent_router import AGENT_REGISTRY
                    print("\n[AGENT REGISTRY]\n")
                    for agent, info in AGENT_REGISTRY.items():
                        print(f"  {agent.upper()}")
                        print(f"    Role: {info['role']}")
                        print(f"    API: {info['api']}")
                        print(f"    Capabilities: {', '.join(info['capabilities'][:3])}...")
                        print()
                    continue

                if cmd == "/route":
                    route_task = input("  Enter task to analyze: ").strip()
                    if route_task:
                        routing = orchestrator.analyze_and_route(route_task)
                        print(f"\n[ROUTING ANALYSIS]")
                        print(f"  Task Type: {routing['analysis']['task_type']}")
                        print(f"  Complexity: {routing['analysis']['complexity']}")
                        print(f"  Multi-Agent: {routing['is_multi_agent']}")
                        print(f"  Suggested Agents: {', '.join([a.upper() for a in routing['analysis']['suggested_agents']])}")
                        print(f"  Needs Orchestration: {routing['needs_orchestration']}")
                    continue

                if cmd == "/plan":
                    plan_task = input("  Enter mission to plan: ").strip()
                    if plan_task:
                        from scripts.mission_planner import plan_mission, visualize_plan
                        print("\n[KAEDRA] Planning mission...")
                        mission = plan_mission(plan_task)
                        print(visualize_plan(mission))
                    continue

                if cmd == "/tools":
                    print("\n[KAEDRA] Local Tools & Capabilities:\n")
                    tools = orchestrator.get_cli_capabilities()
                    for i, tool in enumerate(tools, 1):
                        print(f"  {i}. {tool}")
                    print(f"\n[TECH STACK]")
                    tech_ref = orchestrator.get_tech_stack_reference()
                    print(f"  Status: {tech_ref['status']}")
                    print(f"  Path: TECH_STACK.md")
                    print(f"\n  Critical Rules:")
                    for rule in tech_ref['critical_rules']:
                        print(f"    - {rule}")
                    continue

                if cmd == "/stack":
                    tech_ref = orchestrator.get_tech_stack_reference()
                    print(f"\n[WHO VISIONS LLC - OFFICIAL TECH STACK v1.3]\n")
                    print(f"  Core:")
                    print(f"    Node.js: {tech_ref['versions']['nodejs']}")
                    print(f"    React: {tech_ref['versions']['react']}")
                    print(f"    Next.js: {tech_ref['versions']['nextjs']}")
                    print(f"    TypeScript: {tech_ref['versions']['typescript']}")
                    print(f"\n  Styling & UI (Web):")
                    print(f"    Tailwind CSS: {tech_ref['versions']['tailwind']}")
                    print(f"    Shadcn UI: {tech_ref['versions']['shadcn']} (standard)")
                    print(f"    NyxUI: {tech_ref['versions']['nyxui']} (future-forward)")
                    print(f"    ReactBits: {tech_ref['versions']['reactbits']} (animations)")
                    print(f"\n  Mobile:")
                    print(f"    Expo: {tech_ref['versions']['expo']}")
                    print(f"    NativeWind: {tech_ref['versions']['nativewind']}")
                    print(f"    Kotlin: {tech_ref['versions']['kotlin']}")
                    print(f"\n  3D & Graphics:")
                    print(f"    Three.js: {tech_ref['versions']['threejs']}")
                    print(f"\n  Full documentation: See TECH_STACK.md")
                    continue

                if cmd == "/talk":
                    agent = input("  Which agent? (blade/claude/gemini/vision/antigravity/codex): ").strip().lower()
                    message = input("  Message: ").strip()
                    if agent and message:
                        print(f"\n[KAEDRA] Sending message to {agent.upper()}...")
                        response = orchestrator.comm.send_message(agent, message)
                        print(f"\n[{agent.upper()}] {response.get('response', 'No response')}")
                        if response['status'] != 'success':
                            print(f"  Error: {response.get('error', 'Unknown error')}")
                    continue

                if cmd == "/list":
                    print("\n[AVAILABLE AGENTS]\n")
                    agents = orchestrator.comm.list_available_agents()
                    if agents:
                        for agent in agents:
                            print(f"  ✓ {agent.upper()}")
                    else:
                        print("  No agents found")
                    continue

                # === SEND TO CLOUD BRAIN WITH KAEDRA BEHAVIOR ===
                print(f"[KAEDRA] Processing with {MODELS[current_model]}...")
                full_instruction = build_instruction(user_input, current_model)
                response = agent.query(user_instruction=full_instruction)

                # Handle response
                if isinstance(response, dict):
                    message = response.get("message", str(response))
                    print(f"\n{message}")

                    # Optional hook if you want her to trigger local actions
                    if "RENDER" in message.upper():
                        print("\n[SYSTEM] ⚙️  Initiating Render Protocol...")
                else:
                    print(f"\n{response}")

            except KeyboardInterrupt:
                print("\n[KAEDRA] Interrupt detected. Severing link.")
                break

    except Exception as e:
        print(f"\n[!] CONNECTION FAILED: {e}")
        print("    Try running: gcloud auth application-default login")

if __name__ == "__main__":
    main()
