import os
import time
from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Kaedra core components
from kaedra.services.prompt import PromptService
from kaedra.services.memory import MemoryService
from kaedra.services.research import ResearchService
from kaedra.services.web import WebService
from kaedra.services.wispr import WisprMonitor
from kaedra.services.tts import TTSService
from kaedra.agents.kaedra import KaedraAgent
from kaedra.core.config import PROJECT_ID, LOCATION, AGENT_RESOURCE_NAME
from kaedra.core.google_tools import GOOGLE_TOOLS
from kaedra.core.tools import FreeToolsRegistry

# Load environment variables
load_dotenv()

# Service Metadata
SERVICE_NAME = "kaedra-shadow-tactician"
SERVICE_ICON = "🌑"
SERVICE_ROLE = "Shadow Tactician"
SERVICE_DESCRIPTION = "Strategic intelligence partner for Who Visions LLC. Speaks authentic AAVE, thinks tactically, orchestrates multi-agent operations."
CLOUD_RUN_URL = "https://kaedra-69017097813.us-central1.run.app"

    title="Kaedra API",
    description="Shadow Tactician Agent API",
    version="0.0.8"
)

# -------------------------------------------------------------------------
# CORS MIDDLEWARE - Allow cross-origin requests
# -------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (adjust for production if needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# -------------------------------------------------------------------------
# CONSTANTS & A2A CARD
# -------------------------------------------------------------------------

A2A_CARD = {
    "name": "Kaedra",
    "version": "0.0.8",
    "id": "kaedra-shadow-tactician",
    "description": SERVICE_DESCRIPTION,
    "role": SERVICE_ROLE,
    "icon": SERVICE_ICON,
    "capabilities": [
        "strategic_planning",
        "intelligence_synthesis",
        "shadow_operations",
        "multi_agent_coordination",
        "gemini-3-reasoning",
        "voice_command_listener"
    ],
    "endpoints": {
        "chat": "/v1/chat/completions",
        "info": "/.well-known/agent.json"
    },
    "input_schema": {
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            }
        },
        "required": ["messages"]
    },
    "meta": {
        "framework": "FastAPI",
        "language": "Python",
        "deploy_url": CLOUD_RUN_URL
    }
}

# -------------------------------------------------------------------------
# GLOBAL STATE
# -------------------------------------------------------------------------

class AppState:
    agent: Optional[KaedraAgent] = None
    research_service: Optional[ResearchService] = None
    web_service: Optional[WebService] = None
    wispr_service: Optional[WisprMonitor] = None # Changed from wispr_monitor
    tts_service: Optional[TTSService] = None # Added tts_service

state = AppState()

async def handle_voice_command(command_text: str):
    """Callback for when Wispr detects a wake word."""
    print(f"\n[MIC] Detected Command: {command_text}")
    
    if state.agent:
        # Send to agent as if it were a chat message (but marked as voice)
        print(f"[*] Processing voice command with Kaedra...")
        
        # Add voice context
        context = f"[VOICE COMMAND] User said: '{command_text}' via Wispr Flow."
        
        # Run agent
        response = await state.agent.run(query=command_text, context=context)
        
        # Log response
        # Note: Colors.kaedra_tag() is not defined in the provided context, omitting for now.
        print(f"\nKaedra: {response.content}\n") 
        
        # Speak response if TTS is available
        if state.tts_service:
            # Run in thread pool to avoid blocking async loop with synchronous playback
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, state.tts_service.speak, response.content)
            
    else:
        print("[!] Agent not initialized yet.")

