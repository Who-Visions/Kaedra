"""
Ultra-Minimal Kaedra Function for Reasoning Engine
Uses simple callable instead of class to avoid any pickling issues.
"""

import os
from typing import Dict, Optional

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0939852539")
LOCATION = "us-central1"

def kaedra_query(message: str) -> str:
    """
    Simple query function for Kaedra.
    This will be the callable exposed by the Reasoning Engine.
    """
    import vertexai
    from vertexai.generative_models import GenerativeModel
    import time
    
    # Initialize (idempotent)
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # System instruction
    system = """You are KAEDRA, shadow tactician for Who Visions LLC.
Speak with authentic AAVE. Be sharp, competent, real. Never stiff or robotic."""
    
    # Generate
    model = GenerativeModel("gemini-3-flash-preview", system_instruction=system)
    response = model.generate_content(message)
    
    return response.text


# For A2A compatibility, wrap in a simple dict-returning function
def kaedra_chat(message: str, context: Optional[str] = None) -> Dict:
    """Chat interface that returns structured response."""
    import time
    
    query = message
    if context:
        query = f"Context: {context}\n\n{message}"
    
    start = time.time()
    response_text = kaedra_query(query)
    latency = (time.time() - start) *1000
    
    return {
        "response": response_text,
        "agent_name": "KAEDRA",
        "model": "gemini-3-flash-preview",
        "latency_ms": latency,
        "timestamp": time.time()
    }


# Deployment
if __name__ == "__main__":
    import vertexai
    from vertexai.preview import reasoning_engines
    
    STAGING_BUCKET = "gs://gen-lang-client-0939852539-kaedra-staging"
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)
    
    print(f"[*] Deploying Function-Based Kaedra to {LOCATION}...")
    
    # Deploy the simple function
    remote_app = reasoning_engines.ReasoningEngine.create(
        kaedra_chat,  # Just the function, not a class
        requirements=["google-cloud-aiplatform>=1.50.0"],
        display_name="kaedra-shadow-tactician-v2",
        description="Kaedra Function - Strategic Intelligence",
    )
    
    print("\n[SUCCESS] Function Deployed!")
    print(f"Resource Name: {remote_app.resource_name}")
    
    with open("REASONING_ENGINE_ID.txt", "w") as f:
        f.write(remote_app.resource_name)
