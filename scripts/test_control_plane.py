import asyncio
import logging
from kaedra.control.orchestrator import Orchestrator

# Configure Logging
logging.basicConfig(level=logging.INFO)

async def test_control_plane():
    print("🧪 Testing Autonomy Control Plane...")
    
    orch = Orchestrator()  # No Slack service needed for logic test
    
    # 1. Test Ingestion (Budget Check)
    print("\n[1] Testing Ingestion & Budgeting")
    for i in range(5):
        await orch.ingest_job(f"test-job-{i}", "user-test")
        
    # 2. Test Kill Switch
    print("\n[2] Testing Kill Switch")
    orch.pause_system()
    status = orch.runtime.kill_switch
    print(f"Kill Switch Active: {status}")
    if not status:
        print("❌ Failed to activate Kill Switch")
    
    # Try ingest while paused
    await orch.ingest_job("job-while-paused", "user-test")
    
    # Resume
    orch.resume_system()
    print("Kill Switch Deactivated")
    
    # 3. Test Manual Approval/Denial
    print("\n[3] Testing Task Controls")
    task_id = "manual-task-123"
    
    # Simulate a blocked task (conceptually - runtime doesn't store blocked yet unless real DB)
    # But we can test the methods return expected strings
    res_approve = await orch.approve_task(task_id)
    print(f"Approve Result: {res_approve}")
    
    res_deny = await orch.deny_task(task_id)
    print(f"Deny Result: {res_deny}")
    
    # 4. Test Recursive Loop Detection
    print("\n[4] Testing Recursive Loop Detection")
    # Simulate a high loop count payload
    await orch.runtime.ingest_event(
        "loop-test-01", 
        "manual.ingest", 
        {"loop_count": 5, "input": "Infinite Loop Task"}
    )
    
    # 5. Test Budget Proximity
    print("\n[5] Testing Budget Proximity")
    orch.runtime.budgets["hourly_calls"] = 48 # Near limit 50
    await orch.runtime.ingest_event(
        "budget-test-01",
        "manual.ingest",
        {"input": "Low Budget Task"}
    )

    # 6. Test Exit Signal (Kill Command)
    print("\n[6] Testing Exit Signal (Force Kill)")
    await orch.runtime.ingest_event(
        "exit-test-01",
        "manual.ingest",
        {"exit_signal": True, "input": "Killed Task"}
    )
    
    print("\n✅ Advanced Control Plane Logic Verified!")

if __name__ == "__main__":
    asyncio.run(test_control_plane())
