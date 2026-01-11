"""
Agent Router - Task Routing Logic for Kaedra Orchestrator

Routes incoming tasks to the appropriate agent based on:
- Task type and complexity
- Agent capabilities
- Current agent availability and load
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Agent capability registry
AGENT_REGISTRY = {
    "claude": {
        "role": "Senior Dev / CLI Execution Specialist",
        "api": "Anthropic",
        "model": "claude-sonnet-4-5",
        "capabilities": [
            "shell_commands",
            "file_operations",
            "debugging",
            "git_operations",
            "system_diagnostics",
            "cli_mastery",
            "code_review",
            "troubleshooting"
        ],
        "keywords": ["cli", "shell", "bash", "git", "debug", "troubleshoot", "file", "command"],
        "priority_for": ["cli", "debugging", "system_operations"]
    },
    "gemini": {
        "role": "Web & Cloud Connectivity Specialist",
        "api": "Google AI Studio",
        "model": "gemini-3-flash-preview",
        "capabilities": [
            "web_research",
            "url_fetching",
            "data_extraction",
            "search",
            "analysis",
            "fact_checking"
        ],
        "keywords": ["research", "search", "web", "find", "lookup", "investigate", "data"],
        "priority_for": ["research", "web_search", "data_extraction"]
    },
    "vision": {
        "role": "Creative Content Specialist",
        "api": "Google AI Studio",
        "model": "gemini-3-flash-preview",
        "capabilities": [
            "content_creation",
            "design_concepts",
            "visual_planning",
            "creative_strategy",
            "brand_work"
        ],
        "keywords": ["design", "creative", "content", "visual", "brand", "marketing", "copy"],
        "priority_for": ["creative", "design", "content"]
    },
    "antigravity": {
        "role": "Coding & UX/UI Specialist",
        "api": "Google AI Studio",
        "model": "gemini-3-flash-preview",
        "capabilities": [
            "complex_coding",
            "ux_ui_development",
            "frontend_development",
            "app_architecture",
            "nextjs",
            "react"
        ],
        "keywords": ["code", "app", "frontend", "ui", "ux", "nextjs", "react", "component"],
        "priority_for": ["frontend_dev", "ui_ux", "complex_coding"]
    },
    "codex": {
        "role": "Code Generation Specialist",
        "api": "OpenAI",
        "model": "gpt-4",
        "capabilities": [
            "code_generation",
            "code_patterns",
            "architecture_design",
            "refactoring",
            "optimization"
        ],
        "keywords": ["generate", "pattern", "architecture", "refactor", "optimize", "structure"],
        "priority_for": ["code_gen", "architecture", "patterns"]
    },
    "operator": {
        "role": "Computer Use Specialist",
        "api": "Gemini 2.0 Computer Use",
        "model": "gemini-3-flash-preview",
        "capabilities": [
            "browser_automation",
            "gui_interaction",
            "web_navigation",
            "form_filling",
            "screenshot_analysis"
        ],
        "keywords": ["browser", "navigate", "click", "automate", "gui", "webpage", "screenshot"],
        "priority_for": ["browser_automation", "gui_ops"]
    },
    "kaedra": {
        "role": "Strategic Intelligence Officer / Orchestrator",
        "api": "Vertex AI Reasoning Engine",
        "model": "gemini-2.5-pro",
        "capabilities": [
            "strategic_planning",
            "truth_analysis",
            "emotional_intelligence",
            "tactical_recursion",
            "multi_agent_coordination",
            "orchestration"
        ],
        "keywords": ["strategy", "plan", "analyze", "truth", "coordinate", "orchestrate"],
        "priority_for": ["strategy", "orchestration", "complex_planning"]
    }
}


def analyze_task(task_description: str) -> Dict[str, any]:
    """
    Analyze task to determine complexity and type.

    Args:
        task_description: Natural language task description

    Returns:
        Dict with task_type, complexity, and suggested_agents
    """
    task_lower = task_description.lower()

    # Detect multi-agent need
    multi_agent_keywords = ["and", "then", "also", "both", "multiple", "coordinate"]
    is_multi_agent = any(keyword in task_lower for keyword in multi_agent_keywords)

    # Analyze for agent matches
    agent_scores = {}

    for agent_name, agent_info in AGENT_REGISTRY.items():
        score = 0

        # Keyword matching
        for keyword in agent_info["keywords"]:
            if keyword in task_lower:
                score += 2

        # Priority matching (weighted higher)
        for priority in agent_info["priority_for"]:
            if priority.replace("_", " ") in task_lower:
                score += 5

        if score > 0:
            agent_scores[agent_name] = score

    # Sort by score
    ranked_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)

    # Determine complexity
    complexity_indicators = {
        "simple": ["just", "quick", "simple", "basic"],
        "moderate": ["create", "build", "implement", "setup"],
        "complex": ["architect", "design system", "full stack", "deploy", "integrate"]
    }

    complexity = "moderate"  # default
    for level, indicators in complexity_indicators.items():
        if any(indicator in task_lower for indicator in indicators):
            complexity = level
            break

    return {
        "task_type": ranked_agents[0][0] if ranked_agents else "kaedra",
        "complexity": complexity,
        "is_multi_agent": is_multi_agent,
        "agent_scores": dict(ranked_agents[:3]),  # Top 3
        "suggested_agents": [agent[0] for agent in ranked_agents[:3]]
    }


def route_task(task_description: str, force_agent: Optional[str] = None) -> Tuple[str, Dict]:
    """
    Route a task to the appropriate agent.

    Args:
        task_description: Natural language task description
        force_agent: Optional agent name to force routing to

    Returns:
        Tuple of (agent_name, routing_metadata)
    """
    if force_agent:
        if force_agent not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {force_agent}")
        return force_agent, {
            "routing_reason": "forced",
            "timestamp": datetime.now().isoformat()
        }

    analysis = analyze_task(task_description)

    # If multi-agent, route to Kaedra for orchestration
    if analysis["is_multi_agent"] or analysis["complexity"] == "complex":
        return "kaedra", {
            "routing_reason": "multi_agent_orchestration",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    # Single agent routing
    primary_agent = analysis["suggested_agents"][0] if analysis["suggested_agents"] else "kaedra"

    return primary_agent, {
        "routing_reason": "capability_match",
        "analysis": analysis,
        "timestamp": datetime.now().isoformat()
    }


def check_agent_availability(agent_name: str) -> bool:
    """
    Check if an agent is currently available.

    Args:
        agent_name: Name of the agent

    Returns:
        Boolean indicating availability
    """
    if agent_name not in AGENT_REGISTRY:
        return False

    # Check agent status file
    status_file = os.path.join(
        os.path.dirname(__file__),
        "..",
        "memory",
        "agents",
        f"{agent_name}_status.json"
    )

    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
                return status.get("status") in ["online", "idle"]
        except:
            pass

    # Default to available if no status file
    return True


def get_agent_capabilities(agent_name: str) -> List[str]:
    """
    Get list of capabilities for a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        List of capability strings
    """
    if agent_name not in AGENT_REGISTRY:
        return []

    return AGENT_REGISTRY[agent_name]["capabilities"]


def log_routing_decision(task: str, agent: str, metadata: Dict) -> None:
    """
    Log routing decision to memory system.

    Args:
        task: Task description
        agent: Selected agent
        metadata: Routing metadata
    """
    log_dir = os.path.join(os.path.dirname(__file__), "..", "memory", "decisions")
    os.makedirs(log_dir, exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task,
        "routed_to": agent,
        "metadata": metadata
    }

    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}_routing.jsonl")

    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


if __name__ == "__main__":
    # Test routing
    test_tasks = [
        "Research Next.js 16 features",
        "Debug the git merge conflict",
        "Design a landing page for our product",
        "Research competitors and build a comparison app",
        "Execute browser automation to fill out form"
    ]

    print("🎯 Agent Router Test\n")
    for task in test_tasks:
        agent, metadata = route_task(task)
        print(f"Task: {task}")
        print(f"→ Routed to: {agent.upper()}")
        print(f"  Reason: {metadata['routing_reason']}")
        if 'analysis' in metadata:
            print(f"  Scores: {metadata['analysis']['agent_scores']}")
        print()
