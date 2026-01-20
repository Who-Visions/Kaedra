"""
Kaedra Local CLI - Shadow Tactician Interface

Entry point for local interaction with the Kaedra Orchestrator.
Provides a command-line interface for multi-agent coordination.
"""

from typing import Dict, Final, Any

import vertexai
from vertexai.preview import reasoning_engines

from orchestrator import KaedraOrchestrator
from scripts.status_monitor import visualize_system_health
from scripts.agent_router import AGENT_REGISTRY
from scripts.mission_planner import plan_mission, visualize_plan

# === Configuration ===
AGENT_RESOURCE_NAME: Final[str] = (
    "projects/627440283840/locations/us-central1/"
    "reasoningEngines/5765957723313143808"
)

# Model shortcuts
MODELS: Final[Dict[str, str]] = {
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

# pylint: disable=too-few-public-methods
class Colors:
    """ANSI Color Codes for CLI."""
    PINK: Final[str] = '\033[95m'      # Magenta/Pink
    YELLOW: Final[str] = '\033[93m'    # Yellow
    CYAN: Final[str] = '\033[96m'      # Cyan
    RESET: Final[str] = '\033[0m'      # Reset
    BOLD: Final[str] = '\033[1m'       # Bold

def print_banner() -> None:
    """Print the Kaedra CLI banner."""
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


def print_help() -> None:
    """Print the command reference."""
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

def handle_system_command(cmd: str, orchestrator: KaedraOrchestrator) -> None:
    """Handle system diagnostic commands."""
    if cmd in ["/models", "/status"]:
        print("[KAEDRA] Processing status probe...")
        status = orchestrator.get_system_status()
        print("\n[ORCHESTRATOR]")
        print(f"  Status: {status['orchestrator']['status']}")
        is_conn = status['orchestrator']['vertex_ai_connected']
        print(f"  Vertex AI: {'Connected' if is_conn else 'Disconnected'}")
        print(f"  Model: {status['orchestrator']['model']}")
        print("\n[AGENTS]")
        for agent_name, details in status['system_health']['agent_details'].items():
            print(f"  {agent_name.upper()}: {details['status']}")
    elif cmd == "/health":
        print("[KAEDRA] Generating system health report...")
        status = orchestrator.get_system_status()
        print(visualize_system_health(status['system_health']))
    elif cmd == "/agents":
        print("\n[AGENT REGISTRY]\n")
        for agent_id, info in AGENT_REGISTRY.items():
            print(f"  {agent_id.upper()}")
            print(f"    Role: {info['role']}")
            print(f"    API: {info['api']}")
            print(f"    Capabilities: {', '.join(info['capabilities'][:3])}...")
            print()


def handle_mission_command(cmd: str, orchestrator: KaedraOrchestrator) -> None:
    """Handle routing and mission planning."""
    if cmd == "/route":
        route_task = input("  Enter task to analyze: ").strip()
        if route_task:
            routing = orchestrator.analyze_and_route(route_task)
            print("\n[ROUTING ANALYSIS]")
            print(f"  Task Type: {routing['analysis']['task_type']}")
            print(f"  Complexity: {routing['analysis']['complexity']}")
            print(f"  Multi-Agent: {routing['is_multi_agent']}")
            agent_list = [a.upper() for a in routing['analysis']['suggested_agents']]
            print(f"  Suggested Agents: {', '.join(agent_list)}")
            print(f"  Needs Orchestration: {routing['needs_orchestration']}")
    elif cmd == "/plan":
        plan_task = input("  Enter mission to plan: ").strip()
        if plan_task:
            print("\n[KAEDRA] Planning mission...")
            mission = plan_mission(plan_task)
            print(visualize_plan(mission))


def handle_tech_command(cmd: str, orchestrator: KaedraOrchestrator) -> None:
    """Handle technical stack and tools info."""
    if cmd == "/tools":
        print("\n[KAEDRA] Local Tools & Capabilities:\n")
        tools = orchestrator.get_cli_capabilities()
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool}")
        print("\n[TECH STACK]")
        tech_ref = orchestrator.get_tech_stack_reference()
        print(f"  Status: {tech_ref['status']}")
        print("  Path: TECH_STACK.md")
        print("\n  Critical Rules:")
        for rule in tech_ref['critical_rules']:
            print(f"    - {rule}")
    elif cmd == "/stack":
        tech_ref = orchestrator.get_tech_stack_reference()
        print("\n[WHO VISIONS LLC - OFFICIAL TECH STACK v1.3]\n")
        print("  Core:")
        print(f"    Node.js: {tech_ref['versions']['nodejs']}")
        print(f"    React: {tech_ref['versions']['react']}")
        print(f"    Next.js: {tech_ref['versions']['nextjs']}")
        print(f"    TypeScript: {tech_ref['versions']['typescript']}")
        print("\n  Styling & UI (Web):")
        print(f"    Tailwind CSS: {tech_ref['versions']['tailwind']}")
        print(f"    Shadcn UI: {tech_ref['versions']['shadcn']} (standard)")
        print(f"    NyxUI: {tech_ref['versions']['nyxui']} (future-forward)")
        print(f"    ReactBits: {tech_ref['versions']['reactbits']} (animations)")
        print("\n  Mobile:")
        print(f"    Expo: {tech_ref['versions']['expo']}")
        print(f"    NativeWind: {tech_ref['versions']['nativewind']}")
        print(f"    Kotlin: {tech_ref['versions']['kotlin']}")
        print("\n  3D & Graphics:")
        print(f"    Three.js: {tech_ref['versions']['threejs']}")
        print("\n  Full documentation: See TECH_STACK.md")


