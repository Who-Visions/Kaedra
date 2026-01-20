import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kaedra.services.slack_bot import SlackService

async def verify_slack_service():
    print("🔍 Verifying Slack Service Integration...")
    
    # Initialize service
    service = SlackService()
    
    print(f"   App Token Present: {bool(service.app_token)}")
    print(f"   Signing Secret Present: {bool(service.signing_secret)}")
    print(f"   Bot Token Present: {bool(service.bot_token)}")
    
    # Initialize (should fail gracefully if no bot token)
    service.initialize()
    
    if service.app:
        print("✅ Slack Service Initialized (App Created)")
    else:
        print("⚠️ Slack Service Not Initialized (Expected if no xoxb token)")
        
    print("\n✅ Verification Script Complete")

if __name__ == "__main__":
    asyncio.run(verify_slack_service())
