
import os
import time
from typing import Optional, Dict, List
from kaedra.core.config import PROJECT_ID, LOCATION
import vertexai
from vertexai.preview import reasoning_engines

# Set up the environment (Local)
STAGING_BUCKET = "gs://gen-lang-client-0939852539-kaedra-staging"
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

class KaedraEngine:
    """
    Kaedra Shadow Tactician - Reasoning Engine Wrapper
    
    This class wraps the Kaedra Agent for deployment to Vertex AI Reasoning Engine.
    It exposes the standard agent interface + A2A capabilities.
    """
    
    def __init__(self, project_id: str = PROJECT_ID, location: str = LOCATION):
        """
        Initialize the engine configuration ONLY.
        NO heavy objects (clients, models) here to ensure pickling works.
        """
        self.project_id = project_id
        self.location = location
        self.agent = None
        
    def set_up(self):
        """
        Initialize the heavy services.
        This runs ON THE CLOUD instance (and lazily locally if needed).
        """
        print(f"[*] Setting up Kaedra Engine for {self.project_id} in {self.location}...")
        
        # Imports here to avoid top-level dependency issues during unpickling if environment varies
        import vertexai
        from kaedra.services.prompt import PromptService
        from kaedra.services.memory import MemoryService
        from kaedra.agents.kaedra import KaedraAgent
        
        # Re-init Vertex AI in the remote environment
        vertexai.init(project=self.project_id, location=self.location)
        
        self.prompt_service = PromptService(project=self.project_id, location=self.location)
        self.memory_service = MemoryService() 
        self.agent = KaedraAgent(self.prompt_service, self.memory_service)
        print("[+] Kaedra Agent initialized successfully.")

    def a2a_card(self) -> Dict:
        """Return the Agent-to-Agent (A2A) Card."""
        return {
            "name": "Kaedra",
            "version": "0.0.6",
            "id": "kaedra-shadow-tactician",
            "description": "Strategic intelligence partner and shadow tactician for Who Visions LLC.",
            "role": "Orchestrator",
            "capabilities": [
                "strategic_planning",
                "intelligence_synthesis",
                "shadow_operations",
                "multi_agent_coordination"
            ],
            "endpoints": {
                "chat": "invoke",
                "info": "a2a_card"
            },
            "meta": {
                "framework": "Vertex AI Reasoning Engine",
                "language": "Python",
                "deploy_region": self.location
            }
        }

    def chat(self, message: str, context: Optional[str] = None) -> Dict:
        """
        Chat with Kaedra (v1/chat equivalent).
        """
        # Ensure setup (for local testing mainly, RE calls set_up automaticall usually but good to be safe)
        if hasattr(self, 'agent') and self.agent is None:
            self.set_up()
            
        # Synchronous execution for the engine wrapper
        import asyncio
        import time
        
        print(f"[Query] {message[:50]}...")
        if context:
            print(f"[Context] {context[:50]}...")
            
        result = asyncio.run(self.agent.run(message, context))
        
        return {
            "response": result.content,
            "agent_name": result.agent_name,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "timestamp": time.time()
        }

    def query(self, message: str) -> Dict:
        """Legacy/Simple query alias."""
        return self.chat(message)

# --------------------------------------------------------------------------
# DEPLOYMENT SCRIPT
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[*] Deploying Kaedra Reasoning Engine to {LOCATION}...")
    print(f"[*] Staging Bucket: {STAGING_BUCKET}")
    
    # 1. Define the remote app
    # We pass the class instance. It will be pickled.
    # self.agent is None at this point, so it pickles fine.
    remote_app = reasoning_engines.ReasoningEngine.create(
        KaedraEngine(project_id=PROJECT_ID, location=LOCATION),
        requirements=[
            "google-cloud-aiplatform>=1.50.0",
            "google-generativeai>=0.5.0",
            "python-dotenv>=1.0.0",
            "pytz>=2024.1",
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.0",
        ],
        extra_packages=[
            "./kaedra",  # Bundle the local package
        ],
        display_name="kaedra-shadow-tactician",
        description="Kaedra - Strategic Intelligence Agent",
    )
    
    print("\n[SUCCESS] Reasoning Engine Created!")
    print(f"Resource Name: {remote_app.resource_name}")
    print(f"Operation: {remote_app}")
    
    # Save the resource name to a file for easy access
    with open("REASONING_ENGINE_ID.txt", "w") as f:
        f.write(remote_app.resource_name)
