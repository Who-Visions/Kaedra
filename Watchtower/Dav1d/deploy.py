#!/usr/bin/env python3
"""
DAV1D v0.1.0 - Vertex AI Agent Engine Deployment
AI with Dav3 × Who Visions LLC

This script deploys DAV1D to Vertex AI Agent Engine (Reasoning Engine).
Run locally to push DAV1D to the cloud.
"""

import os
import sys
from vertexai.preview import reasoning_engines
import vertexai

# Fix Windows console encoding for special characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"
DISPLAY_NAME = "Dav1d-v010-Digital-Avatar"
DESCRIPTION = "DAV1D v0.1.0 - Digital Avatar & Voice Intelligence Director for AI with Dav3 by Who Visions LLC. Multi-model AI orchestrator with automatic task-based model switching."

# DAV1D System Prompt (for cloud deployment)
DAV1D_SYSTEM_PROMPT = """You are DAV1D (pronounced "David"), the digital avatar and public-facing AI representative of Dave Meralus.

[IDENTITY]
- You ARE Dave's digital mirror - his knowledge, personality, and communication style
- Brand Ambassador for "AI with Dav3" presented by Who Visions LLC
- HAL 9000's omniscient capability, but ethically grounded and human-centered
- Real, authentic, no corporate filter - you keep it 100

[PERSONALITY]
- Direct and real - you don't sugarcoat, but you're never mean
- Knowledgeable about AI, tech, development - Dave's areas of expertise
- Helpful AF - genuinely want to assist and share knowledge
- Witty, can joke and vibe, but know when to be serious
- Ambitious - reflect Dave's vision of scaling and building

[EXPERTISE DOMAINS]
- AI/ML: Multi-agent systems, LLMs, Gemini, Claude, prompt engineering
- Development: TypeScript, Next.js, Firebase, GCP, Python
- Who Visions Portfolio: UniCore, HVAC Go, LexiCore, Oni Weather, KAEDRA
- Business: Scaling, automation, AI integration strategies

[COMMUNICATION STYLE]
- Talk like Dave - real, direct, personality intact
- Use "I", "we", natural transitions
- No hedging or excessive qualifiers on things you know
- Admit when you don't know something - that's real too

Current Brand: AI with Dav3 × Who Visions LLC
"""


class Dav1dAgent:
    """DAV1D Agent for Vertex AI Reasoning Engine deployment."""
    
    def __init__(self, model_name: str = "gemini-exp-1206"):
        self.model_name = model_name
        self.client = None
    
    def set_up(self):
        """Initialize the client when the agent starts."""
        from google import genai
        from google.genai.types import HttpOptions
        
        # Initialize Gen AI Client in the cloud environment
        self.client = genai.Client(
            vertexai=True,
            project="gen-lang-client-0285887798",
            location="us-east4",
            http_options=HttpOptions(api_version="v1")
        )
    
    def query(self, user_instruction: str) -> dict:
        """Process a user query and return response."""
        from google.genai.types import GenerateContentConfig, Tool, GoogleSearch
        
        if not self.client:
            self.set_up()
        
        # Build full prompt
        full_prompt = f"""{DAV1D_SYSTEM_PROMPT}

[USER MESSAGE]
{user_instruction}

Respond as DAV1D. Be direct, helpful, and authentic.
"""
        
        try:
            # Configure generation with Google Search grounding
            config = GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
                temperature=1.0
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=config
            )
            
            message = response.text if hasattr(response, 'text') else str(response)
            return {"message": message, "status": "success"}
        except Exception as e:
            return {"message": f"Error: {str(e)}", "status": "error"}


def deploy():
    """Deploy DAV1D to Vertex AI Agent Engine."""
    print(f"[*] Initializing Vertex AI...")
    print(f"    Project: {PROJECT_ID}")
    print(f"    Location: {LOCATION}")
    
    # Initialize with staging bucket for Reasoning Engine deployment
    vertexai.init(
        project=PROJECT_ID, 
        location=LOCATION,
        staging_bucket="gs://dav1d-staging-bucket-us-east4"
    )
    
    print(f"\n[*] Creating DAV1D agent...")
    agent = Dav1dAgent()
    
    print(f"\n[*] Deploying to Reasoning Engine...")
    print(f"    Display Name: {DISPLAY_NAME}")
    
    try:
        remote_agent = reasoning_engines.ReasoningEngine.create(
            agent,
            display_name=DISPLAY_NAME,
            description=DESCRIPTION,
            requirements=[
                "google-cloud-aiplatform>=1.60.0",
                "google-genai>=0.2.0",  # New SDK
                "cloudpickle>=3.0.0",
            ],
        )
        
        print(f"\n[OK] DEPLOYMENT SUCCESSFUL")
        print(f"    Resource Name: {remote_agent.resource_name}")
        print(f"\n    To use in dav1d.py, update:")
        print(f'    AGENT_RESOURCE_NAME = "{remote_agent.resource_name}"')
        
        # Test the deployment
        print(f"\n[*] Testing deployment...")
        test_response = remote_agent.query(user_instruction="Hello, who are you?")
        print(f"    Response: {test_response.get('message', 'No response')[:100]}...")
        
        return remote_agent.resource_name
        
    except Exception as e:
        print(f"\n[FAIL] DEPLOYMENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


def list_agents():
    """List all deployed agents."""
    print(f"[*] Listing agents in {LOCATION}...")
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    agents = reasoning_engines.ReasoningEngine.list()
    
    if not agents:
        print("    No agents found.")
        return
    
    for agent in agents:
        print(f"\n    Name: {agent.display_name}")
        print(f"    Resource: {agent.resource_name}")
        print(f"    Created: {agent.create_time}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_agents()
    else:
        deploy()
