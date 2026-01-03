#!/bin/bash
# ====================================================
#  Kaedra - Deploy to Google Cloud Run
#  Project: WhoBanana (gen-lang-client-0939852539)
#  Region: us-central1
# ====================================================

PROJECT_ID="gen-lang-client-0939852539"
SERVICE_NAME="kaedra-shadow-tactician"
REGION="us-central1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo ""
echo "===================================================="
echo " Deploying KAEDRA to Cloud Run"
echo "===================================================="
echo " Project: ${PROJECT_ID}"
echo " Service: ${SERVICE_NAME}"
echo " Region:  ${REGION}"
echo " Image:   ${IMAGE}"
echo "===================================================="
echo ""

# 1. Set active project
echo "[1/5] Setting active project..."
gcloud config set project ${PROJECT_ID}

# 2. Enable required APIs
echo "[2/5] Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# 3. Build container image
echo "[3/5] Building container image..."
gcloud builds submit --tag ${IMAGE} .

# 4. Deploy to Cloud Run
echo "[4/5] Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},KAEDRA_LOCATION=${REGION}"

# 5. Get service URL
echo "[5/5] Getting service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)")

echo ""
echo "===================================================="
echo " SUCCESS! Kaedra deployed to Cloud Run"
echo "===================================================="
echo " URL: ${SERVICE_URL}"
echo " Endpoints:"
echo "   - Health: ${SERVICE_URL}/"
echo "   - A2A Card: ${SERVICE_URL}/a2a"
echo "   - Chat API: ${SERVICE_URL}/v1/chat"
echo "===================================================="
echo ""

echo "Test with:"
echo "  curl ${SERVICE_URL}/a2a"
echo ""
