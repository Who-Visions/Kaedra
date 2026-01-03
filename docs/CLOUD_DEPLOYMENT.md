# Kaedra Google Cloud Deployment Guide

## 📦 Quick Deploy to Cloud Run

### Windows (PowerShell)
```powershell
.\deploy_cloud_run.bat
```

### Linux/Mac
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

---

## 🔧 Manual Deployment Steps

### 1. Set Project
```bash
gcloud config set project gen-lang-client-0939852539
```

### 2. Enable APIs
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Build Container
```bash
gcloud builds submit --tag gcr.io/gen-lang-client-0939852539/kaedra-shadow-tactician:latest .
```

### 4. Deploy to Cloud Run
```bash
gcloud run deploy kaedra-shadow-tactician \
  --image gcr.io/gen-lang-client-0939852539/kaedra-shadow-tactician:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=gen-lang-client-0939852539,KAEDRA_LOCATION=us-central1"
```

### 5. Get Service URL
```bash
gcloud run services describe kaedra-shadow-tactician \
  --region us-central1 \
  --format="value(status.url)"
```

---

## 🧪 Test Deployment

### Get A2A Card
```bash
curl https://YOUR-SERVICE-URL/a2a
```

### Chat Request
```bash
curl -X POST https://YOUR-SERVICE-URL/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Yo, status check?"}'
```

---

## 🔒 Secure Deployment (Authenticated)

To require authentication, deploy with:
```bash
gcloud run deploy kaedra-shadow-tactician \
  --image gcr.io/gen-lang-client-0939852539/kaedra-shadow-tactician:latest \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

Then test with:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://YOUR-SERVICE-URL/v1/chat \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "Yo, status check?"}'
```

---

## 📋 Environment Variables

The following environment variables are automatically set:
- `GOOGLE_CLOUD_PROJECT`: `gen-lang-client-0939852539`
- `KAEDRA_LOCATION`: `us-central1`

To add custom variables:
```bash
gcloud run services update kaedra-shadow-tactician \
  --region us-central1 \
  --update-env-vars "CUSTOM_VAR=value"
```

---

## 🚀 CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main
      - uploads

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - id: 'auth'
      uses: 'google-github-actions/auth@v1'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'
    
    - name: 'Set up Cloud SDK'
      uses: 'google-github-actions/setup-gcloud@v1'
    
    - name: 'Build and Deploy'
      run: |
        gcloud builds submit --tag gcr.io/gen-lang-client-0939852539/kaedra-shadow-tactician:latest
        gcloud run deploy kaedra-shadow-tactician \
          --image gcr.io/gen-lang-client-0939852539/kaedra-shadow-tactician:latest \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

---

## 📊 Monitoring & Logs

### View Logs
```bash
gcloud run services logs read kaedra-shadow-tactician --region us-central1
```

### Live Tail
```bash
gcloud run services logs tail kaedra-shadow-tactician --region us-central1
```

### Metrics
```bash
gcloud run services list --platform managed --region us-central1
```

---

## 💰 Cost Optimization

Cloud Run pricing is based on:
- **CPU**: $0.00002400/vCPU-second
- **Memory**: $0.00000250/GiB-second
- **Requests**: $0.40 per million requests

With 2 vCPUs and 2GiB RAM, approximate cost:
- Idle: Free (scales to zero)
- 1000 requests/day at 1s each: ~$0.20/month
- 10,000 requests/day at 1s each: ~$2.00/month

To reduce costs:
- Lower memory to 1Gi if sufficient
- Reduce CPU to 1 if performance allows
- Set concurrency higher to handle more requests per container

---

## 🔧 Troubleshooting

### Build Fails
Check if `Dockerfile` exists and is valid:
```bash
docker build -t test .
```

### Deployment Fails
Check service account permissions:
```bash
gcloud projects get-iam-policy gen-lang-client-0939852539
```

### Service Fails to Start
Check logs immediately:
```bash
gcloud run services logs read kaedra-shadow-tactician --region us-central1 --limit 100
```

### Port Issues
Ensure Dockerfile exposes port 8080 (Cloud Run default):
```dockerfile
EXPOSE 8080
CMD ["uvicorn", "kaedra.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

**Last Updated**: 2025-12-14
**Project**: WhoBanana (`gen-lang-client-0939852539`)
**Region**: `us-central1`
