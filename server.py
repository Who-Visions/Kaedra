"""
Kaedra Agent API Server.

This module exposes the Kaedra Orchestrator via a FastAPI interface,
allowing for external interaction, fleet communication, and webhook handling.
"""

import os
import sys
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Ensure we can import local modules
try:
    from orchestrator import KaedraOrchestrator
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from orchestrator import KaedraOrchestrator

app = FastAPI(
    title="Kaedra Agent API",
    version="4.2",
    description="Fleet-compatible API for Kaedra Orchestrator"
)

# Initialize Orchestrator (Global)
# We default to 'pro' (Gemini 3 Pro) for server operations
orchestrator = KaedraOrchestrator(model="pro")

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    model: Optional[str] = "pro"
    history: Optional[List[Dict[str, str]]] = []

class GenerateRequest(BaseModel):
    """Request model for generation endpoint."""
    prompt: str
    model: Optional[str] = "pro"

@app.get("/")
def read_root() -> Dict[str, str]:
    """Root endpoint returning service status."""
    return {"status": "online", "agent": "Kaedra", "version": "4.2"}

@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint returning internal system status."""
    status = orchestrator.get_system_status()
    return status

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Standard chat endpoint for Agent-to-Agent communication.
    """
    try:
        # If model requested differs, switch temporarily (or permanently)
        if request.model and request.model != orchestrator.model:
            orchestrator.switch_model(request.model)

        # Kaedra expects a user instruction.
        # We wrap it in a pseudo-chat structure if needed, or just pass raw.
        # orchestrator.process_task returns a Dict with result.

        response_data = orchestrator.process_task(request.message)

        # Format response for the fleet (looking for 'response' or 'message' key)
        # The execute_simple_task returns 'message', execute_mission returns 'status'/'results'

        msg = response_data.get("message")
        if not msg and "results" in response_data:
            # It was a mission
            msg = f"Mission Completed. {response_data['tasks_completed']} tasks executed."

        return {
            "response": msg or str(response_data),
            "data": response_data
        }

    except Exception as exc:
        print(f"Chat Error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/webhook/notion")
async def notion_webhook(request: Request):
    """
    Notion webhook receiver.
    - Handles verification challenges during setup
    - Receives page/database update events
    """
    body = await request.json()

    # Verification handshake - Notion sends this during subscription setup
    if "verification_token" in body:
        print("[Notion Webhook] Verification request received")
        return {"challenge": body["verification_token"]}

    # Real events come here after verification
    event_type = body.get("type", "unknown")
    print(f"[Notion Webhook] Event received: {event_type}")
    print(f"[Notion Webhook] Payload: {body}")

    # Note: Process events (page.updated, database.updated, comment.created, etc.)

    return {"status": "received", "event_type": event_type}


@app.post("/generate")
async def generate_endpoint(request: GenerateRequest):
    """
    Compatibility endpoint for Kronos/Other agents using /generate.
    """
    try:
        response_data = orchestrator.process_task(request.prompt)

        msg = response_data.get("message")
        if not msg and "results" in response_data:
            msg = f"Mission Completed. {response_data['tasks_completed']} tasks executed."

        return {
            "response": msg or str(response_data),
            "content": msg or str(response_data) # Redundancy for different clients
        }
    except Exception as exc:
        print(f"Generate Error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

if __name__ == "__main__":
    import uvicorn
    # Use port 8080 for Cloud Run default
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