@app.on_event("startup")
async def startup_event():
    """Initialize Kaedra agent on startup."""
    print(f"[*] Initializing Kaedra Agent (Project: {PROJECT_ID})...")
    try:
        # Initialize services
        prompt_service = PromptService(project=PROJECT_ID, location=LOCATION)
        memory_service = MemoryService() # Assumes default init is fine
        
        # Initialize Services
        state.web_service = WebService()
        state.research_service = ResearchService(prompt_service)
        
        # TTS only works on local machines with audio output (not Cloud Run)
        try:
            state.tts_service = TTSService()
        except Exception as tts_err:
            print(f"[!] TTS unavailable (normal for Cloud Run): {tts_err}")
            state.tts_service = None
        
        # Initialize Agent
        state.agent = KaedraAgent(prompt_service, memory_service)
        print("[+] Kaedra Agent initialized successfully.")
        
        # Initialize Wispr Monitor
        # Only start if on local Windows machine or appropriately configured environment
        # We can check for the existence of the DB path in the class init logic
        user_home = os.environ.get("USERPROFILE", "")
        if "super" in user_home.lower(): # Simple check to only run on your local machine
            print("[*] Starting Wispr Listener...")
            state.wispr_monitor = WisprMonitor(callback=handle_voice_command)
            await state.wispr_monitor.start()
            
    except Exception as e:
        print(f"[!] Failed to initialize Kaedra Agent: {e}")
        # We don't raise here to allow the server to start, but agent endpoints will fail

# -------------------------------------------------------------------------
# DATA MODELS
# -------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    model: str
    latency_ms: float
    timestamp: float

# OpenAI-Compatible Models
class OpenAIMessage(BaseModel):
    role: str
    content: Union[str, List[Any]]

class OpenAIChatCompletionRequest(BaseModel):
    model: Optional[str] = "gemini-3-flash-preview"
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class OpenAIChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str

class OpenAIChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: Dict[str, int]

# Fleet Request Models
class GenerateRequest(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-3-flash-preview"

class SearchRequest(BaseModel):
    query: str
    num_results: int = 5

class AnalyzeUrlRequest(BaseModel):
    url: str

class ExecuteCodeRequest(BaseModel):
    code: str
    language: str = "python"

class ResearchRequest(BaseModel):
    query: str

class EmbeddingRequest(BaseModel):
    text: str
    model: str = "text-embedding-004"

# -------------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Fleet standard health check."""
    return {
        "status": "ok",
        "service": "kaedra-shadow-tactician",
        "version": "0.0.8",
        "grounding_enabled": True
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "Kaedra",
        "version": "0.0.8",
        "docs": "/docs"
    }

@app.get("/v1")
async def v1_root():
    return {
        "version": "v1",
        "services": ["chat", "api"]
    }

@app.get("/v1/api")
async def v1_api_info():
    """General API information."""
    return {
        "name": "Kaedra Intelligence API",
        "endpoints": ["/v1/chat"],
        "status": "operational"
    }

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Kaedra (Legacy Endpoint).
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Use run_sync logic but inside an async wrapper if needed, 
        # but KaedraAgent.run is async, so we await it.
        # Note: KaedraAgent.run returns AgentResponse object
        result = await state.agent.run(request.message, request.context)
        
        return ChatResponse(
            response=result.content,
            agent_name=result.agent_name,
            model=result.model,
            latency_ms=result.latency_ms,
            timestamp=time.time()
        )
    except Exception as e:
        print(f"[!] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _extract_text(content: Union[str, List[Any]]) -> str:
    """Helper to extract text from OpenAI content (str or list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Extract all text parts
        text_parts = [
            part["text"] for part in content 
            if isinstance(part, dict) and part.get("type") == "text" and "text" in part
        ]
        return "\n".join(text_parts)
    return str(content)

@app.post("/v1/chat/completions", response_model=OpenAIChatCompletionResponse)
async def openai_chat_endpoint(request: OpenAIChatCompletionRequest):
    """
    OpenAI-compatible chat endpoint for Fleet usage.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Extract last message as the prompt
        last_content = request.messages[-1].content
        last_message = _extract_text(last_content)
        
        # Build context from previous messages if any
        context_str = ""
        if len(request.messages) > 1:
            context_entries = []
            for m in request.messages[:-1]:
                m_text = _extract_text(m.content)
                context_entries.append(f"{m.role}: {m_text}")
            context_str = "\n".join(context_entries)

        # Run agent
        result = await state.agent.run(last_message, context_str)
        
        return OpenAIChatCompletionResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=result.model,
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content=result.content),
                    finish_reason="stop"
                )
            ],
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )
    except Exception as e:
        print(f"[!] OpenAI chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=OpenAIChatCompletionResponse)
async def fleet_chat_endpoint(request: OpenAIChatCompletionRequest):
    """
    Standard Fleet Chat Endpoint (alias for /v1/chat/completions).
    """
    return await openai_chat_endpoint(request)

@app.post("/generate")
async def fleet_generate(request: GenerateRequest):
    """
    Fleet Generate Endpoint: Direct text generation.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await state.agent.prompt_service.generate_async(
        prompt=request.prompt,
        model_key="flash" # Default to Flash for speed
    )
    return {"text": result.text, "model": result.model}

@app.post("/search")
async def fleet_search(request: SearchRequest):
    """
    Fleet Search Endpoint: Grounded Google Search.
    """
    return GOOGLE_TOOLS["google_search"](request.query, request.num_results)

@app.post("/analyze-url")
async def fleet_analyze_url(request: AnalyzeUrlRequest):
    """
    Fleet Analyze URL Endpoint: Scrape and Metadata.
    """
    if not state.web_service:
        state.web_service = WebService()
    
    metadata = state.web_service.extract_metadata(request.url)
    return metadata

@app.post("/execute-code")
async def fleet_execute_code(request: ExecuteCodeRequest):
    """
    Fleet Execute Code Endpoint (Simulation/Prompt-based for now).
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # TODO: Connect to Vertex AI Code Execution Tool if available
    prompt = f"Executing {request.language} code:\n```\n{request.code}\n```\n\nSimulate the output of this code:"
    result = await state.agent.prompt_service.generate_async(prompt)
    return {"output": result.text, "status": "simulated"}

@app.post("/research")
async def start_research(request: ResearchRequest):
    """
    Deep Research Endpoint: Starts a research task.
    """
    if not state.research_service:
        raise HTTPException(status_code=503, detail="Research Service not initialized")
    
    task_id = state.research_service.create_task(request.query)
    return {"task_id": task_id, "status": "pending", "message": "Research task started"}

@app.get("/research/{task_id}")
async def get_research_status(task_id: str):
    """
    Get Research Status.
    """
    if not state.research_service:
        raise HTTPException(status_code=503, detail="Research Service not initialized")
    
    task = state.research_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Create Embeddings Endpoint.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    vector = state.agent.prompt_service.embed(request.text, request.model)
    return {
        "object": "list",
        "data": [{"object": "embedding", "embedding": vector, "index": 0}],
        "model": request.model
    }

@app.get("/health/detailed")
async def health_detailed():
    """
    Detailed System Health Check.
    """
    sys_info = FreeToolsRegistry.get_system_info()
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "system": sys_info,
        "timestamp": time.time()
    }

