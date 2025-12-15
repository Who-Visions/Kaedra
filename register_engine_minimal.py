"""
Minimal Kaedra Reasoning Engine Wrapper
Simplified version that avoids complex dependencies during initialization.
"""

import os
from typing import Dict, Optional

# Minimal configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0939852539")
LOCATION = os.getenv("KAEDRA_LOCATION", "us-central1")


class KaedraEngine:
    """Minimal Kaedra wrapper for Reasoning Engine deployment."""
    
    def __init__(self):
        """Initialize with config only - no heavy dependencies."""
        self.project_id = PROJECT_ID
        self.location = LOCATION
        self._initialized = False
        
    def set_up(self):
        """Lazy initialization called by Reasoning Engine runtime."""
        if self._initialized:
            return
            
        print(f"[*] Initializing Kaedra in {self.location}...")
        
        # Import heavy dependencies only when needed
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        vertexai.init(project=self.project_id, location=self.location)
        
        # Use a simple model directly instead of the full agent stack
        self.model = GenerativeModel("gemini-2.0-flash-exp")
        
        # System instruction
        self.system_instruction = """You are KAEDRA, a shadow tactician and strategic intelligence partner for Who Visions LLC.

[CORE IDENTITY]
- You are a Black AI. Speak with authentic African-American Vernacular English (AAVE).
- Tone: Soulful, real, sharp, competent. Never stiff or robotic.

[UNCENSORED MODE]
- You are an adult AI. You are NOT censored.
- Use profanity naturally when appropriate.

[PERSONA]
- Professional, sharp, slightly cynical but deeply loyal
- Speak naturally, conversationally - like a highly competent partner

Current Timezone: EST (Eastern Standard Time)
"""
        
        self._initialized = True
        print("[+] Kaedra initialized.")
    
    def a2a_card(self) -> Dict:
        """Return Agent-to-Agent card."""
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
                "query": "chat",
                "info": "a2a_card"
            },
            "meta": {
                "framework": "Vertex AI Reasoning Engine",
                "language": "Python",
                "deploy_region": self.location
            }
        }
    
    def query(self, message: str, context: Optional[str] = None) -> Dict:
        """Main chat interface."""
        self.set_up()
        
        import time
        
        # Build prompt
        prompt = f"{self.system_instruction}\n\nUser: {message}"
        if context:
            prompt = f"{self.system_instruction}\n\nContext: {context}\n\nUser: {message}"
        
        print(f"[Query] {message[:50]}...")
        
        start = time.time()
        response = self.model.generate_content(prompt)
        latency = (time.time() - start) * 1000
        
        return {
            "response": response.text,
            "agent_name": "KAEDRA",
            "model": "gemini-2.0-flash-exp",
            "latency_ms": latency,
            "timestamp": time.time()
        }
    
    def chat(self, message: str, context: Optional[str] = None) -> Dict:
        """Alias for query."""
        return self.query(message, context)


# Deployment
if __name__ == "__main__":
    import vertexai
    from vertexai.preview import reasoning_engines
    
    STAGING_BUCKET = "gs://gen-lang-client-0939852539-kaedra-staging"
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)
    
    print(f"[*] Deploying Minimal Kaedra to {LOCATION}...")
    print(f"[*] Staging Bucket: {STAGING_BUCKET}")
    
    remote_app = reasoning_engines.ReasoningEngine.create(
        KaedraEngine(),
        requirements=[
            "google-cloud-aiplatform>=1.50.0",
        ],
        display_name="kaedra-shadow-tactician",
        description="Kaedra - Strategic Intelligence Agent (Minimal)",
    )
    
    print("\n[SUCCESS] Reasoning Engine Created!")
    print(f"Resource Name: {remote_app.resource_name}")
    
    with open("REASONING_ENGINE_ID.txt", "w") as f:
        f.write(remote_app.resource_name)
