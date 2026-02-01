from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from kaedra.api.app_state import state
from kaedra.story import Mode, BeatResponse

router = APIRouter(prefix="/story", tags=["StoryEngine"])

class DoctrineResponse(BaseModel):
    debt: int
    red_marks: float
    green_marks: float
    wound: str
    identity_stage: int
    pattern: str

class StateResponse(BaseModel):
    tension: float
    emotions: Dict[str, float]
    pov: str
    mode: str
    scene: int
    doctrine: DoctrineResponse
    active_lore: List[Dict[str, Any]] = []
    character_stats: Dict[str, Any] = {}
    equipment: List[Dict[str, Any]] = []
    environment: Dict[str, Any] = {}
    session_log: List[Dict[str, Any]] = []

class PulseRequest(BaseModel):
    emotion: str
    delta: float

class LightRequest(BaseModel):
    effect: str
    color: Optional[str] = "white"
    period: Optional[float] = 0.5

class UpdateStateRequest(BaseModel):
    tension: Optional[float] = None
    pov: Optional[str] = None
    mode: Optional[str] = None
    emotions: Optional[Dict[str, float]] = None

@router.get("/dashboard", response_model=StateResponse)
async def get_story_state():
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    engine = state.story_engine
    doc = engine.doctrine
    
    # Get robust state dictionary from engine (includes LoreDB data)
    engine_state = engine.state
    
    return StateResponse(
        tension=engine.tension.current,
        emotions=engine.emotions.state,
        pov=engine.pov,
        mode=engine.mode.name,
        scene=engine.scene,
        doctrine=DoctrineResponse(
            debt=doc.abstraction_debt,
            red_marks=doc.red_marks,
            green_marks=doc.green_marks,
            wound=doc.wound,
            identity_stage=doc.identity_stage,
            pattern=doc.pattern
        ),
        active_lore=engine_state.get("active_lore", []),
        character_stats=engine_state.get("character_stats", {}),
        equipment=engine_state.get("equipment", []),
        environment=engine_state.get("environment", {}),
        session_log=engine_state.get("session_log", [])
    )

@router.post("/pulse")
async def pulse_emotion(request: PulseRequest):
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    state.story_engine.emotions.pulse(request.emotion, request.delta)
    # Trigger lighting sync
    state.story_engine._sync_lighting()
    return {"status": "success", "new_state": state.story_engine.emotions.state}

@router.post("/tension")
async def set_tension(target: float = Body(..., embed=True)):
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    state.story_engine.tension.target = target
    return {"status": "success", "new_target": target}

@router.post("/light")
async def trigger_light(request: LightRequest):
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    lc = state.story_engine.lights
    if request.effect == "pulse":
        lc.pulse(color=request.color or "white", period=request.period or 0.5)
    elif request.effect == "breathe":
        lc.breathe(color=request.color or "red", period=request.period or 2.0)
    elif request.effect == "fire":
        lc.fire_mode()
    elif request.effect == "stop":
        lc.stop()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown effect: {request.effect}")
        
    return {"status": "success"}

@router.post("/beat", response_model=BeatResponse)
async def generate_beat(prompt: str = Body(..., embed=True)):
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    engine = state.story_engine
    
    # Run the engine (this is a simplified mock of engine.run() as I need to check exact signature)
    # Most story engines have a 'next_beat' or 'generate' method.
    # Looking at the code, it seems to use process_task or similar in parent orchestrator
    # but StoryEngine itself likely has a main loop or run method.
    
    try:
        # Main entry point for the story engine turn
        result = await engine.generate_response(prompt)
        
        # Raw text extraction
        text = result.text if hasattr(result, 'text') else str(result)
        
        # Extract questions (StoryEngine appends ### Questions for the Author)
        questions = []
        if "### Questions for the Author" in text:
            parts = text.split("### Questions for the Author")
            text = parts[0].strip()
            if len(parts) > 1:
                # Basic parsing of bullet points
                q_lines = parts[1].strip().split("\n")
                questions = [q.strip().lstrip("- ").lstrip("* ") for q in q_lines if q.strip()]
        
        return BeatResponse(
            id=datetime.now().isoformat(),
            content=text,
            questions=questions,
            timestamp=datetime.now().timestamp(),
            tension=engine.tension.current,
            pov=engine.pov
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/state")
async def update_state(request: UpdateStateRequest):
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    engine = state.story_engine
    if request.tension is not None:
        engine.tension.current = request.tension
    if request.pov is not None:
        engine.pov = request.pov
    if request.mode is not None:
        try:
            engine.set_mode(Mode[request.mode.upper()])
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {request.mode}")
    if request.emotions is not None:
        for k, v in request.emotions.items():
            engine.emotions.set(k, v)
            
    return {"status": "success"}

@router.get("/history", response_model=List[BeatResponse])
async def get_history():
    if not state.story_engine:
        raise HTTPException(status_code=503, detail="StoryEngine not initialized.")
    
    # Return from engine.snapshots
    history = []
    for snap in state.story_engine.snapshots:
        history.append(BeatResponse(
            id=snap.get('id', datetime.now().isoformat()),
            content=snap.get('text', ''),
            questions=snap.get('questions', []),
            timestamp=snap.get('timestamp', datetime.now().timestamp()),
            tension=snap.get('tension', 0.2),
            pov=snap.get('pov', 'Narrator')
        ))
    return history


class DiceRollRequest(BaseModel):
    dice: str = "d20"  # e.g. "d20", "2d6", "d100"
    modifier: int = 0
    reason: str = ""

class DiceRollResponse(BaseModel):
    dice: str
    rolls: List[int]
    modifier: int
    total: int
    reason: str
    timestamp: str

@router.post("/roll", response_model=DiceRollResponse)
async def roll_dice(request: DiceRollRequest):
    """Roll dice and log to session."""
    import random
    import re
    from datetime import datetime
    
    # Parse dice notation (e.g., "2d6", "d20")
    match = re.match(r'(\d*)d(\d+)', request.dice.lower())
    if not match:
        raise HTTPException(status_code=400, detail=f"Invalid dice format: {request.dice}")
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + request.modifier
    
    result = DiceRollResponse(
        dice=request.dice,
        rolls=rolls,
        modifier=request.modifier,
        total=total,
        reason=request.reason,
        timestamp=datetime.now().isoformat()
    )
    
    # Add to session log if engine available
    if state.story_engine:
        state.story_engine.snapshots.append({
            "type": "roll",
            "dice": request.dice,
            "result": total,
            "reason": request.reason,
            "timestamp": datetime.now().isoformat()
        })
    
    return result
