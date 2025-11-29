# 🚀 Using Your GCP Credits - Quick Start Guide

**You have $50 in Gemini credits expiring December 22, 2025 (24 days)**

Here's how to maximize usage before they expire:

---

## ⚡ Fastest Ways to Use Credits

### 1. Deploy to Cloud Run (Recommended - Uses Credits 24/7)
```bash
# From the Dav1d directory
cd "dav1d brain"

# Build and deploy
gcloud run deploy dav1d-brain \
  --source . \
  --region us-east4 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 5
```

**Why this burns credits fast:**
- Min instances = 1 means you're paying for 1 instance 24/7
- 2 vCPU + 2GB RAM = ~$35/month
- Your $50 credit will be used in ~35 days (perfect timing!)

---

### 2. Use Premium Gemini Models Heavily

**Run expensive queries:**
```bash
python dav1d.py
```

Then in Dav1d:
```
/deep Tell me a comprehensive business plan for scaling AI with Dav3

/council How should I architect a multi-agent system for enterprise?

Generate 50 images of different UI designs for my app

Search the web for the latest AI news and summarize 20 articles
```

**Credit Consumption:**
- Gemini 3.0 Pro (deep): $0.01 per query × 100 queries = **$1.00**
- Image generation: $0.04 per image × 100 images = **$4.00**
- Vertex AI Grounding (search): $0.035 per query × 50 queries = **$1.75**

---

### 3. Set Up Automated Cloud Build

```bash
# Enable Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Set up automatic deployments from GitHub
gcloud builds submit --config=cloudbuild.yaml .

# Or set up triggers for every commit (burns credits via build minutes)
gcloud builds triggers create github \
  --repo-name=Watchtower \
  --repo-owner=YOUR_GITHUB_USERNAME \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

**Credit Consumption:**
- Each build: ~5 minutes on E2_HIGHCPU_8
- Cost per build: ~$0.15
- 10 builds/day × 24 days = **$36 in credits used**

---

### 4. Heavy API Usage Schedule

Create a script to burn through credits systematically:

```python
# burn_credits.py
import time
from tools.youtube_api import search_youtube_videos
from tools.maps_api import search_nearby_places
from tools.voice_api import text_to_speech

# Use free-tier APIs heavily (good practice, no cost)
for i in range(100):
    search_youtube_videos(f"AI tutorial {i}", max_results=10)
    time.sleep(1)

# Generate lots of voice files
texts = [
    "Testing premium voices",
    "Building AI with Dav3",
    "Who Visions LLC portfolio"
]

for i, text in enumerate(texts * 20):  # 60 TTS calls
    text_to_speech(
        text, 
        output_file=f"voice_test_{i}.mp3",
        voice_name="en-US-Journey-D"  # Premium voice
    )
```

**Run it:**
```bash
python burn_credits.py
```

---

## 📊 Credit Burn Rate Calculator

| Activity | Cost | Quantity | Total Credit Used |
|----------|------|----------|-------------------|
| Cloud Run (always on) | $35/mo | 24 days | **$28** |
| 100 Gemini 3.0 queries | $0.01 | 100 | **$1** |
| 200 Image generations | $0.04 | 200 | **$8** |
| 50 Web searches | $0.035 | 50 | **$1.75** |
| 100 TTS calls (Journey) | $0.016 | 100 | **$1.60** |
| Cloud Build (10 builds) | $0.15 | 10 | **$1.50** |
| **TOTAL** | | | **$41.85** |

**Remaining: ~$8** - Use for experimentation!

---

## 🎯 My Recommendation: "Aggressive Deployment Strategy"

1. **TODAY** - Deploy to Cloud Run with `--min-instances 1`
   - This alone will use $28 of your $50 over 24 days
   
2. **Week 1** - Heavy API testing
   - Generate 100 images for your UI
   - Run 50 web searches
   - Create 50 voice samples
   - Cost: ~$15
   
3. **Week 2-3** - Set up CI/CD
   - Configure Cloud Build triggers
   - Make 10-15 commits to test auto-deploy
   - Cost: ~$2
   
4. **Week 4** - Final sprint
   - Use Gemini 3.0 Pro exclusively
   - Generate final production assets
   - Cost: ~$5

**Total: $50 - Perfectly timed to expire!**

---

## 🔧 Quick Setup Commands

```bash
# 1. Install dependencies
cd "c:\Users\super\Watchtower\Dav1d\dav1d brain"
pip install -r requirements.txt

# 2. Set up API keys
# Add to .env file:
# YOUTUBE_API_KEY=your_key_here
# GOOGLE_MAPS_API_KEY=your_key_here

# 3. Test locally
python dav1d.py

# 4. Deploy to Cloud Run
gcloud run deploy dav1d-brain \
  --source . \
  --region us-east4 \
  --min-instances 1 \
  --memory 2Gi

# 5. Monitor credit usage
gcloud billing accounts list
```

---

## 💡 Pro Tip: Credit Monitoring

Check your credit usage daily:
```bash
# Open GCP Console → Billing → Credits
# Or use gcloud:
gcloud alpha billing accounts describe BILLING_ACCOUNT_ID
```

Set up a budget alert at $40 (80% of $50) so you know when you're close.

---

**TLDR: Deploy to Cloud Run TODAY with min-instances=1. That's the easiest way to burn $28 of credits over 24 days, then use the rest for heavy API testing.**
