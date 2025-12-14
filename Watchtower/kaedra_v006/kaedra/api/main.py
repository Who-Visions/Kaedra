import os
import time
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from dotenv import load_dotenv

# Import Kaedra core components
from kaedra.services.prompt import PromptService
from kaedra.services.memory import MemoryService
from kaedra.agents.kaedra import KaedraAgent
from kaedra.core.config import PROJECT_ID, LOCATION

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Kaedra API",
    description="Shadow Tactician Agent API",
    version="0.0.6"
)

# -------------------------------------------------------------------------
# CONSTANTS & A2A CARD
# -------------------------------------------------------------------------

A2A_CARD = {
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
        "chat": "/v1/chat",
        "info": "/v1/api"
    },
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "context": {"type": "string", "nullable": True}
        },
        "required": ["message"]
    },
    "meta": {
        "framework": "FastAPI",
        "language": "Python",
        "deploy_region": LOCATION
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

# -------------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------------

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
    Chat with Kaedra.
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

@app.get("/a2a")
async def get_a2a_card():
    """Return the Agent-to-Agent (A2A) Card."""
    return A2A_CARD

@app.get("/a2a/card")
async def get_a2a_card_alias():
    """Alias for A2A Card."""
    return A2A_CARD

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
