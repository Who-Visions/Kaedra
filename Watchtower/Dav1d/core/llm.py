import os
import time
from google import genai
from google.genai.types import GenerateContentConfig, HarmCategory, HarmBlockThreshold
from config import PROJECT_ID, LOCATION, Colors

# Define default safety settings
safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": HarmBlockThreshold.BLOCK_NONE,
    },
]

from core.cost_manager import cost_manager

class GenAIModelAdapter:
    """Adapter to make new Gen AI SDK look like the old one for compatibility."""
    def __init__(self, client, model_name, system_instruction=None, config=None):
        self.client = client
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.config = config or GenerateContentConfig()
        
        # Ensure system instruction is in config if provided
        if system_instruction:
            self.config.system_instruction = system_instruction

    def generate_content(self, prompt, stream=False):
        # 1. Check budget before generation (Double check in case of long running session)
        # Note: We can't easily switch models inside the adapter instance, 
        # but we can log a warning if we're over budget.
        # The switching happens at get_model time.
        
        try:
            start_time = time.time()
            if stream:
                response = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=prompt,
                    config=self.config
                )
                # Stream usage tracking is harder, skipping for now or need to iterate
                return response
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=self.config
                )
                
                # 2. Record Usage
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count or 0
                    output_tokens = response.usage_metadata.candidates_token_count or 0
                    
                    # Map model name to key if possible, or just use name
                    # Simple heuristic mapping
                    model_key = "balanced" # Default
                    if "gemini-3.0" in self.model_name: model_key = "deep"
                    elif "flash" in self.model_name: model_key = "flash"
                    
                    cost_manager.record_usage(model_key, input_tokens, output_tokens)
                    
                return response
                
        except Exception as e:
            # Handle rate limits or other API errors
            if "429" in str(e):
                print(f"{Colors.NEON_RED}[!] Rate limit hit. Retrying in 5s...{Colors.RESET}")
                time.sleep(5)
                return self.generate_content(prompt, stream)
            raise e

    def start_chat(self, history=None):
        return self.client.chats.create(
            model=self.model_name,
            history=history or [],
            config=self.config
        )

def get_dav1d_client():
    """Initialize the Gen AI client."""
    return genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def get_model(model_name: str, mode: str = "default", tools: list = None, system_instruction: str = None):
    """Get model with system instructions and thinking config using new SDK."""
    
    # 1. Check Budget & Fallback
    safe_model_name = cost_manager.get_safe_model(model_name)
    
    # 2. Dynamic Location Routing: Gemini 3 models require 'global' location
    if "gemini-3" in safe_model_name:
        location = "global"
    else:
        location = LOCATION  # us-east4 for Gemini 2.5 models
    
    # Create client with appropriate location
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=location)
    
    # Configure generation settings
    # Google recommends temperature=1.0 for Gemini 3.0 Pro
    generation_config = GenerateContentConfig(
        temperature=1.0 if "gemini-3" in safe_model_name else 0.7,
        top_p=0.95,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=safety_settings,
        tools=tools
    )

    return GenAIModelAdapter(
        client=client,
        model_name=safe_model_name,
        system_instruction=system_instruction,
        config=generation_config
    )
