"""
KAEDRA v0.1.0 - Prompt Service
Handles LLM interactions with Vertex AI / Gemini via google-genai SDK.
Integrates GeminiSmartRouter for dual-brain (Flash + Pro) orchestration.
"""

import time
import asyncio
from typing import Optional, Generator, Dict, Any, List, Union
from dataclasses import dataclass, field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from ..core.config import MODELS, PROJECT_ID, LOCATION, MODEL_LOCATION, DEFAULT_MODEL

@dataclass
class PromptResult:
    """Result from a prompt generation."""
    text: str
    model: str
    latency_ms: float
    grounded: bool = False
    thoughts: Optional[str] = None
    metadata: Optional[Dict] = None

class PromptService:
    """
    Manages LLM prompt generation with Smart Routing.
    
    Features:
    - Dual-Brain Architecture (Flash fast, Pro deep)
    - Automatic scaling based on query complexity (Smart Router)
    - Thinking Level Support (Minimal, High)
    - Google Search grounding integration
    """
    
    DEEP_THINKING_KEYWORDS = [
        "research", "analyze", "deep dive", "review", "debug",
        "check this code", "plan", "strategy", "step by step",
        "break down", "compare", "evaluate", "investigate", "explain why"
    ]
    
    def __init__(self, 
                 model_key: str = DEFAULT_MODEL,
                 project: str = PROJECT_ID,
                 location: str = "global", # Gemini 3 requires global endpoint for dynamic routing
                 enable_grounding: bool = True):
        """Initialize with Vertex AI settings."""
        self.project = project
        self.location = location
        self.enable_grounding = enable_grounding
        self._default_model_key = model_key
        
        # Initialize Client
        if genai:
            self.client = genai.Client(vertexai=True, project=project, location=location)
        else:
            self.client = None
            print("[!] PromptService: google-genai SDK not found.")

    def needs_deep_thinking(self, query: str) -> bool:
        """Detect if query requires Gemini 3 Pro reasoning."""
        q_lower = query.lower()
        return any(kw in q_lower for kw in self.DEEP_THINKING_KEYWORDS)

    def _get_config(self, thinking_level: str = "high") -> Any:
        """Build standard generation config with Gemini 3 thinking."""
        tools = []
        if self.enable_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
            
        return types.GenerateContentConfig(
            temperature=1.0, # Recommended for Gemini 3
            tools=tools if tools else None,
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level, include_thoughts=True)
        )

    def generate(self, 
                 prompt: str, 
                 model_key: str = None,
                 system_instruction: str = None,
                 temperature: float = 1.0,
                 max_tokens: int = 4096,
                 response_schema: Dict = None,
                 response_mime_type: str = None) -> PromptResult:
        """
        Synchronous generation with Smart Routing.
        """
        return asyncio.run(self.generate_async(
            prompt, model_key, system_instruction, 
            temperature, max_tokens, response_schema, response_mime_type
        ))

    async def generate_async(self,
                             prompt: str,
                             model_key: str = None,
                             system_instruction: str = None,
                             temperature: float = 1.0,
                             max_tokens: int = 4096,
                             response_schema: Dict = None,
                             response_mime_type: str = None) -> PromptResult:
        """
        Async generation with Smart Router logic.
        """
        if not self.client:
            return PromptResult("[!] GenAI Client not initialized", "N/A", 0)

        # 1. Smart Routing Logic
        target_model_key = model_key or self._default_model_key
        thinking_level = "low" # Standard Flash speed
        
        # Automatic Scale-up
        if not model_key and self.needs_deep_thinking(prompt):
            target_model_key = "pro"
            thinking_level = "high"
            print(f"[*] Smart Router: Escalating to Pro (High Thinking)")
        elif target_model_key == "flash" and not self.needs_deep_thinking(prompt):
             # For ultra fast simple tasks on flash
             thinking_level = "minimal"

        model_id = MODELS.get(target_model_key, MODELS[DEFAULT_MODEL])
        
        # 2. Build Config
        gen_config = self._get_config(thinking_level)
        gen_config.temperature = 1.0 # Force 1.0 as per best practices
        gen_config.max_output_tokens = max_tokens
        gen_config.system_instruction = system_instruction
        
        if response_schema:
            gen_config.response_schema = response_schema
            gen_config.response_mime_type = "application/json"
        elif response_mime_type:
            gen_config.response_mime_type = response_mime_type

        # 3. Execution
        start_time = time.time()
        try:
            # We use the aio (async) client
            response = await self.client.aio.models.generate_content(
                model=model_id,
                contents=prompt,
                config=gen_config
            )
            
            latency = (time.time() - start_time) * 1000
            
            # Extract content and thoughts
            final_text = ""
            thoughts = ""
            
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.thought:
                        thoughts += part.text
                    elif part.text:
                        final_text += part.text
            
            return PromptResult(
                text=final_text or response.text,
                model=model_id,
                latency_ms=latency,
                grounded=self.enable_grounding,
                thoughts=thoughts if thoughts else None
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            print(f"[!] Generation failed: {e}")
            return PromptResult(f"[ERROR] {e}", model_id, latency, metadata={"error": str(e)})

    def generate_stream(self, 
                        prompt: str,
                        model_key: str = None,
                        system_instruction: str = None) -> Generator[str, None, None]:
        """
        Generator for streaming responses (Sync wrapper for aio).
        """
        async def _stream():
            config = self._get_config("minimal")
            config.system_instruction = system_instruction
            model_id = MODELS.get(model_key or self._default_model_key, MODELS[DEFAULT_MODEL])
            
            stream = await self.client.aio.models.generate_content_stream(
                model=model_id,
                contents=prompt,
                config=config
            )
            async for chunk in stream:
                yield chunk.text

        # This is tricky for a sync generator. For now, we recommend use_async
        # or implement a thread-loop bridge if absolutely needed.
        # Most modern Kaedra surfaces are transitioning to async.
        raise NotImplementedError("Use generate_async_stream instead.")

    async def generate_async_stream(self, prompt: str, model_key: str = None, system_instruction: str = None):
         """True async stream handling."""
         target_model_key = model_key or self._default_model_key
         thinking_level = "minimal"
         if not model_key and self.needs_deep_thinking(prompt):
            target_model_key = "pro"
            thinking_level = "high"

         model_id = MODELS.get(target_model_key, MODELS[DEFAULT_MODEL])
         config = self._get_config(thinking_level)
         config.system_instruction = system_instruction
         
         return await self.client.aio.models.generate_content_stream(
             model=model_id,
             contents=prompt,
             config=config
         )

    def embed(self, text: str, model: str = "text-embedding-004") -> List[float]:
        """Generate embeddings using the modern client."""
        if not self.client: return []
        try:
             # Simplified sync call for embeddings usually okay
             response = self.client.models.embed_content(
                 model=model,
                 contents=text
             )
             return response.embeddings[0].values
        except Exception as e:
            print(f"[!] Embedding error: {e}")
            return []
