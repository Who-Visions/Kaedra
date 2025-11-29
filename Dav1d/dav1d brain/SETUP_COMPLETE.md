# ✅ All APIs Implemented - Final Setup Guide

**Status:** All Google Cloud APIs from your utilization plan are now integrated into Dav1d!

---

## 🎯 What's Been Implemented

| API | Status | Files | Purpose |
|-----|--------|-------|---------|
| **Vertex AI (Gemini)** | ✅ Done | `dav1d.py` | Core AI brain |
| **BigQuery Vector Search** | ✅ Done | `tools/vector_store_bigquery.py` | Semantic memory |
| **Cloud SQL** | ✅ Done | `tools/database_cloud_sql.py` | Structured data |
| **Cloud Storage** | ✅ Done | `dav1d.py` (integrated) | Image & log storage |
| **Vertex AI Grounding** | ✅ Done | `dav1d.py` (GoogleSearch) | Web search |
| **Imagen 3/4** | ✅ Done | `dav1d.py` (image gen) | Image generation |
| **YouTube Data API** | ✅ NEW | `tools/youtube_api.py` | Video search |
| **Google Maps** | ✅ NEW | `tools/maps_api.py` | Location services |
| **Text-to-Speech** | ✅ NEW | `tools/voice_api.py` | Voice output |
| **Speech-to-Text** | ✅ NEW | `tools/voice_api.py` | Voice input |
| **Cloud Run** | ✅ NEW | `Dockerfile`, `cloudbuild.yaml` | Deployment |
| **Cloud Build** | ✅ NEW | `cloudbuild.yaml` | CI/CD |

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Configure API Keys

```powershell
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"

# Run the setup wizard
python setup_api_keys.py
```

**When prompted, paste your keys:**

1. **GOOGLE_API_KEY**: `AIzaB8RN6LQSVdpjnglSqGkC1G3HmiVPa4IpW1NDJmg...` (the one you just created)
2. **YOUTUBE_API_KEY**: Create at https://console.cloud.google.com/apis/credentials
3. **GOOGLE_MAPS_API_KEY**: Create at https://console.cloud.google.com/google/maps-apis/credentials

### Step 2: Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- ✅ YouTube API client
- ✅ Google Maps client
- ✅ Cloud Speech & TTS
- ✅ All existing dependencies

### Step 3: Test Everything

```powershell
# Test Dav1d locally
python dav1d.py
```

**Try these commands:**
```
search youtube for "AI with Dav3" videos

find coffee shops near Times Square New York

what's the distance from NYC to Boston

generate an image of a cyberpunk dashboard

convert this text to speech: "Hello, I am Dav1d"

analyze the sentiment of my last 10 chats
```

### Step 4: Start Burning Credits! 💰

```powershell
# Burn $2/day (gentle usage)
python burn_credits.py

# OR burn $50 in one session (aggressive)
python -c "from burn_credits import CreditBurner; b=CreditBurner(); [b.daily_burn_routine() for _ in range(24)]"
```

---

## 📊 API Capabilities Reference

### 🎥 YouTube (`tools/youtube_api.py`)

```python
# Search for videos
search_youtube_videos("AI tutorial", max_results=5)

# Get video details
get_video_details("dQw4w9WgXcQ")

# Get channel info
get_channel_info("UCxxxxxxx")
```

**Usage in Dav1d:**
```
"search youtube for Gemini 2.0 demos"
"show me details for youtube video [ID]"
```

### 🗺️ Maps (`tools/maps_api.py`)

```python
# Geocoding
geocode_address("1600 Amphitheatre Parkway")

# Reverse geocoding
reverse_geocode(37.4224764, -122.0842499)

# Find nearby places
search_nearby_places("Times Square", "restaurant", radius=1000)

# Get directions
get_directions("NYC", "Boston", mode="driving")

# Distance matrix
get_distance_matrix(["NYC", "LA"], ["Boston", "SF"])
```

