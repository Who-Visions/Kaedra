import os
import time
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Kaedra core components
from kaedra.services.prompt import PromptService
from kaedra.services.memory import MemoryService
from kaedra.agents.kaedra import KaedraAgent
from kaedra.core.config import PROJECT_ID, LOCATION, AGENT_RESOURCE_NAME

# Load environment variables
load_dotenv()

# Service Metadata
SERVICE_NAME = "kaedra-shadow-tactician"
SERVICE_ICON = "🌑"
SERVICE_ROLE = "Shadow Tactician"
SERVICE_DESCRIPTION = "Strategic intelligence partner for Who Visions LLC. Speaks authentic AAVE, thinks tactically, orchestrates multi-agent operations."
CLOUD_RUN_URL = "https://kaedra-69017097813.us-central1.run.app"

app = FastAPI(
    title="Kaedra API",
    description="Shadow Tactician Agent API",
    version="0.0.6"
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
    "version": "0.0.6",
    "id": "kaedra-shadow-tactician",
    "description": SERVICE_DESCRIPTION,
    "role": SERVICE_ROLE,
    "icon": SERVICE_ICON,
    "capabilities": [
        "strategic_planning",
        "intelligence_synthesis",
        "shadow_operations",
        "multi_agent_coordination",
        "gemini-3-reasoning"
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

state = AppState()

@app.on_event("startup")
async def startup_event():
    """Initialize Kaedra agent on startup."""
    print(f"[*] Initializing Kaedra Agent (Project: {PROJECT_ID})...")
    try:
        # Initialize services
        prompt_service = PromptService(project=PROJECT_ID, location=LOCATION)
        memory_service = MemoryService() # Assumes default init is fine
        
        # Initialize Agent
        state.agent = KaedraAgent(prompt_service, memory_service)
        print("[+] Kaedra Agent initialized successfully.")
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
    content: str

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

# -------------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Fleet standard health check."""
    return {
        "status": "ok",
        "service": "kaedra-shadow-tactician",
        "version": "0.0.6",
        "grounding_enabled": True
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "Kaedra",
        "version": "0.0.6",
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

@app.post("/v1/chat/completions", response_model=OpenAIChatCompletionResponse)
async def openai_chat_endpoint(request: OpenAIChatCompletionRequest):
    """
    OpenAI-compatible chat endpoint for Fleet usage.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Extract last message as the prompt
        last_message = request.messages[-1].content
        
        # Build context from previous messages if any
        context_str = ""
        if len(request.messages) > 1:
            context_str = "\n".join([f"{m.role}: {m.content}" for m in request.messages[:-1]])

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
        "version": "0.0.6",
        "capabilities": [
            "strategic-planning",
            "intelligence-synthesis",
            "multi-agent-coordination",
            "gemini-3-reasoning"
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
