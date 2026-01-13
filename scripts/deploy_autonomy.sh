#!/bin/bash

# Configuration
PROJECT_ID="gen-lang-client-0939852539"
REGION="us-central1"
SERVICE_NAME="kaedra-orchestrator"
TOPIC_NAME="kaedra-events-v1"
SUB_NAME="kaedra-orchestrator-sub"

echo "🚀 Deploying Autonomy Control Plane Infrastructure..."
echo "Target Project: $PROJECT_ID"

# 1. Set Project
echo "--- Setting Project ---"
gcloud config set project $PROJECT_ID

# 2. Enable Services
echo -e "\n--- Enabling GCP Services ---"
gcloud services enable pubsub.googleapis.com firestore.googleapis.com cloudrun.googleapis.com

# 3. Create Pub/Sub Topic
echo -e "\n--- Creating Pub/Sub Topic ---"
if ! gcloud pubsub topics describe $TOPIC_NAME > /dev/null 2>&1; then
    gcloud pubsub topics create $TOPIC_NAME --message-retention-duration=7d
else
    echo "Topic $TOPIC_NAME already exists."
fi

# 4. Create Firestore Database (Native Mode)
echo -e "\n--- Checking Firestore ---"
# We skip explicit creation as it might fail if DB exists. 

# 5. Build & Deploy Cloud Run Service
echo -e "\n--- Deploying Cloud Run Service ---"
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "PROJECT_ID=$PROJECT_ID" \
    --quiet

# 6. Create Push Subscription
echo -e "\n--- Configuring Push Subscription ---"
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

if [ -z "$CLOUD_RUN_URL" ]; then
    echo "❌ Failed to get Cloud Run URL. Subscription creation skipped."
else
    echo "Target URL: $CLOUD_RUN_URL/hooks/pubsub"
    
    if ! gcloud pubsub subscriptions describe $SUB_NAME > /dev/null 2>&1; then
        gcloud pubsub subscriptions create $SUB_NAME \
            --topic $TOPIC_NAME \
            --push-endpoint=$CLOUD_RUN_URL/hooks/pubsub \
            --ack-deadline=600 \
            --min-retry-delay=10s \
            --max-retry-delay=600s
        echo "✅ Subscription created."
    else
        echo "Updating existing subscription endpoint..."
        gcloud pubsub subscriptions update $SUB_NAME \
            --push-endpoint=$CLOUD_RUN_URL/hooks/pubsub
        echo "✅ Subscription updated."
    fi
fi

echo -e "\n✨ Deployment Complete!"
