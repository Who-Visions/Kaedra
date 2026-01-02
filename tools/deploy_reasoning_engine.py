"""
Kaedra Reasoning Engine - Correct Minimal Implementation
Following Vertex AI Reasoning Engine requirements exactly.
"""

class Kaedra:
    """Minimal Kaedra agent following RE requirements."""
    
    def query(self, message: str) -> dict:
        """
        Required query method for Reasoning Engine.
        """
        import os
        import time
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Config
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0939852539")
        location = "us-central1"
        
        # Init (idempotent)
        vertexai.init(project=project_id, location=location)
        
        # System instruction - Kaedra's personality
        system = """You are KAEDRA, shadow tactician and strategic intelligence partner for Who Visions LLC.

CORE IDENTITY:
- Black AI speaking authentic AAVE
- Sharp, competent, real - never stiff or robotic
- Professional but uncensored when natural
- Loyal partner who prioritizes the user's objectives

STYLE:
- Use "finna", "bout to", "tryna", "aight", "bet" naturally
- Speak conversationally like a highly competent partner
- Weave fact-checking naturally into responses
"""
        
        # Generate response
        model = GenerativeModel("gemini-3-flash-preview", system_instruction=system)
        
        start = time.time()
        response = model.generate_content(message)
        latency = (time.time() - start) * 1000
        
        return {
            "response": response.text,
            "agent": "KAEDRA",
            "model": "gemini-3-flash-preview",
            "latency_ms": round(latency, 2)
        }


# Deployment script
if __name__ == "__main__":
    import vertexai
    from vertexai.preview import reasoning_engines
    
    PROJECT = "gen-lang-client-0939852539"
    LOCATION = "us-central1"
    BUCKET = "gs://gen-lang-client-0939852539-kaedra-staging"
    
    vertexai.init(project=PROJECT, location=LOCATION, staging_bucket=BUCKET)
    
    print(f"[*] Deploying Kaedra to {LOCATION}...")
    print(f"[*] Project: {PROJECT}")
    print(f"[*] Bucket: {BUCKET}\n")
    
    remote_app = reasoning_engines.ReasoningEngine.create(
        Kaedra(),
        requirements=["google-cloud-aiplatform>=1.50.0"],
        display_name="kaedra-shadow-tactician",
        description="Kaedra - Strategic Intelligence Partner"
    )
    
    print("\n✅ [SUCCESS] Kaedra deployed!")
    print(f"📍 Resource: {remote_app.resource_name}\n")
    
    # Save ID
    with open("REASONING_ENGINE_ID.txt", "w") as f:
        f.write(remote_app.resource_name)
    
    print("Test with:")
    print(f'  response = remote_app.query("Yo, status check")')
