# Kaedra Webhook Server
# Receives Notion change events and triggers sync

from flask import Flask, request, jsonify
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.sync_notion import NotionBridge

app = Flask(__name__)

# Default world ID (can be overridden via request)
DEFAULT_WORLD_ID = "world_bee9d6ac"


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "kaedra-webhook"})


@app.route("/webhook/notion", methods=["POST"])
def notion_webhook():
    """
    Receive Notion database change events.
    Triggers sync when Ingestion Queue items are updated.
    """
    try:
        data = request.json
        print(f"📥 Received Notion webhook: {json.dumps(data, indent=2)[:200]}...")
        
        # Get world ID from header or use default
        world_id = request.headers.get("X-World-ID", DEFAULT_WORLD_ID)
        
        # Trigger sync
        bridge = NotionBridge(world_id)
        if bridge.check_connection():
            bridge.pull_ingestion_queue()
            return jsonify({"status": "synced", "world_id": world_id})
        else:
            return jsonify({"status": "error", "message": "Notion connection failed"}), 500
            
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/sync/<world_id>", methods=["POST"])
def manual_sync(world_id: str):
    """Manually trigger a full sync for a world."""
    try:
        bridge = NotionBridge(world_id)
        if bridge.check_connection():
            bridge.sync_all()
            return jsonify({"status": "synced", "world_id": world_id})
        else:
            return jsonify({"status": "error", "message": "Notion connection failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/upload/<world_id>", methods=["POST"])
def upload_file(world_id: str):
    """Upload a file to Notion."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400
        
    file = request.files["file"]
    page_id = request.form.get("page_id")
    
    # Save temp file
    temp_path = Path(f"/tmp/{file.filename}")
    file.save(temp_path)
    
    try:
        bridge = NotionBridge(world_id)
        file_id = bridge.upload_file(temp_path, page_id)
        temp_path.unlink()  # Cleanup
        
        if file_id:
            return jsonify({"status": "uploaded", "file_id": file_id})
        else:
            return jsonify({"status": "error", "message": "Upload failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Kaedra Webhook Server starting on port {port}")
    print(f"   Endpoints:")
    print(f"   - GET  /health")
    print(f"   - POST /webhook/notion")
    print(f"   - POST /sync/<world_id>")
    print(f"   - POST /upload/<world_id>")
    app.run(host="0.0.0.0", port=port, debug=True)
