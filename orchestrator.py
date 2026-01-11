"""
Kaedra Orchestrator - Multi-Agent Coordination Engine

Core orchestration engine that coordinates multiple AI agents
through Vertex AI Reasoning Engine integration.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import vertexai
from vertexai.preview import reasoning_engines

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from agent_router import route_task, analyze_task, AGENT_REGISTRY
from mission_planner import plan_mission, visualize_plan, MissionPlan
from status_monitor import (
    check_system_health,
    visualize_system_health,
    AgentStatus,
    log_performance_metrics
)
from cli_tools import CLITools
from browser_tools import BrowserToolsSync
from code_execution import CodeExecutor
from agent_communication import AgentCommunicator

# Vertex AI Configuration
VERTEX_PROJECT_ID = "627440283840"
VERTEX_LOCATION = "us-central1"
REASONING_ENGINE_ID = "5765957723313143808"
AGENT_RESOURCE_NAME = f"projects/{VERTEX_PROJECT_ID}/locations/{VERTEX_LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"


class KaedraOrchestrator:
    """
    Main orchestrator class for Kaedra.

    Coordinates multi-agent operations using Vertex AI Reasoning Engine
    for strategic intelligence and decision-making.
    """

    def __init__(self, model: str = "pro"):
        """
        Initialize Kaedra Orchestrator.

        Args:
            model: Default Gemini model (flash, pro, ultra)
        """
        self.model = model
        self.models = {
            "flash": "gemini-3-flash-preview",
            "pro": "gemini-3-pro-preview",
            "ultra": "gemini-3-pro-preview"
        }

        # Initialize Vertex AI
        vertexai.init(location=VERTEX_LOCATION)

        try:
            self.reasoning_engine = reasoning_engines.ReasoningEngine(AGENT_RESOURCE_NAME)
            self.connected = True
            print(f"[✓] Kaedra Orchestrator online. Vertex AI connected.")
        except Exception as e:
            self.connected = False
            print(f"[!] Warning: Vertex AI connection failed: {e}")
            print(f"[!] Orchestrator running in local mode.")

        # Initialize CLI tools
        self.cli = CLITools()

        # Initialize browser automation tools (Playwright/Chromium)
        self.browser = BrowserToolsSync(headless=True)

        # Initialize code execution tools
        self.code = CodeExecutor()

        # Initialize agent communication
        self.comm = AgentCommunicator()

        # Load tech stack knowledge
        self.tech_stack = self._load_tech_stack()

        # Initialize orchestrator status
        self.status = AgentStatus("kaedra")
        self.status.update_status("online", task="Orchestration ready")
        self.status.save()

    def _load_tech_stack(self) -> Dict[str, str]:
        """
        Load official tech stack knowledge base.

        Returns:
            Dict with tech stack info
        """
        tech_stack_path = os.path.join(
            os.path.dirname(__file__),
            "TECH_STACK.md"
        )

        tech_stack = {
            "loaded": False,
            "path": tech_stack_path,
            "versions": {
                "nodejs": "25.2.1",
                "react": "19.2.0",
                "nextjs": "16.0.3",
                "tailwind": "3.4",
                "shadcn": "latest",
                "nyxui": "latest",
                "reactbits": "latest",
                "nativewind": "v4",
                "threejs": "latest",
                "typescript": "latest",
                "expo": "latest",
                "kotlin": "2.2.21"
            }
        }

        if os.path.exists(tech_stack_path):
            try:
                with open(tech_stack_path, 'r') as f:
                    tech_stack["content"] = f.read()
                    tech_stack["loaded"] = True
            except Exception as e:
                print(f"[!] Warning: Could not load tech stack: {e}")

        return tech_stack

    def analyze_and_route(self, task: str) -> Dict[str, Any]:
        """
        Analyze task and determine routing strategy.

        Args:
            task: Task description

        Returns:
            Dict with routing decision and metadata
        """
        analysis = analyze_task(task)

        # Use Vertex AI for complex strategic analysis if connected
        if self.connected and analysis["complexity"] in ["complex", "moderate"]:
            strategic_analysis = self._get_strategic_intelligence(task, analysis)
            analysis["strategic_insight"] = strategic_analysis

        # Determine if orchestration is needed
        needs_orchestration = (
            analysis["is_multi_agent"] or
            analysis["complexity"] == "complex" or
            len(analysis["suggested_agents"]) > 1
        )

        return {
            "task": task,
            "needs_orchestration": needs_orchestration,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    def _get_strategic_intelligence(self, task: str, analysis: Dict) -> str:
        """
        Query Vertex AI Reasoning Engine for strategic intelligence.

        Args:
            task: Task description
            analysis: Initial task analysis

        Returns:
            Strategic intelligence from Kaedra's reasoning engine
        """
        if not self.connected:
            return "Local analysis only (Vertex AI not connected)"

        try:
            prompt = f"""
            As Kaedra, Shadow Tactician and Orchestrator, analyze this task:

            TASK: {task}

            INITIAL ANALYSIS:
            - Complexity: {analysis['complexity']}
            - Multi-agent: {analysis['is_multi_agent']}
            - Suggested agents: {', '.join(analysis['suggested_agents'])}

            Provide:
            1. Strategic assessment of task complexity and risks
            2. Recommended orchestration approach
            3. Agent coordination strategy
            4. Potential failure points and mitigation

            Keep response tactical and concise.
            """

            response = self.reasoning_engine.query(user_instruction=prompt)

            if isinstance(response, dict):
                return response.get("message", str(response))
            return str(response)

        except Exception as e:
            return f"Strategic analysis unavailable: {e}"

    def execute_simple_task(self, task: str, agent: str) -> Dict[str, Any]:
        """
        Execute a simple single-agent task.

        Args:
            task: Task description
            agent: Agent to execute task

        Returns:
            Execution result dict
        """
        agent_info = AGENT_REGISTRY.get(agent, {})

        print(f"[KAEDRA] Routing to {agent.upper()}")
        print(f"  Role: {agent_info.get('role', 'Unknown')}")
        print(f"  API: {agent_info.get('api', 'Unknown')}")

        # Update agent status
        agent_status = AgentStatus.load(agent)
        agent_status.update_status("busy", task=task)
        agent_status.save()

        # TODO: Actual agent execution would happen here
        # For now, return placeholder
        result = {
            "status": "delegated",
            "agent": agent,
            "task": task,
            "message": f"Task delegated to {agent.upper()}. Agent should execute independently.",
            "timestamp": datetime.now().isoformat()
        }

        # Update agent back to idle
        agent_status.update_status("idle")
        agent_status.record_task_completion(success=True, response_time=0.0)
        agent_status.save()

        return result

    def execute_mission(self, mission: MissionPlan) -> Dict[str, Any]:
        """
        Execute a complex multi-agent mission.

        Args:
            mission: MissionPlan object with task breakdown

        Returns:
            Mission execution result
        """
        print(f"[KAEDRA] Executing mission: {mission.mission_id}")
        print(visualize_plan(mission))

        results = []

        for task in mission.tasks:
            # Check dependencies
            if task["dependencies"]:
                print(f"  Waiting for dependencies: {', '.join(task['dependencies'])}")

            # Execute task
            print(f"\n  Executing: {task['task_id']}")
            print(f"  Agent: {task['agent'].upper()}")

            agent_result = self.execute_simple_task(
                task=task["description"],
                agent=task["agent"]
            )

            task["status"] = "completed"
            results.append(agent_result)

        mission.status = "completed"
        mission.save()

        return {
            "status": "completed",
            "mission_id": mission.mission_id,
            "tasks_completed": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    def process_task(self, task: str) -> Dict[str, Any]:
        """
        Main entry point for task processing.

        Analyzes task, determines if orchestration is needed,
        and routes/executes accordingly.

        Args:
            task: Task description

        Returns:
            Task execution result
        """
        # Update orchestrator status
        self.status.update_status("processing", task=task)
        self.status.save()

        # Analyze and route
        routing = self.analyze_and_route(task)

        if routing["needs_orchestration"]:
            # Complex mission - plan and execute
            print(f"[KAEDRA] Complex task detected. Planning mission...")

            mission = plan_mission(task)
            result = self.execute_mission(mission)

        else:
            # Simple task - direct routing
            primary_agent = routing["analysis"]["suggested_agents"][0]
            result = self.execute_simple_task(task, primary_agent)

        # Update orchestrator status back to idle
        self.status.update_status("idle")
        self.status.record_task_completion(success=True, response_time=1.0)
        self.status.save()

        return result

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status report.

        Returns:
            System status dict
        """
        health = check_system_health()

        return {
            "orchestrator": {
                "status": "online" if self.connected else "local_mode",
                "vertex_ai_connected": self.connected,
                "model": self.models[self.model],
                "current_task": self.status.current_task
            },
            "system_health": health,
            "timestamp": datetime.now().isoformat()
        }

    def switch_model(self, model: str) -> bool:
        """
        Switch Gemini model for reasoning engine.

        Args:
            model: Model name (flash, pro, ultra)

        Returns:
            Success boolean
        """
        if model not in self.models:
            return False

        self.model = model
        print(f"[KAEDRA] Switched to {self.models[model]}")
        return True

    def execute_cli_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a CLI command using Kaedra's CLI tools.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Command execution result
        """
        print(f"[KAEDRA] Executing CLI: {command}")

        result = self.cli.run_command(command, timeout=timeout)

        if result["status"] == "success":
            print(f"[KAEDRA] ✓ Command completed")
        else:
            print(f"[KAEDRA] ✗ Command failed: {result.get('stderr', 'Unknown error')}")

        return result

    def get_cli_capabilities(self) -> List[str]:
        """
        Get list of available CLI and browser capabilities.

        Returns:
            List of tool categories
        """
        return [
            "File Operations (read, write, list, copy, move, remove)",
            "Git Operations (status, diff, log, add, commit, push, pull)",
            "Process Management (list, kill)",
            "System Diagnostics (disk usage, memory, system info)",
            "Search Operations (find files, grep)",
            "Package Management (pip, npm)",
            "Shell Command Execution (any bash/shell command)",
            "Browser Automation (navigate, click, type, screenshot) - Playwright/Chromium",
            "Code Execution (TypeScript, JavaScript, Python, Kotlin)",
            "Project Creation (Next.js 16.0.3, Expo, React Native)"
        ]

    def get_tech_stack_reference(self) -> Dict[str, Any]:
        """
        Get tech stack reference for agents.

        Returns:
            Tech stack information
        """
        return {
            "status": "loaded" if self.tech_stack["loaded"] else "not_loaded",
            "path": self.tech_stack["path"],
            "versions": self.tech_stack["versions"],
            "instructions": "All agents MUST reference TECH_STACK.md before coding tasks",
            "critical_rules": [
                "Use Node.js 25.2.1 (verify with node --version)",
                "Use React 19.2.0",
                "Use Next.js 16.0.3",
                "Use Tailwind CSS 3.4 (web)",
                "Use NativeWind v4 (mobile)",
                "Use TypeScript (no JavaScript)",
                "Use Shadcn UI (standard) or NyxUI (future-forward)",
                "Use ReactBits for animations",
                "Use Three.js for 3D games/graphics",
                "Use Server Components by default (Next.js)",
                "Use Expo for mobile projects",
                "Use Kotlin 2.2.21 for native/KMP"
            ]
        }


def main():
    """CLI for testing orchestrator."""
    orchestrator = KaedraOrchestrator()

    print("\n" + "="*70)
    print("KAEDRA ORCHESTRATOR - TEST MODE")
    print("="*70)

    # Test tasks
    test_tasks = [
        "Research Next.js 16 features",
        "Debug the authentication flow in the app",
        "Research competitor sites and build a comparison dashboard"
    ]

    for task in test_tasks:
        print(f"\n{'─'*70}")
        print(f"TASK: {task}")
        print(f"{'─'*70}\n")

        result = orchestrator.process_task(task)

        print(f"\n[RESULT]")
        print(json.dumps(result, indent=2))

    # System status
    print(f"\n{'='*70}")
    print("SYSTEM STATUS")
    print(f"{'='*70}\n")

    status = orchestrator.get_system_status()
    print(visualize_system_health(status["system_health"]))


if __name__ == "__main__":
    main()
