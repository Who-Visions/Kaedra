"""
Status Monitor - Agent Health & Performance Tracking for Kaedra Orchestrator

Monitors agent availability, performance metrics, and system health.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agent_router import AGENT_REGISTRY


class AgentStatus:
    """Represents current status of an agent."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.status = "unknown"  # online, offline, busy, error
        self.last_active = None
        self.current_task = None
        self.performance = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "success_rate": 0.0,
            "avg_response_time": 0.0,
            "total_api_calls": 0
        }

    def update_status(self, status: str, task: Optional[str] = None):
        """Update agent status."""
        self.status = status
        self.last_active = datetime.now().isoformat()
        if task:
            self.current_task = task

    def record_task_completion(self, success: bool, response_time: float):
        """Record task completion metrics."""
        if success:
            self.performance["tasks_completed"] += 1
        else:
            self.performance["tasks_failed"] += 1

        total_tasks = (self.performance["tasks_completed"] +
                      self.performance["tasks_failed"])

        self.performance["success_rate"] = (
            self.performance["tasks_completed"] / total_tasks
            if total_tasks > 0 else 0.0
        )

        # Update average response time
        prev_avg = self.performance["avg_response_time"]
        completed = self.performance["tasks_completed"]

        if completed > 1:
            self.performance["avg_response_time"] = (
                (prev_avg * (completed - 1) + response_time) / completed
            )
        else:
            self.performance["avg_response_time"] = response_time

        self.performance["total_api_calls"] += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "last_active": self.last_active,
            "current_task": self.current_task,
            "performance": self.performance
        }

    def save(self, directory: str = None) -> str:
        """Save status to file."""
        if directory is None:
            directory = os.path.join(
                os.path.dirname(__file__),
                "..",
                "memory",
                "agents"
            )

        os.makedirs(directory, exist_ok=True)

        filepath = os.path.join(directory, f"{self.agent_name}_status.json")

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return filepath

    @staticmethod
    def load(agent_name: str, directory: str = None) -> 'AgentStatus':
        """Load status from file."""
        if directory is None:
            directory = os.path.join(
                os.path.dirname(__file__),
                "..",
                "memory",
                "agents"
            )

        filepath = os.path.join(directory, f"{agent_name}_status.json")

        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)

            status = AgentStatus(agent_name)
            status.status = data.get("status", "unknown")
            status.last_active = data.get("last_active")
            status.current_task = data.get("current_task")
            status.performance = data.get("performance", status.performance)

            return status
        else:
            return AgentStatus(agent_name)


def ping_all_agents() -> Dict[str, Dict]:
    """
    Check status of all registered agents.

    Returns:
        Dict mapping agent_name to status dict
    """
    status_report = {}

    for agent_name in AGENT_REGISTRY.keys():
        agent_status = AgentStatus.load(agent_name)

        # Check if agent is stale (no activity in 1 hour)
        is_stale = False
        if agent_status.last_active:
            last_active_dt = datetime.fromisoformat(agent_status.last_active)
            if datetime.now() - last_active_dt > timedelta(hours=1):
                is_stale = True

        status_report[agent_name] = {
            "status": "stale" if is_stale else agent_status.status,
            "last_active": agent_status.last_active,
            "current_task": agent_status.current_task,
            "performance": agent_status.performance
        }

    return status_report


def check_system_health() -> Dict:
    """
    Generate overall system health report.

    Returns:
        Health report dict with status, agent_count, issues
    """
    agent_statuses = ping_all_agents()

    online_count = sum(1 for s in agent_statuses.values()
                      if s["status"] in ["online", "idle", "busy"])
    total_count = len(agent_statuses)

    issues = []

    # Check for offline/error agents
    for agent, status in agent_statuses.items():
        if status["status"] in ["offline", "error"]:
            issues.append(f"{agent.upper()} is {status['status']}")

        # Check success rate
        success_rate = status["performance"]["success_rate"]
        if success_rate < 0.8 and status["performance"]["tasks_completed"] > 5:
            issues.append(f"{agent.upper()} has low success rate: {success_rate:.1%}")

    # Overall health status
    if online_count == total_count:
        health_status = "healthy"
    elif online_count >= total_count * 0.7:
        health_status = "degraded"
    else:
        health_status = "critical"

    return {
        "status": health_status,
        "timestamp": datetime.now().isoformat(),
        "agents_online": online_count,
        "agents_total": total_count,
        "availability": f"{(online_count/total_count)*100:.1f}%",
        "issues": issues,
        "agent_details": agent_statuses
    }