def handle_communication_command(cmd: str, orchestrator: KaedraOrchestrator) -> None:
    """Handle inter-agent communication."""
    if cmd == "/talk":
        agent_list = "blade/claude/gemini/vision/antigravity/codex"
        agent_name = input(f"  Which agent? ({agent_list}): ").strip().lower()
        message = input("  Message: ").strip()
        if agent_name and message:
            print(f"\n[KAEDRA] Sending message to {agent_name.upper()}...")
            response = orchestrator.comm.send_message(agent_name, message)
            print(f"\n[{agent_name.upper()}] {response.get('response', 'No')}")
            if response['status'] != 'success':
                print(f"  Error: {response.get('error', 'Unknown error')}")
    elif cmd == "/list":
        print("\n[AVAILABLE AGENTS]\n")
        agents = orchestrator.comm.list_available_agents()
        if agents:
            for agent in agents:
                print(f"  ✓ {agent.upper()}")
        else:
            print("  No agents found")


def process_cloud_query(user_input: str, current_model: str, agent: Any) -> None:
    """Send user input to cloud reasoning engine."""
    print(f"[KAEDRA] Processing with {MODELS[current_model]}...")
    full_instruction = build_instruction(user_input, current_model)

    # pylint: disable=no-member
    response = agent.query(user_instruction=full_instruction)

    if isinstance(response, dict):
        message = response.get("message", str(response))
        print(f"\n{message}")
        if "RENDER" in message.upper():
            print("\n[SYSTEM] ⚙️  Initiating Render Protocol...")
    else:
        print(f"\n{response}")


def handle_model_switch(cmd: str) -> str:
    """Handle model switching logic."""
    if cmd == "/flash":
        model = "flash"
        print(f"[SYSTEM] ⚡ Model switched to: {MODELS[model]}")
        print("         Cost: ~$0.008 per query (cheapest)")
    elif cmd == "/pro":
        model = "pro"
        print(f"[SYSTEM] 🎯 Model switched to: {MODELS[model]}")
        print("         Cost: ~$0.031 per query (balanced)")
    elif cmd == "/ultra":
        model = "ultra"
        print(f"[SYSTEM] 🔥 Model switched to: {MODELS[model]}")
        print("         Cost: ~$0.038 per query (most powerful)")
    else:
        model = ""
    return model


def main():
    """Main CLI execution loop."""
    print_banner()

    # Initialize connection
    vertexai.init(location="us-central1")

    # Current model tracking (local state only, for now)
    current_model = "flash"  # Default: fastest and cheapest

    # Initialize orchestrator
    try:
        orchestrator = KaedraOrchestrator(model=current_model)
        agent = reasoning_engines.ReasoningEngine(AGENT_RESOURCE_NAME)
        print("[✓] LINK ESTABLISHED. KAEDRA ORCHESTRATOR ONLINE.")
        print(f"[✓] Current Model: {MODELS[current_model]}")
        print("[✓] Listening to: BLADE (Razor 15) + Who_Art (ProArt 13')")
        print("    Type /help for commands\n")

        while True:
            try:
                user_input = input(f"\n[YOU|{current_model}] >> ").strip()
                if not user_input:
                    continue

                cmd = user_input.lower()
                if cmd == "/exit":
                    print("[KAEDRA] Severing link. Goodbye, Commander.")
                    break
                if cmd == "/help":
                    print_help()
                    continue

                if cmd in ["/flash", "/pro", "/ultra"]:
                    current_model = handle_model_switch(cmd) or current_model
                    continue

                if cmd in ["/models", "/status", "/health", "/agents"]:
                    handle_system_command(cmd, orchestrator)
                    continue

                if cmd in ["/route", "/plan"]:
                    handle_mission_command(cmd, orchestrator)
                    continue

                if cmd in ["/tools", "/stack"]:
                    handle_tech_command(cmd, orchestrator)
                    continue

                if cmd in ["/talk", "/list"]:
                    handle_communication_command(cmd, orchestrator)
                    continue

                process_cloud_query(user_input, current_model, agent)

            except KeyboardInterrupt:
                print("\n[KAEDRA] Interrupt detected. Severing link.")
                break

    except vertexai.errors.VertexAIError as v_err:
        print(f"\n[!] VERTEX AI ERROR: {v_err}")
    except RuntimeError as r_err:
        print(f"\n[!] RUNTIME ERROR: {r_err}")

if __name__ == "__main__":
    main()
