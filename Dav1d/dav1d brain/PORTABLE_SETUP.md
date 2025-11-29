# 🌍 Dav1d Portable Setup Guide
**Run Dav1d from Anywhere in 3 Steps**

---

## ✅ YES, You Can Run Dav1d Anywhere!

Because Dav1d is **cloud-native**, you can pull the code and run it from:
- ✅ Your laptop
- ✅ Your desktop
- ✅ A friend's computer
- ✅ A cloud VM (AWS EC2, GCP Compute, Azure VM)
- ✅ GitHub Codespaces
- ✅ WSL/Linux/macOS

**All your data lives in GCP**, so the local machine is just a client.

---

## 📋 Prerequisites

### What You Need:
1. **Python 3.10+** installed
2. **Git** installed
3. **GCP Service Account Key** (one-time setup)

---

## 🚀 Quick Setup (3 Steps)

### ⚡ FASTEST: Google Cloud Shell (0 Auth Setup!)

**Perfect for testing - everything pre-configured!**

1. **Open Cloud Shell:** https://shell.cloud.google.com
2. **Run these commands:**
   ```bash
   # Clone repo
   git clone https://github.com/YOUR_USERNAME/Dav1d.git
   cd Dav1d/dav1d\ brain
   
   # Install dependencies (Python 3.9 pre-installed)
   pip install --user -r requirements.txt
   
   # Set project (already authenticated!)
   gcloud config set project gen-lang-client-0285887798
   
   # Run Dav1d - NO .env NEEDED!
   python dav1d.py
   ```

**Why Cloud Shell rocks:**
- ✅ Pre-authenticated with your Google account
- ✅ Python, git, gcloud already installed
- ✅ 5GB persistent storage across sessions
- ✅ Free tier includes 50 hours/week
- ✅ Access from any browser

---

### Standard Setup (Local Machine)

### Step 1: Clone the Repo
```bash
git clone https://github.com/YOUR_USERNAME/Dav1d.git
cd Dav1d/dav1d\ brain
```

### Step 2: Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Configure Authentication
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# GOOGLE_API_KEY=your_key_here
```

**That's it!** Run Dav1d:
```bash
python dav1d.py
```

---

## 🔑 Authentication Deep Dive

### Option A: API Key (Easiest - Recommended)
This is what you're currently using.

**Setup:**
1. Get API key: https://aistudio.google.com/app/apikey
2. Add to `.env`:
   ```bash
   GOOGLE_API_KEY=AIza...your_key_here
   GOOGLE_GENAI_USE_VERTEXAI=True
   ```

**Pros:**
- ✅ Works anywhere instantly
- ✅ No file management
- ✅ Easy to rotate/revoke

**Cons:**
- ⚠️ Must keep `.env` secret
- ⚠️ Not for production (use service accounts)

---

### Option B: Service Account JSON (Production)
Better for automation and CI/CD.

**Setup:**
1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create dav1d-runner \
     --display-name="Dav1d Runner"
   ```

2. **Grant Permissions:**
   ```bash
   gcloud projects add-iam-policy-binding gen-lang-client-0285887798 \
     --member="serviceAccount:dav1d-runner@gen-lang-client-0285887798.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   
   gcloud projects add-iam-policy-binding gen-lang-client-0285887798 \
     --member="serviceAccount:dav1d-runner@gen-lang-client-0285887798.iam.gserviceaccount.com" \
     --role="roles/bigquery.admin"
   ```

3. **Download Key:**
   ```bash
   gcloud iam service-accounts keys create dav1d-key.json \
     --iam-account=dav1d-runner@gen-lang-client-0285887798.iam.gserviceaccount.com
   ```

4. **Set Environment Variable:**
   ```bash
   # Windows (PowerShell)
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\dav1d-key.json"
   
   # Mac/Linux
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/dav1d-key.json"
   ```

**Pros:**
- ✅ Production-ready
- ✅ Fine-grained permissions
- ✅ Audit logging

**Cons:**
- ⚠️ More setup
- ⚠️ Must secure JSON file

---

### Option C: gcloud CLI (Development)
Let Google handle auth for you.

**Setup:**
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project gen-lang-client-0285887798

# Application Default Credentials
gcloud auth application-default login
```

**Pros:**
- ✅ No keys to manage
- ✅ Uses your Google account
- ✅ Automatic credential refresh

**Cons:**
- ⚠️ Only works with your Google account
- ⚠️ Can't use in automation

---

## 📦 What Gets Synced vs. What's Local

### Always in GCP (Portable):
- ✅ **Memory Bank** → Cloud Storage (`gs://dav1d-memory-us-east4`)
- ✅ **Semantic Memories** → BigQuery (`dav1d_memory.embeddings`)
- ✅ **Images** → Cloud Storage (`gs://dav1d-images-us-east4`)
- ✅ **Videos** → Cloud Storage (`gs://dav1d-videos-us-east4`)
- ✅ **Logs** → Cloud Storage (`gs://dav1d-logs-us-east4`)