@app.get("/a2a")
async def get_a2a_card():
    """Return the Agent-to-Agent (A2A) Card."""
    return A2A_CARD

@app.get("/a2a/card")
async def get_a2a_card_alias():
    """Alias for A2A Card."""
    return A2A_CARD

@app.get("/.well-known/agent.json")
async def get_agent_card_standard():
    """
    Standard Agent Identity Card for Who Visions Fleet.
    Compliant with /.well-known/agent.json specification.
    """
    return {
        "name": "Kaedra",
        "description": SERVICE_DESCRIPTION,
        "icon": SERVICE_ICON,
        "role": SERVICE_ROLE,
        "version": "0.0.8",
        "capabilities": [
            "strategic-planning",
            "intelligence-synthesis",
            "multi-agent-coordination",
            "gemini-3-reasoning",
            "deep-research",
            "embeddings",
            "code-execution"
        ],
        "endpoints": {
            "chat": f"{CLOUD_RUN_URL}/v1/chat/completions",
            "health": f"{CLOUD_RUN_URL}/health",
            "card": f"{CLOUD_RUN_URL}/.well-known/agent.json"
        },
        "extensions": {
            "color": "neon pink",
            "personality": "AAVE, tactical, uncensored",
            "deploy_region": LOCATION,
            "reasoning_engine": AGENT_RESOURCE_NAME
        }
    }

# -------------------------------------------------------------------------
# RUNNER
# -------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    # Default to port 8000 or allow env override
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"[*] Starting Kaedra Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
