
import os
import vertexai
from vertexai.preview import reasoning_engines

# Hardcode config to match existing setup
PROJECT_ID = "gen-lang-client-0939852539"
LOCATION = "us-central1" # Back to Primary Region
# Create a NEW bucket to force fresh permissions
import uuid
run_id = str(uuid.uuid4())[:8]
STAGING_BUCKET = f"gs://{PROJECT_ID}-kaedra-staging-{run_id}"

class MinimalAgent:
    def __init__(self):
        print("MinimalAgent Initialized")

    def query(self, prompt: str):
        return {"response": f"Echo: {prompt}"}

def deploy():
    print(f"[*] Deploying MinimalAgent to {LOCATION}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

    remote_app = reasoning_engines.ReasoningEngine.create(
        MinimalAgent,
        requirements=[],
        extra_packages=[],
        display_name="minimal-agent-attempt-26",
        description="Isolation Test Agent (Py3.12 - Absolute Minimal)",
        sys_version="3.12",
    )
    
    print(f"[SUCCESS] Deployed: {remote_app.resource_name}")
    return remote_app

if __name__ == "__main__":
    try:
        deploy()
    except Exception as e:
        print(f"[ERROR] Deployment Failed: {e}")
        # Print full traceback if possible
        import traceback
        traceback.print_exc()