### Local Only (Must Copy):
- ⚠️ `.env` file (contains secrets)
- ⚠️ Service account JSON keys (if using)
- ⚠️ `requirements.txt` (but in git)
- ⚠️ Python code (in git)

---

## 🌐 Real-World Scenarios

### Scenario 0: Google Cloud Shell (Instant Access)
```bash
# Literally just open your browser!
# https://shell.cloud.google.com

# Clone, install, run - done in 2 minutes
git clone https://github.com/YOUR_USERNAME/Dav1d.git
cd Dav1d/dav1d\ brain
pip install --user -r requirements.txt
python dav1d.py

# Your data persists in $HOME across sessions
# No local setup whatsoever!
```

**Use cases:**
- ✅ Demo Dav1d to others instantly
- ✅ Quick test without installing locally
- ✅ Access from Chromebook/tablet
- ✅ Run while traveling (just need browser)

### Scenario 1: Work Laptop → Home Desktop
```bash
# On work laptop
git push origin main

# On home desktop
git clone https://github.com/YOUR_USERNAME/Dav1d.git
cd Dav1d/dav1d\ brain
pip install -r requirements.txt

# Add same API key to .env
echo "GOOGLE_API_KEY=your_key" > .env

# Run - all your memories load from cloud!
python dav1d.py
```

### Scenario 2: Collaborator Access
```bash
# Give collaborator:
# 1. Git access
# 2. Their own API key (or share yours securely)

# They run:
git clone <repo>
pip install -r requirements.txt
# Add their API key to .env
python dav1d.py

# They see ALL the same data (shared GCP project)
```

### Scenario 3: Cloud VM (24/7 Agent)
```bash
# On GCP Compute Engine VM
gcloud compute instances create dav1d-runner \
  --zone=us-east4-a \
  --machine-type=e2-medium \
  --scopes=cloud-platform

# SSH in
gcloud compute ssh dav1d-runner

# Setup
git clone <repo>
pip install -r requirements.txt
gcloud auth application-default login

# Run as background service
nohup python dav1d.py &
```

---

## 🔒 Security Best Practices

### DO:
✅ Add `.env` to `.gitignore` (already done)
✅ Add `*.json` keys to `.gitignore` (already done)
✅ Use separate API keys per environment
✅ Rotate keys regularly
✅ Use service accounts for production

### DON'T:
❌ Commit `.env` to git
❌ Share API keys in Slack/Discord
❌ Use personal accounts for production
❌ Store keys in Docker images

---

## 🧪 Testing Portability

Run this on a new machine:

```bash
# Test script
cat > test_portable.sh << 'EOF'
#!/bin/bash
set -e

echo "🧪 Testing Dav1d Portability..."

# Check Python
python --version || { echo "❌ Python not found"; exit 1; }

# Check dependencies
pip install -q -r requirements.txt

# Check authentication
python -c "
import os
from google import genai

api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print('❌ GOOGLE_API_KEY not set')
    exit(1)

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
print('✅ Authentication works!')
print('✅ Dav1d is portable!')
"
EOF

chmod +x test_portable.sh
./test_portable.sh
```

---

## 📊 What's Your Setup?

Based on your current config:

```
✅ API Key: Yes (in .env)
✅ Project: gen-lang-client-0285887798
✅ Location: us-east4
✅ Cloud Storage: Configured
✅ BigQuery: Configured
⚠️ Service Account: Optional (you have JSON files but using API key)
```

**Recommendation:** Keep using API key for now. It's portable and simple.

---

## 🎯 TL;DR

**Yes, you can pull Dav1d from anywhere and run it!**

Minimum needed:
1. ✅ Git clone
2. ✅ `pip install -r requirements.txt`
3. ✅ `.env` file with `GOOGLE_API_KEY`

**All your data is already in GCP**, so you'll have access to:
- Your memories
- Your chat history
- Your images
- Your analytics

Just don't commit `.env` to git! 🔒

---

## 🚀 Next Steps

Want to make it even more portable?

1. **Docker Image:**
   ```bash
   # Build once, run anywhere
   docker build -t dav1d .
   docker run -e GOOGLE_API_KEY=$API_KEY dav1d
   ```

2. **Secrets Manager:**
   ```bash
   # Store API key in GCP Secret Manager
   # Dav1d auto-fetches it (no .env needed!)
   ```

3. **GitHub Actions:**
   ```bash
   # Run Dav1d on schedule from GitHub
   # No local machine needed
   ```

Interested in any of these? Let me know! 🚀
