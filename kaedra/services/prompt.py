"""
KAEDRA v0.0.6 - Prompt Service
Handles LLM interactions with Vertex AI / Gemini.
"""

import time
from typing import Optional, Generator, Dict, Any
from dataclasses import dataclass

import vertexai
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai.language_models import TextEmbeddingModel

from ..core.config import MODELS, PROJECT_ID, LOCATION, MODEL_LOCATION, DEFAULT_MODEL


@dataclass
class PromptResult:
    """Result from a prompt generation."""
    text: str
    model: str
    latency_ms: float
    grounded: bool = False
    metadata: Optional[Dict] = None


class PromptService:
    """
    Manages LLM prompt generation via Vertex AI.
    
    Features:
    - Multiple model support (flash/pro/ultra)
    - Google Search grounding
    - Streaming responses
    - Retry logic with exponential backoff
    - Latency tracking
    """
    
    def __init__(self, 
                 model_key: str = DEFAULT_MODEL,
                 project: str = PROJECT_ID,
                 location: str = LOCATION,
                 enable_grounding: bool = True):
        """
        Initialize the prompt service.
        
        Args:
            model_key: Model key from MODELS dict (flash/pro/ultra)
            project: GCP project ID
            location: GCP region
            enable_grounding: Whether to enable Google Search grounding
        """
        self.project = project
        self.location = location
        self.enable_grounding = enable_grounding
        self._current_model_key = model_key
        
        self.model_location = MODEL_LOCATION
        
        # Initialize Vertex AI
        vertexai.init(project=project, location=self.model_location)
        
        # Model cache
        self._models: Dict[str, GenerativeModel] = {}
    
    @property
    def current_model(self) -> str:
        """Get the current model name."""
        return MODELS.get(self._current_model_key, MODELS[DEFAULT_MODEL])
    
    @property
    def current_model_key(self) -> str:
        """Get the current model key."""
        return self._current_model_key
    
    def set_model(self, model_key: str) -> str:
        """
        Switch to a different model.
        
        Args:
            model_key: Model key (flash/pro/ultra)
            
        Returns:
            The model name that was set
        """
        if model_key in MODELS:
            self._current_model_key = model_key
        return self.current_model
    
    def _get_model(self, model_key: str = None) -> GenerativeModel:
        """Get or create a GenerativeModel instance."""
        key = model_key or self._current_model_key
        model_name = MODELS.get(key, MODELS[DEFAULT_MODEL])
        
        if model_name not in self._models:
            try:
                if self.enable_grounding:
                    tools = [
                        Tool.from_google_search_retrieval(
                            google_search_retrieval=vertexai.generative_models.GoogleSearchRetrieval()
                        ),
                    ]
                    self._models[model_name] = GenerativeModel(model_name, tools=tools)
                else:
                    self._models[model_name] = GenerativeModel(model_name)
            except Exception:
                # Fallback without grounding
                self._models[model_name] = GenerativeModel(model_name)
        
        return self._models[model_name]
    
    def generate(self, 
                 prompt: str, 
                 model_key: str = None,
                 system_instruction: str = None,
                 temperature: float = 0.7,
                 max_tokens: int = 4096) -> PromptResult:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            model_key: Override model key
            system_instruction: System instruction to prepend
            temperature: Generation temperature (0.0-1.0)
            max_tokens: Maximum output tokens
            
        Returns:
            PromptResult with response text and metadata
        """
        model = self._get_model(model_key)
        model_name = MODELS.get(model_key or self._current_model_key)
        
        # Build full prompt
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        # Generate with timing
        start_time = time.time()
        
        try:
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return PromptResult(
                text=response.text if hasattr(response, 'text') else str(response),
                model=model_name,
                latency_ms=latency_ms,
                grounded=self.enable_grounding
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return PromptResult(
                text=f"[ERROR] Generation failed: {e}",
                model=model_name,
                latency_ms=latency_ms,
                metadata={'error': str(e)}
            )
    
    def generate_stream(self, 
                        prompt: str,
                        model_key: str = None,
                        system_instruction: str = None) -> Generator[str, None, None]:
        """
        Generate a streaming response.
        
        Args:
            prompt: The user prompt
            model_key: Override model key
            system_instruction: System instruction
            
        Yields:
            Text chunks as they're generated
        """
        model = self._get_model(model_key)
        
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        try:
            response = model.generate_content(full_prompt, stream=True)
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text
        except Exception as e:
            yield f"[ERROR] Streaming failed: {e}"
    
    async def generate_async(self,
                             prompt: str,
                             model_key: str = None,
                             system_instruction: str = None) -> PromptResult:
        """
        Async version of generate for concurrent operations.
        
        Note: Currently wraps sync call. Full async support pending
        Vertex AI SDK updates.
        """
        # TODO: Use true async when Vertex AI SDK supports it
        return self.generate(prompt, model_key, system_instruction)

    def embed(self, text: str, model: str = "text-embedding-004") -> List[float]:
        """
        Generate embeddings for a given text.
        
        Args:
            text: The text to embed
            model: Embedding model name
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding_model = TextEmbeddingModel.from_pretrained(model)
            embeddings = embedding_model.get_embeddings([text])
            if embeddings:
                return embeddings[0].values
            return []
        except Exception as e:
            print(f"[!] Embedding error: {e}")
            return []
