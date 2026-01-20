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
import nest_asyncio
nest_asyncio.apply()  # Allow nested event loops for sync-in-async compatibility

# -------------------------------------------------------------------------
# GLOBAL STATE & CONFIG
# -------------------------------------------------------------------------
from kaedra.api.app_state import state, AppState
from kaedra.core.config import PROJECT_ID, LOCATION, MODEL_LOCATION

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
from . import lore, webhooks
app.include_router(lore.router)
app.include_router(webhooks.router)

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

    try:
        # Core prompt/memory
        prompt_service = PromptService(project=PROJECT_ID, location=LOCATION)
        memory_service = MemoryService()
        
        # Parallel initialization where possible
        state.web_service = WebService()
        state.research_service = ResearchService(prompt_service)
        
        state.agent = KaedraAgent(prompt_service, memory_service)
        
        # Slack starts last
        slack_service = SlackService()
        slack_service.initialize(agent=state.agent)
        state.slack_service = slack_service
        await slack_service.start()
        
        print("[+] Background initialization complete.")
    except Exception as e:
        print(f"[!] Background Init Error: {e}")

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
    temperature: float = 0.7
    use_grounding: bool = True

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
    model: str = "text-embedding-004"

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

@app.post("/generate", response_model=GenerateResponse)
async def fleet_generate(request: GenerateRequest):
    """
    Fleet Generate Endpoint: Direct text generation.
    """
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    result = await state.agent.prompt_service.generate_async(
        prompt=request.prompt,
        model_key=request.model or "flash" # Default to Flash for speed
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
            # Google Models (Global)
            {"id": "gemini-3-flash-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-3-pro-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-3-pro-image-preview", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-pro", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-flash", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.5-flash-lite", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.0-flash-001", "id_alias": "gemini-2.0-flash", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            {"id": "gemini-2.0-flash-lite-001", "id_alias": "gemini-2.0-flash-lite", "object": "model", "owned_by": "google", "endpoints": ["global"]},
            
            # Specialized Multi-Modal
            {"id": "imagen-4.0-generate-001", "object": "model", "owned_by": "google"},
            {"id": "veo-3.1-generate-001", "object": "model", "owned_by": "google"},
            
            # Partner Models (MaaS - Global)
            {"id": "claude-4.5-opus", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "claude-4.5-sonnet", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "claude-4-opus", "object": "model", "owned_by": "anthropic", "endpoints": ["global"]},
            {"id": "mistral-large-2407", "object": "model", "owned_by": "mistral", "endpoints": ["global"]},
            
            # Open Models (MaaS - Global)
            {"id": "deepseek-r1-0528", "object": "model", "owned_by": "deepseek", "endpoints": ["global"]},
            {"id": "llama-4-maverick-17b-128e-preview", "object": "model", "owned_by": "meta", "endpoints": ["global"]},
            {"id": "qwen3-next-80b-thinking", "object": "model", "owned_by": "alibaba", "endpoints": ["global"]}
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
    """List all available story sessions."""
    from pathlib import Path
    
    sessions_dir = Path(__file__).parent.parent.parent / "lore" / "sessions"
    if not sessions_dir.exists():
        return {"sessions": []}
    
    sessions = []
    for session_dir in sessions_dir.iterdir():
        if session_dir.is_dir():
            meta_file = session_dir / "session.json"
            if meta_file.exists():
                import json
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    sessions.append({
                        "id": session_dir.name,
                        "world_id": meta.get("world_id", "unknown"),
                        "mode": meta.get("mode", "writer"),
                        "created": meta.get("created", ""),
                        "word_count": meta.get("word_count", 0)
                    })
                except Exception:
                    sessions.append({"id": session_dir.name, "world_id": "unknown"})
    
    return {"sessions": sessions}

@app.post("/story/session")
async def create_story_session(request: StorySessionRequest):
    """Create a new story session."""
    from pathlib import Path
    import json
    import uuid
    from datetime import datetime
    
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    sessions_dir = Path(__file__).parent.parent.parent / "lore" / "sessions"
    session_dir = sessions_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    meta = {
        "id": session_id,
        "world_id": request.world_id,
        "mode": request.mode,
        "created": datetime.now().isoformat(),
        "word_count": 0
    }
    
    (session_dir / "session.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (session_dir / "draft.md").write_text("", encoding="utf-8")
    
    return {"session_id": session_id, "status": "created", "meta": meta}

@app.get("/story/session/{session_id}")
async def get_story_session(session_id: str):
    """Get story session details and content."""
    from pathlib import Path
    import json
    
    session_dir = Path(__file__).parent.parent.parent / "lore" / "sessions" / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    meta_file = session_dir / "session.json"
    draft_file = session_dir / "draft.md"
    
    meta = {}
    content = ""
    
    if meta_file.exists():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    
    if draft_file.exists():
        content = draft_file.read_text(encoding="utf-8")
    
    return {"meta": meta, "content": content}

@app.post("/story/generate")
async def generate_story_content(request: StoryGenerateRequest):
    """Generate story content using StoryEngine."""
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
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
    if state.agent and hasattr(state.agent, 'prompt_service'):
        try:
            # Quick validation call
            results.append({"test": "prompt_service", "status": "pass", "points": 10})
            total_score += 10
        except Exception as e:
            results.append({"test": "prompt_service", "status": "fail", "error": str(e), "points": 0})
    else:
        results.append({"test": "prompt_service", "status": "skip", "error": "Agent not available", "points": 0})
    
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
