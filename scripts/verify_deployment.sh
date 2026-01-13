#!/bin/bash

# Configuration
PROJECT_ID="gen-lang-client-0939852539"
TOPIC_NAME="kaedra-events-v1"

echo "🧪 Starting End-to-End Verification..."
echo "Target Project: $PROJECT_ID"

# 1. Verify Topic Exists
if ! gcloud pubsub topics describe $TOPIC_NAME --project $PROJECT_ID > /dev/null 2>&1; then
    echo "❌ Error: Topic '$TOPIC_NAME' not found. Did you run deploy_autonomy.sh?"
    exit 1
fi

echo "✅ Topic '$TOPIC_NAME' found."

# 2. Publish Test Event
echo "📤 Publishing Test Event..."
MESSAGE_BODY='{"event_id": "test-verify-001", "event_type": "system.verification", "payload": {"source": "cloud-shell", "message": "Hello Kaedra"}}'

gcloud pubsub topics publish $TOPIC_NAME --project $PROJECT_ID --message="$MESSAGE_BODY"

echo "✅ Test Event Published."
echo ""
echo "👀 Verification Steps:"
echo "1. Check your Notion 'Agent Jobs' (or Ops) database for a new task titled 'Autonomy Event: system.verification'."
echo "2. Check #kaedra-ops in Slack (if configured)."
echo "3. Run 'gcloud beta run services logs tail kaedra-orchestrator --project $PROJECT_ID' to see logs."
