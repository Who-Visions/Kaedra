import logging
import base64
import json
import hmac
import hashlib
import os
from fastapi import APIRouter, Request, HTTPException, status, Header
from kaedra.api.app_state import state
from typing import Optional

try:
    from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
except ImportError:
    AsyncSlackRequestHandler = None

logger = logging.getLogger("kaedra.webhooks")
router = APIRouter(prefix="/hooks", tags=["Webhooks"])

# Notion Webhook Verification Token (Store securely, ideally in env/secrets)
NOTION_WEBHOOK_TOKEN = os.getenv("NOTION_WEBHOOK_TOKEN", "")

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


# -------------------------------------------------------------------------
# NOTION WEBHOOK ENDPOINT
# -------------------------------------------------------------------------

def _verify_notion_signature(body: bytes, signature: str, token: str) -> bool:
    """
    Verify Notion webhook signature using HMAC-SHA256.
    
    Args:
        body: The raw request body bytes.
        signature: The X-Notion-Signature header value (e.g., "sha256=...").
        token: The verification_token received during subscription setup.
    
    Returns:
        True if signature is valid, False otherwise.
    """
    if not token or not signature:
        return False
    
    try:
        expected_sig = "sha256=" + hmac.new(
            token.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)
    except Exception:
        return False


@router.post("/notion")
async def notion_webhook(
    request: Request,
    x_notion_signature: Optional[str] = Header(None, alias="X-Notion-Signature")
):
    """
    Handle incoming Notion webhook events.
    
    This endpoint:
    1. Handles initial verification (returns verification_token in response during setup).
    2. Validates signature on subsequent events.
    3. Processes supported event types (page.content_updated, comment.created, etc.).
    """
    try:
        body_bytes = await request.body()
        payload = json.loads(body_bytes)
        
        # --- Step 1: Handle Verification Request ---
        # During subscription setup, Notion sends a one-time POST with verification_token
        if "verification_token" in payload and not payload.get("type"):
            logger.info("🔑 Notion Webhook Verification Request Received")
            # Store this token securely for future signature validation
            # For now, we just acknowledge receipt. User must manually paste token.
            return {"status": "verification_received", "message": "Token received. Paste into Notion UI."}
        
        # --- Step 2: Validate Signature (for real events) ---
        if NOTION_WEBHOOK_TOKEN and x_notion_signature:
            if not _verify_notion_signature(body_bytes, x_notion_signature, NOTION_WEBHOOK_TOKEN):
                logger.warning("⚠️ Notion Webhook: Invalid Signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        elif NOTION_WEBHOOK_TOKEN and not x_notion_signature:
            # Token configured but no signature received: suspicious
            logger.warning("⚠️ Notion Webhook: Missing signature header")
            # Allow pass-through in dev, but log warning
        
        # --- Step 3: Process Event ---
        event_type = payload.get("type", "unknown")
        event_id = payload.get("id")
        entity = payload.get("entity", {})
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        
        logger.info(f"📬 Notion Webhook Event: {event_type} | Entity: {entity_type}:{entity_id}")
        
        # Handle specific event types
        if event_type == "page.content_updated":
            # Could trigger a sync or notify agents
            logger.info(f"  ↳ Page Updated: {entity_id}")
            # Example: state.notion_sync_service.queue_sync(entity_id)
            
        elif event_type == "page.created":
            logger.info(f"  ↳ Page Created: {entity_id}")
            
        elif event_type == "comment.created":
            data = payload.get("data", {})
            page_id = data.get("page_id")
            logger.info(f"  ↳ Comment Created on Page: {page_id}")
            # Could trigger agent to respond to comment
            
        elif event_type == "database.schema_updated" or event_type == "data_source.schema_updated":
            logger.info(f"  ↳ Schema Updated: {entity_id}")
            # Could trigger schema re-sync
            
        else:
            logger.info(f"  ↳ Unhandled event type: {event_type}")
        
        return {"status": "ok", "event_id": event_id}
        
    except json.JSONDecodeError:
        logger.error("❌ Notion Webhook: Invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Notion Webhook Error: {e}")
        return {"status": "error", "reason": str(e)}