def log_performance_metrics(agent_name: str, metrics: Dict) -> None:
    """
    Log performance metrics for an agent.

    Args:
        agent_name: Name of the agent
        metrics: Dict with performance data
    """
    agent_status = AgentStatus.load(agent_name)

    # Update from metrics
    if "success" in metrics:
        agent_status.record_task_completion(
            success=metrics["success"],
            response_time=metrics.get("response_time", 0.0)
        )

    if "status" in metrics:
        agent_status.update_status(
            status=metrics["status"],
            task=metrics.get("task")
        )

    agent_status.save()


def generate_performance_report(agent_name: Optional[str] = None) -> str:
    """
    Generate formatted performance report.

    Args:
        agent_name: Specific agent (or None for all agents)

    Returns:
        Formatted report string
    """
    output = []
    output.append("=" * 70)
    output.append("KAEDRA ORCHESTRATOR - AGENT PERFORMANCE REPORT")
    output.append("=" * 70)
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if agent_name:
        agents_to_report = [agent_name]
    else:
        agents_to_report = list(AGENT_REGISTRY.keys())

    for agent in agents_to_report:
        status = AgentStatus.load(agent)
        agent_info = AGENT_REGISTRY.get(agent, {})

        output.append(f"\n{'─' * 70}")
        output.append(f"AGENT: {agent.upper()}")
        output.append(f"Role: {agent_info.get('role', 'Unknown')}")
        output.append(f"{'─' * 70}")

        output.append(f"  Status: {status.status.upper()}")
        output.append(f"  Last Active: {status.last_active or 'Never'}")
        output.append(f"  Current Task: {status.current_task or 'None'}")

        output.append(f"\n  Performance Metrics:")
        perf = status.performance
        output.append(f"    Tasks Completed: {perf['tasks_completed']}")
        output.append(f"    Tasks Failed: {perf['tasks_failed']}")
        output.append(f"    Success Rate: {perf['success_rate']:.1%}")
        output.append(f"    Avg Response Time: {perf['avg_response_time']:.2f}s")
        output.append(f"    Total API Calls: {perf['total_api_calls']}")

    output.append(f"\n{'=' * 70}")

    return '\n'.join(output)


def visualize_system_health(health_report: Dict) -> str:
    """
    Create visual representation of system health.

    Args:
        health_report: Output from check_system_health()

    Returns:
        Formatted visualization
    """
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️",
        "critical": "🔴"
    }

    output = []
    output.append("=" * 70)
    output.append("KAEDRA ORCHESTRATOR - SYSTEM HEALTH")
    output.append("=" * 70)
    output.append(f"Status: {status_emoji.get(health_report['status'], '❓')} {health_report['status'].upper()}")
    output.append(f"Timestamp: {health_report['timestamp']}")
    output.append(f"Availability: {health_report['availability']} ({health_report['agents_online']}/{health_report['agents_total']} agents)")
    output.append("")

    if health_report['issues']:
        output.append("⚠️  ISSUES:")
        for issue in health_report['issues']:
            output.append(f"  - {issue}")
        output.append("")

    output.append("AGENT STATUS:")
    for agent, details in health_report['agent_details'].items():
        status_icon = "🟢" if details['status'] in ["online", "idle"] else "🔴"
        output.append(f"  {status_icon} {agent.upper()}: {details['status']}")

    output.append("=" * 70)

    return '\n'.join(output)


if __name__ == "__main__":
    # Test status monitoring
    print("🔍 Status Monitor Test\n")

    # Simulate some agent activity
    for agent in ["claude", "gemini", "vision"]:
        status = AgentStatus(agent)
        status.update_status("online", task="Test task")
        status.record_task_completion(success=True, response_time=1.5)
        status.save()

    print("📊 Performance Report:\n")
    print(generate_performance_report())

    print("\n🏥 System Health:\n")
    health = check_system_health()
    print(visualize_system_health(health))
