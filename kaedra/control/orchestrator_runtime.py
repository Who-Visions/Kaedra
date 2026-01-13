import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from kaedra.control.policy import PolicyEngine, RiskProfile
from kaedra.services.notion_service import NotionService

logger = logging.getLogger("kaedra.orchestrator.runtime")

class OrchestratorRuntime:
    """
    Control Plane Runtime for Autonomy.
    Implements Loopless State Machine, Budget Checks, and Circuit Breakers.
    """
    
    def __init__(self, notion: Optional[NotionService] = None, slack = None):
        self.notion = notion or NotionService()
        self.slack = slack
        self.policy = PolicyEngine()
        
        # In-Memory State (For MVP - Production should use Firestore)
        self.active_tasks = {} 
        self.budgets = {
            "hourly_calls": 0,
            "hourly_limit": 50,
            "last_reset": datetime.utcnow().hour
        }

    async def ingest_event(self, event_id: str, event_type: str, payload: Dict[str, Any]):
        """
        Main Event Ingestion.
        """
        logger.info(f"⚡ Ingesting Event: {event_id} ({event_type})")
        
        # 1. Budget Check
        if not self._check_budget():
            logger.warning("⛔ Budget Exceeded. Blocking Event.")
            return

        # 2. Risk Analysis
        risk: RiskProfile = self.policy.evaluate(event_type, payload)
        
        # 3. Create Notion Ops Task
        title = f"Autonomy Event: {event_type} [{event_id[:8]}]"
        
        status = "Needs Review" if risk.requires_approval else "Running"
        
        props = {
            "Risk Score": risk.score,
            "Autonomy Status": "Blocked" if risk.requires_approval else "Running",
            "Loop Count": 0,
            "Exit Signal": False
        }
        
        try:
            task_id = self.notion.create_ops_task(title=title, status=status, properties=props)
            logger.info(f"✅ Created Ops Task: {task_id}")
            
            if risk.requires_approval:
                await self._notify_slack_blocked(task_id, risk)
            else:
                 await self._execute_action(task_id, event_type, payload)
                 
        except Exception as e:
            logger.error(f"❌ Failed to process event: {e}")

    def _check_budget(self) -> bool:
        """Simple Hourly Budget Check."""
        now_hour = datetime.utcnow().hour
        if now_hour != self.budgets["last_reset"]:
            self.budgets["hourly_calls"] = 0
            self.budgets["last_reset"] = now_hour
            
        if self.budgets["hourly_calls"] >= self.budgets["hourly_limit"]:
            return False
            
        self.budgets["hourly_calls"] += 1
        return True

    async def _notify_slack_blocked(self, task_id: str, risk: RiskProfile):
        """Send Blocked Alert."""
        if self.slack:
             msg = f"🛑 *Autonomy Blocked*\nTask: `{task_id}`\nRisk: {risk.score}\nFactors: {', '.join(risk.factors)}"
             await self.slack.app.client.chat_postMessage(channel="#kaedra-ops", text=msg)

    async def _execute_action(self, task_id: str, event_type: str, payload: Dict):
        """Execute (Stub)."""
        logger.info(f"🚀 Executing Action for {task_id}...")
        # In real impl, this calls Vertex/Tools
        await asyncio.sleep(1)
        logger.info(f"✅ Action Complete for {task_id}")
