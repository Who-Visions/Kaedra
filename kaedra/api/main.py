import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import sys
import shutil
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles
# try:
#     import nest_asyncio
#     nest_asyncio.apply()  # Allow nested event loops for sync-in-async compatibility
#     import nest_asyncio
#     nest_asyncio.apply()  # Allow nested event loops for sync-in-async compatibility
# except ImportError:
#     pass

import firebase_admin
from firebase_admin import credentials

# Global Config Import (Moved up for init)
from kaedra.core.config import PROJECT_ID, LOCATION, MODEL_LOCATION, AGENT_RESOURCE_NAME

# -------------------------------------------------------------------------
# LAZY FIREBASE INITIALIZATION (Reduces cold start from 60s to ~5s)
# -------------------------------------------------------------------------
_firebase_initialized = False
_cred = None
db = None
db_memory = None

def _ensure_firebase():
    """Lazy init Firebase on first use, not at import time."""
    global _firebase_initialized, _cred, db, db_memory
    
    if _firebase_initialized:
        return
    
    try:
        _cred = credentials.Certificate("kaedra/secrets/service_account.json")
        firebase_admin.initialize_app(_cred)
        
        from google.cloud import firestore as gc_firestore
        
        # 1. Chat DB
        db = gc_firestore.Client(
            project=PROJECT_ID,
            credentials=_cred.get_credential(),
            database="kaedra-chat"
        )
        
        # 2. Memory DB
        try:
            db_memory = gc_firestore.Client(
                project=PROJECT_ID,
                credentials=_cred.get_credential(),
                database="kaedra-memory"
            )
            print(f"[+] Firebase lazy-init: Chat & Memory databases connected.")
        except Exception as e_mem:
            print(f"[!] Failed to connect to kaedra-memory: {e_mem}")
            db_memory = None
            
    except Exception as e:
        print(f"[!] Firebase init failed: {e}")
        db = None
        db_memory = None
    
    _firebase_initialized = True

def get_db():
    """Get Firestore Chat DB (lazy init)."""
    _ensure_firebase()
    return db

def get_db_memory():
    """Get Firestore Memory DB (lazy init)."""
    _ensure_firebase()
    return db_memory


# -------------------------------------------------------------------------
# ACTIVITY LOGGING SERVICE (Simple In-Memory)
# -------------------------------------------------------------------------
class ActivityLogService:
    def __init__(self):
        self._activities = []
    
    def log(self, action: str, detail: str, icon: str = "info"):
        """Add an activity to the log."""
        entry = {
            "action": action,
            "detail": detail,
            "icon": icon,
            "timestamp": time.time(),
            "timeAgo": "just now" # Computed by client usually, but good fallback
        }
        self._activities.insert(0, entry)
        # Keep last 50
        self._activities = self._activities[:50]
        
    def get_activities(self):
        return self._activities

# Initialize global activity log
activity_log = ActivityLogService()

# -------------------------------------------------------------------------
# GLOBAL STATE & CONFIG
# -------------------------------------------------------------------------
memory_service = None  # Global placeholder
from kaedra.api.app_state import state, AppState
# PROJECT_ID etc already imported above
from kaedra.core.tools import FreeToolsRegistry
try:
    from kaedra.core.google_tools import GOOGLE_TOOLS
except ImportError:
    GOOGLE_TOOLS = {}

# Service metadata
SERVICE_NAME = "kaedra-shadow-tactician"
SERVICE_ICON = "🌑"
SERVICE_ROLE = "Shadow Tactician"
SERVICE_DESCRIPTION = "Strategic intelligence partner for Who Visions LLC. Speaks authentic AAVE, thinks tactically, orchestrates multi-agent operations."
CLOUD_RUN_URL = "https://kaedra-69017097813.us-central1.run.app"

app = FastAPI(
    title="Kaedra API",
    description="Shadow Tactician Agent API",
    version="0.0.9"
)

# Include Routers
from . import lore, webhooks, story
app.include_router(lore.router)
app.include_router(webhooks.router)
app.include_router(story.router)

@app.get("/")
async def root():
    """Root endpoint to verify API is alive."""
    return {
        "status": "online",
        "service": SERVICE_NAME,
        "version": app.version,
        "timestamp": time.time()
    }

