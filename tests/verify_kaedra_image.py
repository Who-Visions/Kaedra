import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from kaedra.agents.kaedra import KaedraAgent
from kaedra.services.prompt import PromptService

class MockPromptResult:
    def __init__(self, text):
        self.text = text
        self.model = "mock-model"

class MockPromptService(PromptService):
    def generate(self, prompt, **kwargs):
        if "generate_image" in prompt:
            # First pass: Model suggests the tool
            return MockPromptResult('[TOOL: generate_image(prompt="a cinematic shot of a shadow tactician")]')
        # Second pass: Model acknowledges the tool result
        return MockPromptResult("Aight, I generated that image for you. It's looking sharp.")

async def verify_agent_image():
    print("--- Verifying KaedraAgent Image Integration ---")
    
    # Check if google-genai is installed
    try:
        from google import genai
        print(f"[✅] google-genai is installed (SDK version: {genai.__version__ if hasattr(genai, '__version__') else 'unknown'})")
    except ImportError:
        print("[!] google-genai is NOT installed.")
        return

    # Initialize Agent
    prompt_service = MockPromptService()
    agent = KaedraAgent(prompt_service=prompt_service)
    
    if agent.genai_client:
        print("[✅] KaedraAgent genai_client initialized.")
    else:
        print("[!] KaedraAgent genai_client NOT initialized. Check Vertex AI creds/PROJECT_ID.")

    # Test Tool Parsing (Dry Run - since we don't want to actually call the API and spend money/fail without creds)
    print("\n[Testing Tool Parsing & Execution Flow]")
    
    # We'll monkey-patch the client call to avoid real API hit
    if agent.genai_client:
        # Mock generate_images (Gemini 3)
        def mock_generate_images(*args, **kwargs):
            print(f"[*] MAPPED Gemini 3 API CALL: model='{kwargs.get('model')}', prompt='{kwargs.get('prompt')}'")
            class MockResp: 
                model = "gemini-3-pro-image-preview"
                generated_images = [type('obj', (object,), {'image': type('obj', (object,), {'image_bytes': b'fake'})})()]
            return MockResp()
        
        agent.genai_client.models.generate_images = mock_generate_images
        
        # Mock generate_content (Fallback)
        def mock_generate_content(*args, **kwargs):
            print(f"[*] MAPPED Fallback API CALL: model='{kwargs.get('model')}'")
            class MockResp:
                model = kwargs.get('model')
                parts = [type('obj', (object,), {'as_image': lambda: "MOCK_IMAGE"})()]
            return MockResp()
        
        agent.genai_client.models.generate_content = mock_generate_content
        
        # Mock _backup_asset
        def mock_backup(data, prompt, content_type):
            print(f"[*] MAPPED GCS BACKUP: prompt='{prompt[:20]}...', content_type='{content_type}'")
            return "gs://mock-bucket/mock-image.jpg"
        
        agent._backup_asset = mock_backup
        
        print("\n[Test 1: Gemini 3 Path]")
        response = await agent.run("Generate an image of a cybernetic lion.")
        print(f"Final Response: {response.content}")
        
        print("\n[Test 2: Fallback Path]")
        # Force fallback by making generate_images fail
        def fail_gen(*args, **kwargs): raise Exception("Simulated Gemini 3 Failure")
        agent.genai_client.models.generate_images = fail_gen
        response = await agent.run("Generate another image.")
        print(f"Final Response: {response.content}")
    else:
        print("[!] Skipping tool execution test as client is missing.")

if __name__ == "__main__":
    asyncio.run(verify_agent_image())
