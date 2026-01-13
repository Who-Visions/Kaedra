import logging
import base64
import json
from fastapi import APIRouter, Request, HTTPException, status
from kaedra.api.app_state import state

try:
    from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
except ImportError:
    AsyncSlackRequestHandler = None

logger = logging.getLogger("kaedra.webhooks")
router = APIRouter(prefix="/hooks", tags=["Webhooks"])

@router.post("/slack/commands")
@router.post("/slack/events")
async def slack_endpoint(request: Request):
    """
    Handle incoming Slack interactions (slash commands, events).
    Routes requests to the SlackService via Bolt adapter.
    """
    if not AsyncSlackRequestHandler:
        logger.error("❌ slack_bolt not installed")
        raise HTTPException(status_code=500, detail="Slack integration missing dependencies")

    if not state.slack_service or not state.slack_service.app:
        logger.warning("⚠️ SlackService not initialized")
        raise HTTPException(status_code=503, detail="Slack service unavailable")
    
    handler = AsyncSlackRequestHandler(state.slack_service.app)
    return await handler.handle(request)

@router.post("/pubsub")
async def pubsub_webhook(request: Request):
    """
    Handle Google Cloud Pub/Sub push messages.
    """
    try:
        envelope = await request.json()
        if not envelope:
            msg = "no Pub/Sub message received"
            logger.error(f"❌ {msg}")
            raise HTTPException(status_code=400, detail=f"Bad Request: {msg}")

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            logger.error(f"❌ {msg}")
            raise HTTPException(status_code=400, detail=f"Bad Request: {msg}")

        pubsub_message = envelope["message"]
        
        # Decode data
        if "data" in pubsub_message:
            decoded_bytes = base64.b64decode(pubsub_message["data"])
            decoded_str = decoded_bytes.decode("utf-8")
            event_data = json.loads(decoded_str)
        else:
            event_data = {}
            
        event_id = pubsub_message.get("messageId")
        attributes = pubsub_message.get("attributes", {})
        event_type = attributes.get("event_type", "unknown")
        
        logger.info(f"📨 Pub/Sub Message Received: {event_id} Type: {event_type}")

        if state.orchestrator:
            await state.orchestrator.ingest_event(event_id, event_type, event_data)
        else:
            logger.warning("⚠️ Orchestrator not initialized, event ignored.")

        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"❌ Pub/Sub Webhook Error: {e}")
        # Return 200 to acknowledge Pub/Sub and prevent retry loops for bad formatting
        return {"status": "error", "reason": str(e)}
