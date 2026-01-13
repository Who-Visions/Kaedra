from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class RiskProfile:
    score: int
    requires_approval: bool
    factors: List[str] = field(default_factory=list)

class PolicyEngine:
    """
    Evaluates events against safety policies to determine risk score.
    Implements L1 Exception-Based Autonomy logic.
    """
    
    # Risk Weights
    WEIGHT_WRITE_PROD = 50
    WEIGHT_PUBLIC_POST = 30
    WEIGHT_HIGH_COST = 20
    WEIGHT_LOW_CONFIDENCE = 20
    
    # Thresholds
    APPROVAL_THRESHOLD = 60

    def evaluate(self, event_type: str, payload: Dict[str, Any]) -> RiskProfile:
        score = 0
        factors = []
        
        # 1. Action Type Risk
        if event_type == "notion.write":
            # Check DB ID (Simulated check for Prod DB)
            db_id = payload.get("database_id", "")
            if "prod" in db_id or "2e7ca671" in db_id: # Example IDs
                score += self.WEIGHT_WRITE_PROD
                factors.append("Write to Production DB")
            else:
                score += 10 # Low risk for internal DB
                factors.append("Write to Internal DB")
                
        elif event_type == "slack.post":
            channel = payload.get("channel", "")
            if channel.startswith("C_PUBLIC"): # Hypothetical public channel prefix
                score += self.WEIGHT_PUBLIC_POST
                factors.append("Public Slack Post")
            else:
                score += 5
                factors.append("Internal Slack Post")

        elif event_type == "vertex.generate":
            cost_est = payload.get("estimated_cost", 0.0)
            if cost_est > 1.0:
                score += self.WEIGHT_HIGH_COST
                factors.append(f"High Estimated Cost (${cost_est})")
        
        # 2. Confidence Check
        confidence = payload.get("confidence", 1.0)
        if confidence < 0.8:
            score += self.WEIGHT_LOW_CONFIDENCE
            factors.append(f"Low Model Confidence ({confidence})")

        # 3. Blast Radius (Batch Size)
        items = payload.get("item_count", 0)
        if items > 10:
            score += 30
            factors.append(f"High Blast Radius ({items} items)")

        # 4. Recursive Loop Detection (Ralph Mechanics)
        loop_count = payload.get("loop_count", 0)
        if loop_count > 3:
            score += 40
            factors.append(f"Recursive Loop Warning (Count: {loop_count})")
        elif loop_count > 0:
            score += (loop_count * 10)
            factors.append(f"Incremental Loop Risk (Count: {loop_count})")

        # 5. Budget Proximity
        remaining_budget = payload.get("remaining_budget_percent", 100)
        if remaining_budget < 10:
            score += 25
            factors.append("Critically Low Hourly Budget")
        elif remaining_budget < 25:
            score += 10
            factors.append("Low Hourly Budget")

        # 6. Exit Signal (Explicit Block)
        if payload.get("exit_signal", False):
            score = 100
            factors.append("Force Kill: Exit Signal Detected")

        # Determine if approval needed
        requires_approval = score >= self.APPROVAL_THRESHOLD
        
        return RiskProfile(
            score=score,
            requires_approval=requires_approval,
            factors=factors
        )