**Usage in Dav1d:**
```
"where is the nearest coffee shop to me?"
"how do I get from Times Square to Brooklyn?"
"what's the distance between NYC and LA?"
```

### 🎤 Voice (`tools/voice_api.py`)

```python
# Text to Speech
text_to_speech(
    "Hello, I am Dav1d",
    voice_name="en-US-Journey-D",  # Premium voice
    output_file="greeting.mp3"
)

# Speech to Text
speech_to_text("recording.wav")

# List available voices
list_available_voices("en-US")
```

**Usage in Dav1d:**
```
"convert this to speech: [text]"
"transcribe my audio file at path/to/audio.wav"
"what premium voices are available?"
```

---

## 🏗️ Deployment to Cloud Run

```bash
# Enable required services
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Deploy from source
cd "c:\Users\super\Watchtower\Dav1d"
gcloud run deploy dav1d-brain \
  --source "dav1d brain" \
  --region us-east4 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=gen-lang-client-0285887798,LOCATION=us-east4
```

**To burn credits 24/7, set `--min-instances 1`**

---

## 🔥 Credit Burning Strategies

### Strategy 1: Automated Daily Burn ($2/day)
```powershell
# Set up Task Scheduler
schtasks /create /tn "Dav1d_Credit_Burn" /tr "c:\Users\super\Watchtower\Dav1d\dav1d brain\run_daily_burn.bat" /sc daily /st 03:00
```

### Strategy 2: Cloud Run Always-On ($28 in 24 days)
```bash
gcloud run deploy dav1d-brain --source . --min-instances 1 --memory 2Gi
```

### Strategy 3: Manual Heavy Usage (When you need it)
```bash
python burn_credits.py
```

---

## 📈 Expected Costs (Using Your $50 Credit)

| Activity | Unit Cost | Recommended Usage | Total |
|----------|-----------|-------------------|-------|
| Gemini 3.0 Pro queries | $0.014 | 100 queries | $1.40 |
| Imagen 4 generation | $0.04 | 200 images | $8.00 |
| Vertex AI Grounding | $0.035 | 100 searches | $3.50 |
| Gemini 2.5 Flash queries | $0.0019 | 1000 queries | $1.90 |
| **Cloud Run (24/7, 24 days)** | **$1.17/day** | **24 days** | **$28.08** |
| YouTube API | Free | Unlimited | $0.00 |
| Maps API (w/ $200 credit) | Free | ~40k queries | $0.00 |
| TTS (Journey voices) | $0.016 | 100 calls | $1.60 |
| STT | $0.024/min | 60 min | $1.44 |
| **TOTAL** |||**~$46**|

**Remaining $4** = Buffer for experimentation!

---

## 🎉 You're All Set!

**What you have now:**
- ✅ Complete multi-API Dav1d system
- ✅ YouTube video search & analysis
- ✅ Google Maps location services
- ✅ Voice input/output capabilities
- ✅ Cloud deployment ready
- ✅ Automated credit burning
- ✅ $50 in credits to use

**Next steps:**
1. Run `python setup_api_keys.py` to configure your keys
2. Run `python burn_credits.py` to start using your credit
3. Run `python dav1d.py` to chat with your fully-powered AI

---

## 🆘 Troubleshooting

**"API not enabled" error:**
```bash
gcloud services enable youtube.googleapis.com
gcloud services enable maps-backend.googleapis.com
gcloud services enable texttospeech.googleapis.com
gcloud services enable speech.googleapis.com
```

**"Quota exceeded" error:**
- Check quotas: https://console.cloud.google.com/iam-admin/quotas
- For image generation: Wait 60s between batches
- For Grounding: Rate limit to 10/minute

**"Authentication failed":**
```bash
gcloud auth application-default login
gcloud config set project gen-lang-client-0285887798
```

---

**LET'S BURN THOSE CREDITS! 🔥**

```powershell
python burn_credits.py
```
