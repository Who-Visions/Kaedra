"""
Mission Planner - Complex Task Decomposition for Kaedra Orchestrator

Breaks down complex missions into agent-specific subtasks and generates
execution plans (sequential, parallel, or hybrid).
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from agent_router import AGENT_REGISTRY, route_task


class MissionPlan:
    """Represents a planned mission with tasks and agent assignments."""

    def __init__(self, objective: str, mission_id: Optional[str] = None):
        self.mission_id = mission_id or str(uuid.uuid4())[:8]
        self.objective = objective
        self.tasks: List[Dict] = []
        self.execution_mode = "sequential"  # sequential, parallel, hybrid
        self.created_at = datetime.now().isoformat()
        self.status = "planned"

    def add_task(self, description: str, agent: str, dependencies: List[str] = None,
                 priority: int = 1):
        """Add a task to the mission plan."""
        task_id = f"{self.mission_id}_t{len(self.tasks) + 1}"

        task = {
            "task_id": task_id,
            "description": description,
            "agent": agent,
            "dependencies": dependencies or [],
            "priority": priority,
            "status": "pending"
        }

        self.tasks.append(task)
        return task_id

    def set_execution_mode(self, mode: str):
        """Set execution mode: sequential, parallel, or hybrid."""
        if mode not in ["sequential", "parallel", "hybrid"]:
            raise ValueError("Mode must be sequential, parallel, or hybrid")
        self.execution_mode = mode

    def to_dict(self) -> Dict:
        """Convert plan to dictionary."""
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "execution_mode": self.execution_mode,
            "tasks": self.tasks,
            "created_at": self.created_at,
            "status": self.status
        }

    def save(self, directory: str = None) -> str:
        """Save mission plan to file."""
        if directory is None:
            directory = os.path.join(
                os.path.dirname(__file__),
                "..",
                "memory",
                "missions"
            )

        os.makedirs(directory, exist_ok=True)

        filename = f"{datetime.now().strftime('%Y-%m-%d')}_{self.mission_id}.json"
        filepath = os.path.join(directory, filename)

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return filepath


def decompose_mission(mission_description: str) -> List[str]:
    """
    Break down a complex mission into discrete subtasks.

    Args:
        mission_description: High-level mission objective

    Returns:
        List of subtask descriptions
    """
    # Common mission patterns
    patterns = {
        "research_and_build": [
            "Research {topic} and gather requirements",
            "Analyze research findings and create specifications",
            "Build {deliverable} based on specifications",
            "Test and validate {deliverable}",
            "Document and deliver final result"
        ],
        "create_and_deploy": [
            "Design {item} concept and structure",
            "Implement {item} with required features",
            "Test {item} functionality",
            "Deploy {item} to production",
            "Monitor and verify deployment"
        ],
        "analyze_and_report": [
            "Gather data on {subject}",
            "Analyze data and identify patterns",
            "Generate insights and recommendations",
            "Create report with findings",
            "Present results"
        ]
    }

    # Detect pattern based on keywords
    mission_lower = mission_description.lower()

    if any(word in mission_lower for word in ["research", "investigate", "build", "create", "app"]):
        template = patterns["research_and_build"]
        # Extract topic/deliverable from description
        # Simple extraction - can be enhanced with NLP
        return [task.format(topic="specified topic", deliverable="solution")
                for task in template]

    elif any(word in mission_lower for word in ["deploy", "launch", "production"]):
        template = patterns["create_and_deploy"]
        return [task.format(item="application") for task in template]

    elif any(word in mission_lower for word in ["analyze", "report", "study"]):
        template = patterns["analyze_and_report"]
        return [task.format(subject="subject") for task in template]

    else:
        # Generic breakdown
        return [
            f"Analyze requirements for: {mission_description}",
            f"Execute primary work for: {mission_description}",
            f"Review and validate results",
            f"Deliver final output"
        ]


def assign_agents(subtasks: List[str]) -> List[Tuple[str, str]]:
    """
    Assign agents to subtasks based on capabilities.

    Args:
        subtasks: List of subtask descriptions

    Returns:
        List of (subtask, agent_name) tuples
    """
    assignments = []

    for task in subtasks:
        agent, metadata = route_task(task)
        assignments.append((task, agent))

    return assignments


def generate_execution_plan(assignments: List[Tuple[str, str]],
                           mode: str = "auto") -> MissionPlan:
    """
    Generate execution plan from task-agent assignments.

    Args:
        assignments: List of (task, agent) tuples
        mode: Execution mode (auto, sequential, parallel, hybrid)

    Returns:
        MissionPlan object
    """
    # Extract mission objective from first task
    objective = "Complex multi-agent mission"
    if assignments:
        objective = assignments[0][0]

    plan = MissionPlan(objective=objective)

    # Detect dependencies and determine execution mode
    if mode == "auto":
        # Auto-detect based on task types
        agent_counts = {}
        for _, agent in assignments:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        # If tasks can be parallelized (different agents, no dependencies)
        if len(agent_counts) == len(assignments):
            mode = "parallel"
        else:
            mode = "sequential"

    plan.set_execution_mode(mode)

    # Add tasks with dependencies based on mode
    task_ids = []

    for i, (task_desc, agent) in enumerate(assignments):
        if mode == "sequential":
            # Each task depends on previous
            deps = [task_ids[-1]] if task_ids else []
        elif mode == "parallel":
            # No dependencies
            deps = []
        else:  # hybrid
            # Group by agent, sequential within agent, parallel across agents
            same_agent_tasks = [tid for tid, (_, a) in zip(task_ids, assignments[:i])
                              if a == agent]
            deps = [same_agent_tasks[-1]] if same_agent_tasks else []

        task_id = plan.add_task(
            description=task_desc,
            agent=agent,
            dependencies=deps,
            priority=len(assignments) - i  # Earlier tasks have higher priority
        )
        task_ids.append(task_id)

    return plan


def plan_mission(mission_description: str, execution_mode: str = "auto") -> MissionPlan:
    """
    Complete mission planning pipeline.

    Args:
        mission_description: High-level mission description
        execution_mode: How to execute (auto, sequential, parallel, hybrid)

    Returns:
        Complete MissionPlan
    """
    # Step 1: Decompose into subtasks
    subtasks = decompose_mission(mission_description)

    # Step 2: Assign agents
    assignments = assign_agents(subtasks)

    # Step 3: Generate execution plan
    plan = generate_execution_plan(assignments, mode=execution_mode)

    # Save plan
    plan.save()

    return plan


def visualize_plan(plan: MissionPlan) -> str:
    """
    Generate text visualization of mission plan.

    Args:
        plan: MissionPlan object

    Returns:
        Formatted string visualization
    """
    output = []
    output.append(f"{'='*60}")
    output.append(f"MISSION: {plan.objective}")
    output.append(f"ID: {plan.mission_id}")
    output.append(f"Mode: {plan.execution_mode.upper()}")
    output.append(f"{'='*60}\n")

    for i, task in enumerate(plan.tasks, 1):
        agent_info = AGENT_REGISTRY.get(task['agent'], {})
        agent_name = task['agent'].upper()
        agent_role = agent_info.get('role', 'Unknown')

        output.append(f"TASK {i}: {task['task_id']}")
        output.append(f"  Description: {task['description']}")
        output.append(f"  Agent: {agent_name} ({agent_role})")
        output.append(f"  Priority: {task['priority']}")
        output.append(f"  Dependencies: {', '.join(task['dependencies']) if task['dependencies'] else 'None'}")
        output.append(f"  Status: {task['status']}")
        output.append("")

    output.append(f"{'='*60}")

    return '\n'.join(output)


if __name__ == "__main__":
    # Test mission planning
    print("🎯 Mission Planner Test\n")

    test_missions = [
        "Research Next.js 16 features and build a demo application",
        "Analyze competitor websites and create a design comparison report",
        "Deploy the new landing page to production"
    ]

    for mission_desc in test_missions:
        print(f"\n📋 PLANNING: {mission_desc}\n")

        plan = plan_mission(mission_desc)
        print(visualize_plan(plan))
        print(f"✅ Plan saved to: memory/missions/\n")
        print("-" * 60)
