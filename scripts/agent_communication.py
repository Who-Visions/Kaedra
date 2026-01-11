"""
Agent Communication - Inter-Agent Messaging for Kaedra Orchestrator

Enables Kaedra to communicate with other agents on the system:
- BLADE (System AI Brain)
- Claude (Senior Dev)
- Gemini (Research)
- Vision (Creative)
- Anti-Gravity (Coding)
- Codex (Code Generation)
- Operator (Computer Use)
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


# Agent Locations (HQ_WhoArt system)
AGENT_PATHS = {
    "blade": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/blade_agent.py",
    "claude": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/claude_agent.py",
    "gemini": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/gemini_agent.py",
    "vision": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/vision_agent.py",
    "antigravity": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/antigravity_agent.py",
    "codex": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/codex_agent.py",
    "operator": "/mnt/c/Users/super/Watchtower/HQ_WhoArt/agents/operator_agent.py",
}


class AgentCommunicator:
    """Handles communication between Kaedra and other agents."""

    def __init__(self):
        """Initialize agent communicator."""
        self.message_history: List[Dict] = []
        self.hq_root = "/mnt/c/Users/super/Watchtower/HQ_WhoArt"

    def send_message(
        self,
        agent_name: str,
        message: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Send a message to another agent and get response.

        Args:
            agent_name: Name of agent (blade, claude, gemini, etc.)
            message: Message to send
            timeout: Response timeout in seconds

        Returns:
            Response from agent
        """
        agent_name = agent_name.lower()

        result = {
            "from": "kaedra",
            "to": agent_name,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "response": None
        }

        # Check if agent exists
        if agent_name not in AGENT_PATHS:
            result["status"] = "error"
            result["error"] = f"Unknown agent: {agent_name}. Available: {', '.join(AGENT_PATHS.keys())}"
            return result

        agent_path = AGENT_PATHS[agent_name]

        # Check if agent file exists
        if not os.path.exists(agent_path):
            result["status"] = "error"
            result["error"] = f"Agent file not found: {agent_path}"
            return result

        try:
            # Execute agent with message
            process = subprocess.run(
                ['python3', agent_path, message],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(agent_path)
            )

            result["response"] = process.stdout.strip()
            result["stderr"] = process.stderr.strip() if process.stderr else None
            result["returncode"] = process.returncode

            if process.returncode != 0:
                result["status"] = "error"

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = f"Agent {agent_name} did not respond within {timeout}s"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        # Log message
        self.message_history.append(result)

        return result

    def broadcast_message(
        self,
        message: str,
        agents: List[str] = None,
        timeout: int = 30
    ) -> Dict[str, Dict]:
        """
        Broadcast message to multiple agents.

        Args:
            message: Message to broadcast
            agents: List of agent names (or None for all)
            timeout: Response timeout per agent

        Returns:
            Dict mapping agent names to responses
        """
        target_agents = agents or list(AGENT_PATHS.keys())

        responses = {}

        for agent in target_agents:
            responses[agent] = self.send_message(agent, message, timeout)

        return responses

    def query_agent(
        self,
        agent_name: str,
        query: str,
        timeout: int = 30
    ) -> str:
        """
        Query an agent and get just the response text.

        Args:
            agent_name: Agent to query
            query: Query string
            timeout: Timeout in seconds

        Returns:
            Response text (or error message)
        """
        result = self.send_message(agent_name, query, timeout)

        if result["status"] == "success":
            return result["response"]
        else:
            return f"[ERROR] {result.get('error', 'Unknown error')}"

    def check_agent_availability(self, agent_name: str) -> bool:
        """
        Check if agent is available.

        Args:
            agent_name: Name of agent

        Returns:
            Boolean availability
        """
        if agent_name not in AGENT_PATHS:
            return False

        agent_path = AGENT_PATHS[agent_name]
        return os.path.exists(agent_path)

    def list_available_agents(self) -> List[str]:
        """
        List all available agents.

        Returns:
            List of agent names
        """
        available = []

        for agent_name, agent_path in AGENT_PATHS.items():
            if os.path.exists(agent_path):
                available.append(agent_name)

        return available

    def get_message_history(self, limit: int = 10) -> List[Dict]:
        """Get recent message history."""
        return self.message_history[-limit:]

    def create_agent_group(
        self,
        group_name: str,
        agents: List[str]
    ) -> Dict[str, Any]:
        """
        Create a group of agents for coordinated tasks.

        Args:
            group_name: Name of the group
            agents: List of agent names

        Returns:
            Group configuration
        """
        # Verify all agents exist
        unavailable = [a for a in agents if not self.check_agent_availability(a)]

        if unavailable:
            return {
                "status": "error",
                "error": f"Unavailable agents: {', '.join(unavailable)}"
            }

        group = {
            "name": group_name,
            "agents": agents,
            "created": datetime.now().isoformat(),
            "status": "active"
        }

        # Save group configuration
        groups_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "memory",
            "agent_groups"
        )
        os.makedirs(groups_dir, exist_ok=True)

        group_file = os.path.join(groups_dir, f"{group_name}.json")

        with open(group_file, 'w') as f:
            json.dump(group, f, indent=2)

        return {
            "status": "success",
            "group": group,
            "path": group_file
        }


# Singleton for orchestrator use
agent_communicator = AgentCommunicator()


if __name__ == "__main__":
    # Test agent communication
    print("📡 Agent Communication Test\n")

    comm = AgentCommunicator()

    # List available agents
    print("Available agents:")
    agents = comm.list_available_agents()
    for agent in agents:
        print(f"  - {agent.upper()}")

    print("\nTesting communication with BLADE...")

    # Test messaging
    response = comm.send_message("blade", "Hello from Kaedra, the orchestrator. Status check.")

    print(f"  Status: {response['status']}")
    print(f"  Response: {response.get('response', 'No response')}")

    if response.get('stderr'):
        print(f"  stderr: {response['stderr']}")