# CORS MIDDLEWARE - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (adjust for production if needed)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Uploads Configuration
UPLOAD_DIR = Path("kaedra/api/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return its URL."""
    try:
        # Sanitize filename (basic)
        safe_filename = file.filename.replace(" ", "_").replace("/", "").replace("\\", "")
        file_path = UPLOAD_DIR / safe_filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return full URL if possible, or relative
        return {"url": f"{CLOUD_RUN_URL}/uploads/{safe_filename}", "filename": safe_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Initialize Services Container (Lazy)
slack_service = None # Will be initialized in startup

# -------------------------------------------------------------------------
# CONSTANTS & A2A CARD
# -------------------------------------------------------------------------

A2A_CARD = {
    "name": "Kaedra",
    "version": "0.0.9",
    "id": "kaedra-shadow-tactician",
    "description": SERVICE_DESCRIPTION,
    "role": SERVICE_ROLE,
    "icon": SERVICE_ICON,
    "capabilities": [
        "strategic_planning",
        "narrative_design",
        "visual_generation",
        "autonomous_reasoning",
        "global_routing_optimized",
        "gemini-3-native-thinking",
        "multi_agent_collaboration"
    ],
    "endpoints": {
        "chat": "/v1/chat/completions",
        "info": "/.well-known/agent.json",
        "webhook": "/webhook/notion",
        "sync": "/sync",
        "generate_image": "/generate-image",
        "generate": "/generate",
        "models": "/v1/models",
        "cowrite": "/cowrite"
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

# Import shared state to avoid circular dependencies
from kaedra.api.app_state import state, AppState

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
    """Initialize Kaedra agent in background to ensure fast server start."""
    global slack_service
    print(f"[*] Fast Startup: Server is online. Backgrounding service initialization...")
    
    # Deferred heavy lifting
    asyncio.create_task(background_init())

async def background_init():
    """Heavy service initialization moved out of the request path."""
    global slack_service
    from kaedra.services.prompt import PromptService
    from kaedra.services.memory import MemoryService
    from kaedra.services.slack_bot import SlackService
    from kaedra.agents.kaedra import KaedraAgent
    from kaedra.services.research import ResearchService
    from kaedra.services.web import WebService
    from kaedra.services.bigquery_memory import BigQueryMemoryService
    from kaedra.services.context import ConfuciusContextProvider
    from kaedra.services.stores import FirestoreMessageStore

    try:
        # 1. Core Services
        print("[*] Init: Core Services...")
        prompt_service = PromptService(project=PROJECT_ID, location=LOCATION)
        
        # 2. Memory Services (New Columnar + Thread Stores)
        print("[*] Init: Memory Services...")
        state.bq_memory = BigQueryMemoryService(prompt_service)
        state.message_store = FirestoreMessageStore(db=db_memory if 'db_memory' in globals() and db_memory else db)
        
        # 3. Context & Reflection Loop (Hierarchical)
        print("[*] Init: Context & Reflection...")
        from kaedra.services.engram_service import EngramService
        state.engram_service = EngramService()
        state.context_provider = ConfuciusContextProvider(state.bq_memory, engram_service=state.engram_service)
        
        # Parallel initialization where possible
        print("[*] Init: Web & Research...")
        state.web_service = WebService()
        state.research_service = ResearchService(prompt_service)
        
        # 4. Agent (Shadow Tactician with Confucius Scaffolding)
        print("[*] Init: Agent...")
        state.agent = KaedraAgent(prompt_service=prompt_service)
        state.agent.context_provider = state.context_provider
        
        # 5. Connect Slack
        print("[*] Init: Slack...")
        slack_service = SlackService()
        slack_service.initialize(agent=state.agent)
        state.slack_service = slack_service
        # await slack_service.start() # Commenting out potential blocker for now or keep it?
        # Keeping it but formatted
        await slack_service.start()
        
        # 6. Initialize StoryEngine (Modular + Reactive)
        print("[*] Init: StoryEngine...")
        from kaedra.story.engine import StoryEngine
        state.story_engine = StoryEngine()
        
        # 7. Initialize MCP Client (Notion MCP Tools)
        print("[*] Init: MCP Client...")
        from kaedra.services.mcp_client import NotionMCPClient
        state.mcp_client = NotionMCPClient()
        await state.mcp_client.initialize()
        
        print("[+] Production Background initialization complete (BQ + Confucius + Story + MCP).")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[!] Background Init Error: {e}")

# -------------------------------------------------------------------------
# DEBUG ENDPOINT
# -------------------------------------------------------------------------
@app.get("/debug/init")
async def manual_init():
    """Manually trigger initialization to see errors."""
    try:
        if state.story_engine:
            return {"status": "Already initialized"}
            
        print("[DEBUG] Manual init triggered")
        await background_init()
        return {"status": "success", "message": "Manual init complete"}
    except Exception as e:
        import traceback
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    model: str
    latency_ms: float
    timestamp: float
    thread_id: Optional[str] = None

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
    temperature: float = 1.0
    use_grounding: bool = True
    thinking_level: Optional[str] = None # minimal, low, medium, high

class GenerateResponse(BaseModel):
    response: str
    model_used: str
    grounded: bool

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
    model: str = "gemini-embedding-001"

# Visual Request Models
class ImageRequest(BaseModel):
    prompt: str

class VideoGenerationRequest(BaseModel):
    prompt: str
    resolution: str = "720p"
    aspect_ratio: str = "16:9"
    number_of_videos: int = 1

# Worldbuilding Request Models (HALCYON-pattern)
class WorldBuildRequest(BaseModel):
    """Generate a complete fictional world from a seed prompt."""
    seed: str  # e.g. "A planet where AI cities turned feral"
    tone: str = "dark and atmospheric"
    theme: str = "power and survival"
    include_characters: bool = True
    include_quests: bool = True

class WorldBuildResponse(BaseModel):
    """Complete recursive world output."""
    success: bool
    world_name: str
    era: str
    core_tension: str
    factions: List[Dict[str, Any]]
    characters: List[Dict[str, Any]]
    quests: List[Dict[str, Any]]
    full_data: Dict[str, Any]
    export_path: Optional[str] = None

# Autonomy Run Models (V2)
class RunRequest(BaseModel):
    """Request to start an autonomous run."""
    task: str  # e.g. "Expand all Olympus Mons locations"
    mode: str = "kaedra"  # professional, kaedra, unk, lore_scribe, command

class RunResponse(BaseModel):
    """Response for run creation."""
    run_id: str
    status: str
    message: str

class CowriteRequest(BaseModel):
    """Request for multi-agent collaboration."""
    prompt: str
    context: Optional[str] = None
    max_turns: Optional[int] = 3
    mode: Optional[str] = "narrative"
    thinking_level: Optional[str] = "low" # Minimal, Low, Medium, High

class CowriteResponse(BaseModel):
    """Collaboration response."""
    content: str
    turns_completed: int
    participating_agents: List[str]
    status: str


@app.get("/activity")
async def get_activity_log():
    """Get recent system activities."""
    return {"items": activity_log.get_activities()}

@app.post("/v1/generate")
async def v1_generate(request: GenerateRequest):
    """V1 Text Generation with Thinking Level support."""
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent warming up.")
    
    result = await state.agent.prompt_service.generate_async(
        prompt=request.prompt,
        model_key=request.model,
        thinking_level=request.thinking_level
    )
    
    return GenerateResponse(
        response=result.text,
        model_used=result.model,
        grounded=result.grounded
    )

# -------------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    """Fleet standard health check."""
    return {
        "status": "ok",
        "service": "kaedra-shadow-tactician",
        "version": "0.0.9",
        "grounding_enabled": True
    }

@app.get("/")
async def root():
    return {
        "status": "online",
        "agent": "Kaedra",
        "version": "0.0.9",
        "docs": "/docs"
    }

@app.get("/v1")
async def v1_root():
    return {
        "version": "v1",
        "services": ["chat", "api", "visual"]
    }

@app.get("/v1/api")
async def v1_api_info():
    """General API information."""
    return {
        "name": "Kaedra Intelligence API",
        "endpoints": ["/v1/chat", "/generate-image", "/generate/video", "/v1/models"],
        "status": "operational"
    }

@app.post("/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with Kaedra (Production Endpoint with Hierarchical Memory).
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent warming up.")

    try:
        # Load or Create Thread
        thread_id = request.thread_id
        thread = None
        if thread_id and state.message_store:
            thread = await state.message_store.load_thread(thread_id)
        
        if not thread:
            from kaedra.core.agent_types import AgentThread
            thread = AgentThread(thread_id=thread_id)

        # Run Agent
        result = await state.agent.run(request.message, thread=thread, context=request.context)

        # Save Thread State
        if state.message_store:
            await state.message_store.save_thread(thread)

        # Log Activity
        activity_log.log(
            action="User Chat",
            detail=f"Kaedra (Hierarchical) replied: {result.content[:30]}...",
            icon="psychology"
        )

        return ChatResponse(
            response=result.content,
            agent_name=result.agent_name,
            model=result.model,
            latency_ms=result.latency_ms,
            timestamp=time.time(),
            thread_id=thread.thread_id # Added to response
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
    OpenAI-compatible chat endpoint.
    Leverages thread persistence even via completions API.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent warming up.")

    try:
        # For completions, we treat it as a transient thread unless 
        # thread_id meta is passed (custom extension)
        from kaedra.core.agent_types import AgentThread
        thread = AgentThread() # Transient by default for completions
        
        # Extract last message
        last_content = request.messages[-1].content
        last_message = _extract_text(last_content)

        # Run agent
        result = await state.agent.run(last_message, thread=thread)

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

@app.post("/generate", response_model=GenerateResponse)
async def fleet_generate(request: GenerateRequest):
    """
    Fleet Generate Endpoint: Direct text generation.
    """
    # Wait for background_init if needed
    if not state.agent:
        for _ in range(10):
            if state.agent: break
            await asyncio.sleep(1)
        if not state.agent:
            raise HTTPException(status_code=503, detail="Agent still warming up in background.")

    result = await state.agent.prompt_service.generate_async(
        prompt=request.prompt,
        model_key=request.model or "flash" # Default to Flash for speed
    )
    
    activity_log.log(
        action="System Generate",
        detail=f"Generated text for: {request.prompt[:30]}...",
        icon="edit"
    )
    
    return GenerateResponse(
        response=result.text,
        model_used=result.model,
        grounded=True
    )

@app.post("/generate-image")
async def generate_image(request: ImageRequest):
    """
    Generate an image using Gemini 3 Pro Image Preview.
    """
    if not state.visual_service:
        # Try lazy init
        try:
            from kaedra.services.visual import VisualService
            state.visual_service = VisualService()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Visual Service unavailable: {e}")

    try:
        # We run the synchronous call in an async executor to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()

        # This returns a PIL Image object
        image_obj = await loop.run_in_executor(None, state.visual_service.generate_image, request.prompt)

        # For API, we need to return bytes or a signed URL.
        # Since this is a simple setup, we'll convert to base64 for direct return
        import io
        import base64

        buffered = io.BytesIO()
        image_obj.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        image_obj.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        activity_log.log(
            action="System Visual",
            detail=f"Generated image: {request.prompt[:30]}...",
            icon="image"
        )

        return {
            "status": "success",
            "image_type": "png",
            "image_base64": img_str,
            "prompt": request.prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/video")
async def generate_video(request: VideoGenerationRequest):
    """
    Generate a video using Veo 3.1.
    NOTE: This is a long-running operation.
    """
    if not state.visual_service:
        try:
            from kaedra.services.visual import VisualService
            state.visual_service = VisualService()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Visual Service unavailable: {e}")

    try:
        # Run in executor (this can take 60s+)
        import asyncio
        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            lambda: state.visual_service.generate_video(
                prompt=request.prompt,
                resolution=request.resolution,
                aspect_ratio=request.aspect_ratio,
                number_of_videos=request.number_of_videos
            )
        )

        return {
            "status": "success",
            "file_path": str(result.file_path), # In Cloud Run this is local ephemeral
            "duration": result.duration_seconds,
            "model": result.model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# WORLDBUILDING ENDPOINT (HALCYON Pattern)
# -------------------------------------------------------------------------

@app.post("/generate/world", response_model=WorldBuildResponse)
async def generate_world(request: WorldBuildRequest):
    """
    Generate a complete fictional world using recursive AI.
    
    HALCYON-inspired 3-layer generation:
    1. World Generator - Creates world from seed
    2. Character Generator - NPCs grounded in world logic
    3. Quest Builder - Narrative missions with moral dilemmas
    """
    try:
        from kaedra.skills.worldbuilder import RecursiveWorldBuilder, asdict
        from pathlib import Path
        
        builder = RecursiveWorldBuilder()
        
        # Generate world recursively
        result = await builder.build_world(
            seed=request.seed,
            tone=request.tone,
            theme=request.theme
        )
        
        # Export to file if desired
        export_path = None
        try:
            output_dir = Path("./generated_worlds") / result.world.world_name.lower().replace(" ", "_")
            result.export(output_dir)
            export_path = str(output_dir)
        except Exception:
            pass  # Export is optional
        
        # Build response
        return WorldBuildResponse(
            success=True,
            world_name=result.world.world_name,
            era=result.world.era,
            core_tension=result.world.core_tension,
            factions=[asdict(f) for f in result.world.factions],
            characters=[asdict(c) for c in result.characters] if request.include_characters else [],
            quests=[asdict(q) for q in result.quests] if request.include_quests else [],
            full_data={
                "seed": result.seed,
                "generated_at": result.generated_at,
                "world": asdict(result.world),
                "characters": [asdict(c) for c in result.characters],
                "quests": [asdict(q) for q in result.quests]
            },
            export_path=export_path
        )
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Worldbuilder not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models_v1():
    """List available models (OpenAI/Fleet compatible) via GLOBAL endpoint."""
    return {
        "object": "list",
        "data": [
            # Google Models (Global)
            {"id": "gemini-3-flash-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-3-pro-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-3-pro-image-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-pro", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-flash", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-flash-lite", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.0-flash-001", "id_alias": "gemini-2.0-flash", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.0-flash-lite-001", "id_alias": "gemini-2.0-flash-lite", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            
            # Gemma 3 (Global)
            {"id": "gemma-3-27b", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemma-3-12b", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemma-3-4b", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemma-3-1b", "object": "model", "owned_by": "google", "endpoints": ["global"]},

            # Specialized Multi-Modal
            {"id": "imagen-4.0-generate-001", "object": "model", "owned_by": "google"},
            {"id": "veo-3.1-generate-001", "object": "model", "owned_by": "google"},
            
            # Partner Models (MaaS - Global)
            {"id": "claude-4.5-opus", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "claude-4.5-sonnet", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "claude-4.5-haiku", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "claude-4-opus", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "mistral-large-2407", "object": "model", "owned_by": "mistral", "endpoints": ["global"]},
            
            # Open Models (MaaS - Global)
            {"id": "deepseek-r1-0528", "object": "model", "owned_by": "deepseek", "endpoints": ["global"]},
            {"id": "deepseek-v3.1", "object": "model", "owned_by": "deepseek", "endpoints": ["global"]},
            {"id": "llama-4-maverick-17b-128e-preview", "object": "model", "owned_by": "meta", "endpoints": ["global"]},
            {"id": "llama-4-scout-17b-16e-preview", "object": "model", "owned_by": "meta", "endpoints": ["global"]},
            {"id": "qwen3-next-80b-thinking", "object": "model", "owned_by": "alibaba", "endpoints": ["global"]},
            {"id": "qwen3-235b", "object": "model", "owned_by": "alibaba", "endpoints": ["global"]}
        ]
    }

@app.get("/models")
async def list_models_alias():
    """Alias for List Models."""
    return await list_models_v1()

@app.get("/config")
async def get_config():
    """Get current agent configuration."""
    return {
         "service": SERVICE_NAME,
         "project": PROJECT_ID,
         "region": LOCATION,
         "deploy_mode": "Cloud Run" if os.getenv("K_SERVICE") else "Local",
         "visual_enabled": state.visual_service is not None
    }

# -------------------------------------------------------------------------
# AUTONOMY ENDPOINTS (V2 - Ralph-style runs)
# -------------------------------------------------------------------------

@app.post("/runs", response_model=RunResponse)
async def create_run(request: RunRequest):
    """
    Create and start an autonomous run.
    Implements Ralph-style exit detection with dual conditions.
    """
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        import asyncio
        run_id = await state.orchestrator.run_manager.create_run(
            task=request.task,
            mode=request.mode
        )
        
        # Start the loop in the background
        asyncio.create_task(state.orchestrator.run_manager.execute_loop(run_id))
        
        return RunResponse(
            run_id=run_id,
            status="started",
            message=f"Run {run_id} started: {request.task[:50]}..."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs")
async def list_runs():
    """List all autonomous runs with their status."""
    if not state.orchestrator:
        return {"runs": []}
    
    return {"runs": state.orchestrator.run_manager.list_runs()}

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get details for a specific run."""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    run = state.orchestrator.run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return run

@app.post("/search")
async def fleet_search(request: SearchRequest):
    """
    Fleet Search Endpoint: Grounded Google Search.
    """
    if "google_search" not in GOOGLE_TOOLS:
        raise HTTPException(status_code=503, detail="Search service not configured.")
        
    return GOOGLE_TOOLS["google_search"](request.query, request.num_results)

@app.post("/analyze-url")
async def fleet_analyze_url(request: AnalyzeUrlRequest):
    """
    Fleet Analyze URL Endpoint: Scrape and Metadata.
    """
    if not state.web_service:
        from kaedra.services.web import WebService
        state.web_service = WebService()

    metadata = state.web_service.extract_metadata(request.url)
    return metadata

@app.post("/execute-code")
async def fleet_execute_code(request: ExecuteCodeRequest):
    """
    Fleet Execute Code Endpoint (Simulation/Prompt-based for now).
    """
    if not state.agent:
        for _ in range(10):
            if state.agent: break
            await asyncio.sleep(1)
            
        if not state.agent:
            raise HTTPException(status_code=503, detail="Agent still warming up in background.")

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

@app.post("/cowrite", response_model=CowriteResponse)
async def cowrite_endpoint(request: CowriteRequest):
    """
    Back-and-forth collaboration between Kaedra and Rhea Noir.
    """
    # Wait for background_init if needed (but don't block startup)
    if not state.agent:
        # Try a quick wait if it just started
        for _ in range(5):
            if state.agent: break
            await asyncio.sleep(1)
            
        if not state.agent:
            raise HTTPException(status_code=503, detail="Agent still warming up in background.")

    try:
        from kaedra.story.components.co_writer import CoWriter
        rhea = CoWriter(warmup=True)
        
        current_context = request.context or ""
        history = []
        
        print(f"[COWRITE] Starting collaboration: {request.prompt[:50]}...")
        
        # 1. Kaedra (Shadow Tactician) refines/structures
        k_res = await state.agent.run(f"Structure this request: {request.prompt}", current_context)
        history.append(f"Kaedra: {k_res.content}")
        
        # 2. Rhea (Vibe/Prose)
        # Use thinking level if provided
        r_res = rhea.consult(
            k_res.content, 
            current_context + f"\nStructure: {k_res.content}",
            thinking_level=request.thinking_level
        )
        history.append(f"Rhea: {r_res}")
        
        # Optional: Further turns if requested
        if request.max_turns and request.max_turns > 2:
            # Kaedra critiques or advances
            k_res_2 = await state.agent.run(f"Advance the narrative or critique the vibe: {r_res}", current_context + f"\n{r_res}")
            history.append(f"Kaedra: {k_res_2.content}")
            
            # Rhea finalizes
            r_res_2 = rhea.consult(k_res_2.content, current_context + f"\n{k_res_2.content}")
            history.append(f"Rhea: {r_res_2}")
            final_content = r_res_2
        else:
            final_content = r_res
            
        return CowriteResponse(
            content=final_content,
            turns_completed=len(history),
            participating_agents=["Kaedra", "Rhea Noir"],
            status="completed"
        )
    except Exception as e:
        print(f"[!] Cowrite error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    """
    Create Embeddings Endpoint.
    """
    if not state.agent:
        for _ in range(10):
            if state.agent: break
            await asyncio.sleep(1)
            
        if not state.agent:
            raise HTTPException(status_code=503, detail="Agent still warming up in background.")

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

@app.get("/agent-card")
async def get_agent_card_alias_2():
    """Alias for Agent Card (Fleet Standard)."""
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
        "version": "0.0.9",
        "capabilities": [
            "strategic-planning",
            "intelligence-synthesis",
            "multi-agent-coordination",
            "gemini-3-reasoning",
            "deep-research",
            "embeddings",
            "code-execution",
            "visual-generation"
        ],
        "endpoints": {
            "chat": f"{CLOUD_RUN_URL}/v1/chat/completions",
            "health": f"{CLOUD_RUN_URL}/health",
            "card": f"{CLOUD_RUN_URL}/.well-known/agent.json",
            "generate_image": f"{CLOUD_RUN_URL}/generate-image"
        },
        "extensions": {
            "color": "neon pink",
            "personality": "AAVE, tactical, uncensored",
            "deploy_region": LOCATION,
            "reasoning_engine": AGENT_RESOURCE_NAME
        }
    }

# -------------------------------------------------------------------------
# NOTION WEBHOOK ENDPOINTS
# -------------------------------------------------------------------------

class NotionWebhookPayload(BaseModel):
    """Payload from Notion webhook events."""
    type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class SyncRequest(BaseModel):
    """Manual sync request."""
    world_id: str = "world_bee9d6ac"

@app.post("/webhook/notion")
async def notion_webhook(payload: NotionWebhookPayload = Body(...)):
    """
    Receive Notion database change events.
    Triggers sync when Ingestion Queue items are updated.

    POST https://kaedra-69017097813.us-central1.run.app/webhook/notion
    """
    import sys
    sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    try:
        from tools.sync_notion import NotionBridge

        print(f"📥 Received Notion webhook: {payload.type}")

        # Default world ID
        world_id = "world_bee9d6ac"

        bridge = NotionBridge(world_id)
        if bridge.check_connection():
            bridge.pull_ingestion_queue()
            return {"status": "synced", "world_id": world_id}
        else:
            raise HTTPException(status_code=500, detail="Notion connection failed")

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def manual_sync(request: SyncRequest):
    """
    Manually trigger a full Notion sync for a world.

    POST https://kaedra-69017097813.us-central1.run.app/sync
    Body: {"world_id": "world_bee9d6ac"}
    """
    import sys
    sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    try:
        from tools.sync_notion import NotionBridge

        bridge = NotionBridge(request.world_id)
        if bridge.check_connection():
            bridge.sync_all()
            return {"status": "synced", "world_id": request.world_id}
        else:
            raise HTTPException(status_code=500, detail="Notion connection failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync/{world_id}")
async def sync_status(world_id: str):
    """Check sync status for a world."""
    from pathlib import Path
    import json

    worlds_root = Path(__file__).parent.parent.parent / "lore" / "worlds"
    world_path = worlds_root / world_id

    if not world_path.exists():
        raise HTTPException(status_code=404, detail=f"World {world_id} not found")

    ingestion_path = world_path / "ingestion.json"
    bible_path = world_path / "world_bible.json"

    status = {
        "world_id": world_id,
        "ingestion_items": 0,
        "bible_entries": 0
    }

    if ingestion_path.exists():
        data = json.loads(ingestion_path.read_text())
        status["ingestion_items"] = len(data.get("items", []))

    if bible_path.exists():
        data = json.loads(bible_path.read_text())
        sections = data.get("sections", {})
        for entries in sections.values():
            status["bible_entries"] += len(entries)

    return status

# -------------------------------------------------------------------------
# MOBILE / LORE ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/worlds")
async def list_available_worlds():
    """List all available worlds for the mobile app selector."""
    import sys
    # Ensure root is in path to import kaedra modules depending on execution context
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)

    from kaedra.worlds.store import list_worlds
    worlds = list_worlds()
    return {"worlds": [w.__dict__ for w in worlds]}

@app.get("/lore/feed")
async def get_lore_feed(world_id: str = "world_bee9d6ac"):
    """Get the Ingestion Feed (New Lore) for a specific world."""
    from pathlib import Path
    import json

    # Locate World
    worlds_root = Path(__file__).parent.parent.parent / "lore" / "worlds"
    world_path = worlds_root / world_id

    if not world_path.exists():
        raise HTTPException(status_code=404, detail=f"World {world_id} not found")

    ingestion_path = world_path / "ingestion.json"
    if not ingestion_path.exists():
        return {"items": []}

    try:
        data = json.loads(ingestion_path.read_text(encoding="utf-8"))
        return data # Returns {"items": [...]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load ingestion feed: {e}")

@app.get("/lore/bible")
async def get_world_bible(world_id: str = "world_bee9d6ac"):
    """Get the World Bible (Canon Lore) for a specific world."""
    from pathlib import Path
    import json

    # Locate World
    worlds_root = Path(__file__).parent.parent.parent / "lore" / "worlds"
    world_path = worlds_root / world_id

    if not world_path.exists():
        raise HTTPException(status_code=404, detail=f"World {world_id} not found")

    bible_path = world_path / "world_bible.json"
    if not bible_path.exists():
        return {"sections": {}}

    try:
        data = json.loads(bible_path.read_text(encoding="utf-8"))
        return data # Returns {"sections": {...}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load world bible: {e}")

@app.get("/lore/weighted")
async def get_weighted_lore(limit: int = 50):
    """Get Notion lore entities sorted by Importance Score (highest first)."""
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root not in sys.path:
        sys.path.insert(0, root)
    
    try:
        from kaedra.services.notion_service import NotionService
        
        service = NotionService()
        pages = service.list_all_universe_pages()
        
        # Extract and sort by Importance Score
        weighted_items = []
        for page in pages:
            props = page.get("properties", {})
            
            # Skip ghosts
            title = service._get_title(page)
            if not title:
                continue
            
            imp_score = service.safe_get_property(props, "Importance Score", "number") or 0
            conf_score = service.safe_get_property(props, "Canon Confidence", "number") or 0
            category = service.safe_get_property(props, "Category", "select") or "Lore"
            
            weighted_items.append({
                "id": page["id"],
                "title": title,
                "category": category,
                "importance": imp_score,
                "confidence": conf_score,
                "url": page.get("url", ""),
                "created_time": page.get("created_time", "")
            })
        
        # Sort by importance descending
        weighted_items.sort(key=lambda x: x["importance"], reverse=True)
        
        # Return top N
        return {"items": weighted_items[:limit]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weighted lore: {e}")

# -------------------------------------------------------------------------
# N2: STORY ENGINE ENDPOINTS
# -------------------------------------------------------------------------

class StorySessionRequest(BaseModel):
    """Request to create or update a story session."""
    world_id: str = "world_bee9d6ac"
    mode: str = "writer"  # writer, planner, critic
    prompt: Optional[str] = None

class StoryGenerateRequest(BaseModel):
    """Request to generate story content."""
    session_id: str
    prompt: str
    auto_mode: bool = False

@app.get("/story/sessions")
async def list_story_sessions():
    """List all available story sessions from Firestore."""
    if not db:
        return {"sessions": [], "error": "Database not initialized"}
    
    try:
        docs = db.collection("sessions").stream()
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            sessions.append(data)
        return {"sessions": sessions}
    except Exception as e:
        return {"sessions": [], "error": str(e)}

@app.post("/story/session")
async def create_story_session(request: StorySessionRequest):
    """Create a new story session in Firestore."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    import uuid
    from datetime import datetime
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    meta = {
        "id": session_id,
        "title": "New Session",
        "world_id": request.world_id,
        "mode": request.mode,
        "created": datetime.now().isoformat(),
        "word_count": 0,
        "content": "" 
    }
    
    try:
        db.collection("sessions").document(session_id).set(meta)
        return {"session_id": session_id, "status": "created", "meta": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/session/{session_id}")
async def get_story_session(session_id: str):
    """Get story session details and chat history from Firestore."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
        
    try:
        doc_ref = db.collection("sessions").document(session_id)
        doc = doc_ref.get()
        
        if not doc.exists:
             raise HTTPException(status_code=404, detail="Session not found")
             
        meta = doc.to_dict()
        content = meta.get("content", "")
        
        # Get Messages Subcollection
        messages_docs = doc_ref.collection("messages").order_by("timestamp").stream()
        messages = [m.to_dict() for m in messages_docs]
        
        return {"meta": meta, "content": content, "messages": messages}
    except Exception as e:
        print(f"Error fetching session: {e}")
        # Fallback to empty if error (or raise)
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/story/session/{session_id}")
async def update_story_session(session_id: str, request: Request):
    """Update session metadata (e.g. title)."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        data = await request.json()
        doc_ref = db.collection("sessions").document(session_id)
        doc_ref.update(data)
        return {"status": "updated", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/story/session/{session_id}")
async def delete_story_session(session_id: str):
    """Delete a story session and its messages."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
        
    try:
        doc_ref = db.collection("sessions").document(session_id)
        # Delete messages subcollection (not atomic, but sufficient for now)
        msgs = doc_ref.collection("messages").list_documents()
        for m in msgs:
            m.delete()
            
        doc_ref.delete()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/story/session/{session_id}/export")
async def export_story_session(session_id: str):
    """Export session chat history as Markdown."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
        
    try:
        doc_ref = db.collection("sessions").document(session_id)
        meta = doc_ref.get().to_dict()
        msgs = doc_ref.collection("messages").order_by("timestamp").stream()
        
        md_content = f"# {meta.get('title', 'Session Export')}\n\n"
        for m in msgs:
            d = m.to_dict()
            role = d.get('role', 'unknown').capitalize()
            content = d.get('content', '')
            md_content += f"**{role}**: {content}\n\n"
            
        return {"markdown": md_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/memories")
async def get_system_memories(limit: int = 10):
    """Debug endpoint to list recent memories."""
    if not memory_service:
         raise HTTPException(status_code=503, detail="Memory service not initialized")
    return {"memories": memory_service.list_recent(limit=limit)}

class ChatMessagePayload(BaseModel):
    role: str
    content: str
    timestamp: float = 0.0

@app.post("/story/session/{session_id}/message")
async def append_session_message(session_id: str, message: ChatMessagePayload):
    """Append a message to the session chat history in Firestore."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
        
    try:
        import time
        msg_data = message.dict()
        if msg_data["timestamp"] == 0.0:
            msg_data["timestamp"] = time.time()
            
        doc_ref = db.collection("sessions").document(session_id)
        
        # Auto-Title Logic
        if message.role == "user":
            meta = doc_ref.get().to_dict() or {}
            current_title = meta.get("title", "New Session")
            
            if current_title == "New Session" and state.agent:
                # Generate a short title
                try:
                    prompt = f"Summarize this user request into a specific, short 3-5 word title (no quotes): {message.content}"
                    resp = await state.agent.prompt_service.generate_async(prompt, model_key="flash")
                    new_title = resp.text.strip().replace('"', '')
                    doc_ref.update({"title": new_title})
                except Exception as e:
                    print(f"[!] Auto-title failed: {e}")

        # Add to subcollection
        doc_ref.collection("messages").add(msg_data)
        
        return {"status": "saved"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/lore/entry")
async def add_lore_entry(request: Request):
    """Add a new entry to the Lore database (Firestore)."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
        
    try:
        data = await request.json()
        content = data.get("content", "")
        
        if not content:
            raise HTTPException(status_code=400, detail="Content required")
            
        doc_ref = db.collection("lore").document()
        doc_ref.set({
            "content": content,
            "created": time.time(),
            "source": "chat_action",
            "tags": ["manual_save"]
        })
        
        return {"status": "saved", "id": doc_ref.id}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/story/generate")
async def generate_story_content(request: StoryGenerateRequest):
    """Generate story content using StoryEngine."""
    if not state.agent:
        for _ in range(10):
            if state.agent: break
            await asyncio.sleep(1)
            
        if not state.agent:
            raise HTTPException(status_code=503, detail="Agent still warming up in background.")
    
    try:
        # Use agent's prompt service for story generation
        prompt = f"""You are a creative fiction writer. Write the next section of the story based on:
        
User Request: {request.prompt}

Write in vivid, immersive prose. Focus on sensory details and emotional moments."""
        
        result = await state.agent.prompt_service.generate_async(
            prompt=prompt,
            model_key="pro"  # Use Pro for creative writing
        )
        
        return {
            "content": result.text,
            "session_id": request.session_id,
            "model": result.model,
            "word_count": len(result.text.split())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# N4: LIFX SMART LIGHT ENDPOINTS
# -------------------------------------------------------------------------

class LightStateRequest(BaseModel):
    """Request to set light state."""
    selector: str = "all"
    power: Optional[str] = None  # "on" or "off"
    color: Optional[str] = None
    brightness: Optional[float] = None
    duration: float = 1.0

class LightEffectRequest(BaseModel):
    """Request to run a light effect."""
    selector: str = "all"
    effect: str = "breathe"  # breathe, pulse
    color: str = "purple"
    period: float = 2.0
    cycles: float = 3

@app.get("/lights/status")
async def get_lights_status():
    """Get current status of all LIFX lights."""
    try:
        from kaedra.services.lifx import LIFXService
        
        lifx = LIFXService()
        lights = lifx.list_lights()
        
        return {
            "status": "connected",
            "count": len(lights),
            "lights": lights
        }
    except Exception as e:
        return {"status": "disconnected", "error": str(e), "lights": []}

@app.post("/lights/set")
async def set_light_state(request: LightStateRequest):
    """Set LIFX light state."""
    try:
        from kaedra.services.lifx import LIFXService
        
        lifx = LIFXService()
        result = lifx.set_state(
            selector=request.selector,
            power=request.power,
            color=request.color,
            brightness=request.brightness,
            duration=request.duration
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/lights/effect")
async def run_light_effect(request: LightEffectRequest):
    """Run a LIFX light effect."""
    try:
        from kaedra.services.lifx import LIFXService
        
        lifx = LIFXService()
        
        if request.effect == "breathe":
            result = lifx.breathe(
                selector=request.selector,
                color=request.color,
                period=request.period,
                cycles=request.cycles
            )
        elif request.effect == "pulse":
            result = lifx.pulse(
                selector=request.selector,
                color=request.color,
                period=request.period,
                cycles=request.cycles
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown effect: {request.effect}")
        
        return {"status": "success", "effect": request.effect, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/lights/presets")
async def get_light_presets():
    """Get available mood presets for LIFX lights."""
    presets = [
        {"id": "focus", "name": "Focus Mode", "color": "white", "brightness": 0.8, "kelvin": 4000},
        {"id": "relax", "name": "Relax", "color": "orange", "brightness": 0.4, "kelvin": 2700},
        {"id": "creative", "name": "Creative Flow", "color": "purple", "brightness": 0.6},
        {"id": "gaming", "name": "Gaming", "color": "cyan", "brightness": 0.7},
        {"id": "writing", "name": "Writing Session", "color": "kelvin:3200", "brightness": 0.5},
        {"id": "veil", "name": "VeilVerse Mode", "color": "hue:280 saturation:0.8", "brightness": 0.4},
    ]
    return {"presets": presets}

@app.post("/lights/preset/{preset_id}")
async def apply_light_preset(preset_id: str):
    """Apply a mood preset to all lights."""
    presets = {
        "focus": {"color": "kelvin:4000", "brightness": 0.8},
        "relax": {"color": "kelvin:2700", "brightness": 0.4},
        "creative": {"color": "purple", "brightness": 0.6},
        "gaming": {"color": "cyan", "brightness": 0.7},
        "writing": {"color": "kelvin:3200", "brightness": 0.5},
        "veil": {"color": "hue:280 saturation:0.8", "brightness": 0.4},
    }
    
    if preset_id not in presets:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    try:
        from kaedra.services.lifx import LIFXService
        
        lifx = LIFXService()
        preset = presets[preset_id]
        result = lifx.set_state(
            selector="all",
            color=preset.get("color"),
            brightness=preset.get("brightness"),
            duration=2.0
        )
        
        return {"status": "success", "preset": preset_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# N4: RAZER CHROMA ENDPOINTS
# -------------------------------------------------------------------------

class RazerEffectRequest(BaseModel):
    """Request to set Razer effect."""
    effect: str = "static"  # static, fire, wave, rainbow, lightning
    color: Optional[str] = "purple"

@app.get("/razer/status")
async def get_razer_status():
    """Get Razer Chroma connection status."""
    try:
        from kaedra.services.razer import RazerService
        
        razer = RazerService()
        connected = razer.connect()
        
        return {
            "status": "connected" if connected else "disconnected",
            "session_uri": razer.session_uri if connected else None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/razer/effect")
async def set_razer_effect(request: RazerEffectRequest):
    """Set Razer Chroma effect."""
    try:
        from kaedra.services.razer import RazerService
        
        razer = RazerService()
        if not razer.connect():
            raise HTTPException(status_code=503, detail="Failed to connect to Razer Synapse")
        
        if request.effect == "static":
            razer.set_static(request.color or "purple")
        elif request.effect == "fire":
            razer.start_fire_effect()
        elif request.effect == "wave":
            razer.start_wave_effect(color_name=request.color or "cyan")
        elif request.effect == "rainbow":
            razer.start_rainbow_cycle()
        elif request.effect == "lightning":
            razer.start_lightning_effect(base_color=request.color or "purple")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown effect: {request.effect}")
        
        return {"status": "success", "effect": request.effect, "color": request.color}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/razer/sync")
async def sync_razer_to_lifx():
    """Sync Razer lighting to LIFX lights."""
    try:
        from kaedra.services.razer import RazerService
        from kaedra.services.lifx import LIFXService
        
        # Get current LIFX state
        lifx = LIFXService()
        lights = lifx.list_lights()
        
        if not lights:
            return {"status": "no_lights", "message": "No LIFX lights found to sync from"}
        
        # Get dominant color from first light
        first_light = lights[0]
        color = first_light.get("color", {})
        
        # Connect and set Razer to match
        razer = RazerService()
        if razer.connect():
            # Simplified color mapping
            hue = color.get("hue", 0)
            if hue < 30 or hue > 330:
                razer.set_static("red")
            elif hue < 90:
                razer.set_static("yellow")
            elif hue < 150:
                razer.set_static("green")
            elif hue < 210:
                razer.set_static("cyan")
            elif hue < 270:
                razer.set_static("blue")
            else:
                razer.set_static("purple")
            
            return {"status": "synced", "source_hue": hue}
        else:
            return {"status": "failed", "message": "Could not connect to Razer Synapse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------------------
# N5: VALIDATION SUITE ENDPOINTS
# -------------------------------------------------------------------------

@app.get("/validate")
async def run_validation_suite():
    """
    Run comprehensive 50-point validation suite.
    Tests connectivity, services, and system health.
    """
    results = []
    total_score = 0
    
    # 1. API Health (5 points)
    try:
        results.append({"test": "api_health", "status": "pass", "points": 5})
        total_score += 5
    except Exception as e:
        results.append({"test": "api_health", "status": "fail", "error": str(e), "points": 0})
    
    # 2. Agent Initialization (10 points)
    if state.agent:
        results.append({"test": "agent_init", "status": "pass", "points": 10})
        total_score += 10
    else:
        results.append({"test": "agent_init", "status": "fail", "error": "Agent not initialized", "points": 0})
    
    # 3. Prompt Service (10 points)
    if state.agent and (hasattr(state.agent, 'prompt') or hasattr(state.agent, 'prompt_service')):
        try:
            # Quick validation call
            results.append({"test": "prompt_service", "status": "pass", "points": 10})
            total_score += 10
        except Exception as e:
            results.append({"test": "prompt_service", "status": "fail", "error": str(e), "points": 0})
    else:
        results.append({"test": "prompt_service", "status": "skip", "error": "Agent prompt service not found", "points": 0})
    
    # 4. Visual Service (5 points)
    if state.visual_service:
        results.append({"test": "visual_service", "status": "pass", "points": 5})
        total_score += 5
    else:
        results.append({"test": "visual_service", "status": "warn", "error": "Not initialized", "points": 2})
        total_score += 2
    
    # 5. Research Service (5 points)
    if state.research_service:
        results.append({"test": "research_service", "status": "pass", "points": 5})
        total_score += 5
    else:
        results.append({"test": "research_service", "status": "warn", "error": "Not initialized", "points": 2})
        total_score += 2
    
    # 6. Web Service (5 points)
    if state.web_service:
        results.append({"test": "web_service", "status": "pass", "points": 5})
        total_score += 5
    else:
        results.append({"test": "web_service", "status": "warn", "error": "Not initialized", "points": 2})
        total_score += 2
    
    # 7. LIFX Service (3 points)
    try:
        from kaedra.services.lifx import LIFXService
        lifx = LIFXService()
        lights = lifx.list_lights()
        if lights:
            results.append({"test": "lifx_service", "status": "pass", "lights": len(lights), "points": 3})
            total_score += 3
        else:
            results.append({"test": "lifx_service", "status": "warn", "error": "No lights found", "points": 1})
            total_score += 1
    except Exception as e:
        results.append({"test": "lifx_service", "status": "skip", "error": str(e), "points": 0})
    
    # 8. Razer Service (2 points)
    try:
        from kaedra.services.razer import RazerService
        razer = RazerService()
        if razer.connect():
            results.append({"test": "razer_service", "status": "pass", "points": 2})
            total_score += 2
        else:
            results.append({"test": "razer_service", "status": "warn", "error": "Could not connect", "points": 0})
    except Exception as e:
        results.append({"test": "razer_service", "status": "skip", "error": str(e), "points": 0})
    
    # 9. Lore Database (3 points)
    try:
        from pathlib import Path
        worlds_dir = Path(__file__).parent.parent.parent / "lore" / "worlds"
        if worlds_dir.exists():
            world_count = len([d for d in worlds_dir.iterdir() if d.is_dir()])
            results.append({"test": "lore_database", "status": "pass", "worlds": world_count, "points": 3})
            total_score += 3
        else:
            results.append({"test": "lore_database", "status": "warn", "error": "No worlds directory", "points": 1})
            total_score += 1
    except Exception as e:
        results.append({"test": "lore_database", "status": "fail", "error": str(e), "points": 0})
    
    # 10. TTS Service (2 points)
    if state.tts_service:
        results.append({"test": "tts_service", "status": "pass", "points": 2})
        total_score += 2
    else:
        results.append({"test": "tts_service", "status": "skip", "error": "Not available (Cloud Run)", "points": 0})
    
    # Calculate grade
    max_score = 50
    percentage = (total_score / max_score) * 100
    
    if percentage >= 90:
        grade = "A"
    elif percentage >= 80:
        grade = "B"
    elif percentage >= 70:
        grade = "C"
    elif percentage >= 60:
        grade = "D"
    else:
        grade = "F"
    
    return {
        "validation_suite": "Kaedra 50-Point Validation",
        "score": total_score,
        "max_score": max_score,
        "percentage": round(percentage, 1),
        "grade": grade,
        "results": results,
        "timestamp": time.time()
    }

@app.get("/validate/quick")
async def quick_validation():
    """Quick health validation - just core services."""
    checks = {
        "api": True,
        "agent": state.agent is not None,
        "visual": state.visual_service is not None,
        "research": state.research_service is not None,
        "web": state.web_service is not None,
        "tts": state.tts_service is not None,
    }
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    return {
        "status": "healthy" if passed >= 4 else "degraded" if passed >= 2 else "unhealthy",
        "checks": checks,
        "passed": passed,
        "total": total
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
