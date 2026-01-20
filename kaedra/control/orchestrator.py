import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field

# Google Cloud Imports
try:
    from google.cloud import firestore
except ImportError:
    firestore = None

from kaedra.control.policy import PolicyEngine, RiskProfile
from kaedra.services.slack_bot import SlackService

logger = logging.getLogger("kaedra.orchestrator")

from kaedra.control.orchestrator_runtime import OrchestratorRuntime


@dataclass
class RunState:
    """State for an autonomous run"""
    run_id: str
    task: str
    mode: str
    status: str = "pending"
    completion_indicators: int = 0
    exit_signal: bool = False
    loop_count: int = 0
    outputs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class RunManager:
    """
    Manages long-running autonomous tasks.
    Implements Ralph-style exit detection with dual conditions.
    """
    
    # Circuit breaker thresholds
    NO_PROGRESS_THRESHOLD = 3
    SAME_ERROR_THRESHOLD = 5
    MAX_LOOPS = 50
    
    def __init__(self, slack: Optional[SlackService] = None, agent=None):
        self.slack = slack
        self.agent = agent
        self.runs: Dict[str, RunState] = {}
        logger.info("✅ RunManager initialized")
    
    async def create_run(self, task: str, mode: str = "kaedra") -> str:
        """Create a run, post to Slack, return run_id"""
        run_id = uuid4().hex[:8]
        run = RunState(run_id=run_id, task=task, mode=mode, status="started")
        self.runs[run_id] = run
        
        if self.slack:
            await self.slack.post_message(f"🚀 Run `{run_id}` started: {task}")
        
        logger.info(f"Run {run_id} created: {task}")
        return run_id
    
    async def execute_loop(self, run_id: str):
        """Ralph-style autonomy loop with exit detection"""
        run = self.runs.get(run_id)
        if not run:
            logger.error(f"Run {run_id} not found")
            return
        
        run.status = "running"
        errors_in_a_row = 0
        no_progress_count = 0
        
        while not self._should_exit(run) and run.loop_count < self.MAX_LOOPS:
            run.loop_count += 1
            logger.info(f"Run {run_id} loop {run.loop_count}")
            
            try:
                if self.agent:
                    result = await self.agent.run(run.task, mode=run.mode)
                    run.outputs.append(str(result)[:200])
                    
                    # Check for completion indicators in output
                    if self._detect_completion(result):
                        run.completion_indicators += 1
                    
                    # Check for explicit exit signal
                    if self._detect_exit_signal(result):
                        run.exit_signal = True
                    
                    errors_in_a_row = 0
                    no_progress_count = 0
                else:
                    # Dummy loop for testing
                    await asyncio.sleep(1)
                    run.completion_indicators += 1
                    if run.loop_count >= 3:
                        run.exit_signal = True
                    
            except Exception as e:
                errors_in_a_row += 1
                logger.error(f"Run {run_id} loop {run.loop_count} error: {e}")
                
                # Circuit breaker
                if errors_in_a_row >= self.SAME_ERROR_THRESHOLD:
                    run.status = "failed"
                    if self.slack:
                        await self.slack.post_message(f"🔴 Run `{run_id}` failed: circuit breaker opened")
                    return
            
            run.updated_at = datetime.utcnow()
            
            # Update Slack periodically
            if self.slack and run.loop_count % 5 == 0:
                await self.slack.post_message(f"⏳ Run `{run_id}` progress: loop {run.loop_count}")
        
        # Complete
        run.status = "completed"
        if self.slack:
            await self.slack.post_message(
                f"✅ Run `{run_id}` completed after {run.loop_count} loops"
            )
        logger.info(f"Run {run_id} completed: {run.loop_count} loops")
    
    def _should_exit(self, run: RunState) -> bool:
        """Dual condition exit: completion_indicators >= 2 AND exit_signal"""
        return run.completion_indicators >= 2 and run.exit_signal
    
    def _detect_completion(self, result: Any) -> bool:
        """Detect completion indicators from agent output"""
        if not result:
            return False
        text = str(result).lower()
        indicators = ["complete", "done", "finished", "all tasks", "mission accomplished"]
        return any(ind in text for ind in indicators)
    
    def _detect_exit_signal(self, result: Any) -> bool:
        """Detect explicit exit signal from agent"""
        if isinstance(result, dict):
            return result.get("exit_signal", False)
        return False
    
    def list_runs(self) -> List[Dict[str, Any]]:
        """List all runs with their status"""
        return [
            {
                "run_id": r.run_id,
                "task": r.task[:50],
                "status": r.status,
                "loops": r.loop_count,
                "created_at": r.created_at.isoformat(),
            }
            for r in self.runs.values()
        ]
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific run"""
        run = self.runs.get(run_id)
        if not run:
            return None
        return {
            "run_id": run.run_id,
            "task": run.task,
            "mode": run.mode,
            "status": run.status,
            "loops": run.loop_count,
            "completion_indicators": run.completion_indicators,
            "exit_signal": run.exit_signal,
            "outputs": run.outputs[-5:],  # Last 5 outputs
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
        }


class Orchestrator:
    """
    Control Plane Orchestrator Facade.
    Delegates to Runtime. Includes RunManager for autonomous tasks.
    """
    
    def __init__(self, slack_service: Optional[SlackService] = None, agent=None):
        # Initialize Runtime
        self.runtime = OrchestratorRuntime(slack=slack_service)
        
        # Initialize RunManager for autonomous loops
        self.run_manager = RunManager(slack=slack_service, agent=agent)
        
        logger.info("✅ Orchestrator Facade + RunManager Initialized.")

    async def ingest_event(self, event_id: str, event_type: str, payload: Dict[str, Any]):
        """
        Delegate event ingestion to runtime.
        """
        await self.runtime.ingest_event(event_id, event_type, payload)

    async def _handle_blocked(self, correlation_id: str, risk: RiskProfile):
        pass

    async def _execute_task(self, correlation_id: str, event_type: str, payload: Dict[str, Any]):
        pass

    async def _persist_state(self, correlation_id: str, data: Dict[str, Any]):
        pass

    # --- Control Plane Interface (Slack/API) ---

    async def ingest_job(self, input_data: str, user_id: str):
        """Ingest a job from Slack/CLI."""
        # Simple wrap as an event
        await self.runtime.ingest_event(
            event_id=f"manual-{int(datetime.utcnow().timestamp())}",
            event_type="manual.ingest",
            payload={"source": "slack", "input": input_data, "user": user_id}
        )

    async def approve_task(self, task_id: str) -> str:
        return await self.runtime.approve_request(task_id)

    async def deny_task(self, task_id: str) -> str:
        return await self.runtime.deny_request(task_id)

    def pause_system(self):
        self.runtime.set_kill_switch(True)

    def resume_system(self):
        self.runtime.set_kill_switch(False)

    async def kill_task(self, task_id: str) -> str:
        return await self.runtime.kill_task(task_id)

    def get_status(self, task_id: str) -> str:
        return self.runtime.get_status(task_id)
