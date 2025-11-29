# ☁️ Run Dav1d in Google Cloud Shell
**Zero Setup Required - Just Open Your Browser!**

---

## ⚡ Quick Start (Copy-Paste This)

### 1. Open Cloud Shell
**Click here:** https://shell.cloud.google.com/?project=gen-lang-client-0285887798

### 2. Run This Command Block
```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/Dav1d.git
cd Dav1d/dav1d\ brain

# Install dependencies (takes ~2 minutes)
pip install --user -r requirements.txt

# Configure project
gcloud config set project gen-lang-client-0285887798

# Launch Dav1d!
python dav1d.py
```

**That's it!** No API keys, no auth, no config files needed. ✅

---

## 🎯 Why Cloud Shell is Perfect for Dav1d

| Feature | Cloud Shell | Local Machine |
|---------|-------------|---------------|
| **Setup Time** | 2 minutes | 10-15 minutes |
| **Authentication** | Auto (gcloud) | Manual (.env) |
| **Python** | Pre-installed | Must install |
| **GCP Access** | Native | Via API key |
| **Cost** | Free (50hrs/wk) | Varies |
| **Portability** | Any browser | Single machine |

---

## 📦 What Gets Installed

When you run `pip install --user -r requirements.txt`, you get:

**Core AI:**
- `google-genai` - New Gen AI SDK
- `google-cloud-aiplatform` - Vertex AI
- `anthropic` - Claude support

**Cloud Services:**
- `google-cloud-bigquery` - Vector search
- `google-cloud-storage` - File storage
- `cloud-sql-python-connector` - Database access

**UI & Terminal:**
- `rich` - Beautiful terminal UI
- `prompt_toolkit` - Interactive prompts

**Total:** ~150MB, installs in 2-3 minutes on Cloud Shell

---

## 💡 Pro Tips

### 1. Persist Your Setup
Cloud Shell home directory (`$HOME`) persists across sessions!

```bash
# First time only
cd ~
git clone https://github.com/YOUR_USERNAME/Dav1d.git

# Every time you open Cloud Shell
cd ~/Dav1d/dav1d\ brain
python dav1d.py
```

### 2. Create an Alias
Add to `~/.bashrc`:
```bash
alias dav1d='cd ~/Dav1d/dav1d\ brain && python dav1d.py'
```

Now just type `dav1d` to launch!

### 3. Run in Background
```bash
# Start Dav1d in the background
nohup python dav1d.py > dav1d.log 2>&1 &

# Check logs
tail -f dav1d.log
```

### 4. Use Cloud Shell Editor
Built-in VS Code-like editor:
```bash
# Open editor
cloudshell edit dav1d.py

# Or use the web UI
# Click "Open Editor" button in Cloud Shell
```

### 5. Boost Performance (Temporarily)
```bash
# Cloud Shell normally has 1.7GB RAM
# Boost to 8GB for 24 hours (free)
cloudshell env update-default-image

# Check resources
free -h
df -h
```

---

## 🔧 Troubleshooting

### "Command not found: python"
Cloud Shell uses `python3`:
```bash
# Use python3 explicitly
python3 dav1d.py

# Or create alias
alias python=python3
```

### "Permission denied" during pip install
Use `--user` flag:
```bash
pip install --user -r requirements.txt
```

### "Project not set"
```bash
gcloud config set project gen-lang-client-0285887798
```

### Terminal freezes
Cloud Shell has 60-minute inactivity timeout:
```bash
# Reconnect and resume
cd ~/Dav1d/dav1d\ brain
python dav1d.py
```

---

## 📊 Cloud Shell Limits

**Free Tier:**
- ✅ 50 hours/week usage
- ✅ 5GB persistent storage ($HOME)
- ✅ 1.7GB RAM (boostable to 8GB for 24h)
- ✅ Internet egress included

**Session Limits:**
- ⏱️ 60-minute inactivity timeout
- ⏱️ 12-hour maximum session
- 🔄 Auto-reconnect on disconnect

**Not a problem for Dav1d** - most sessions are interactive!

---

## 🚀 Advanced: Run as a Service

Want Dav1d to run 24/7? Use Cloud Run instead:

```bash
# In Cloud Shell
cd ~/Dav1d/dav1d\ brain

# Deploy to Cloud Run
gcloud run deploy dav1d \
  --source . \
  --platform managed \
  --region us-east4 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 3600

# Get URL
gcloud run services describe dav1d --region us-east4 --format 'value(status.url)'
```

Now Dav1d is accessible via HTTPS endpoint!

---

## 🔒 Security Notes

### Cloud Shell is Secure:
- ✅ Isolated per user
- ✅ Automatic auth via your Google account
- ✅ No API keys needed
- ✅ Encrypted connections

### Best Practices:
- Don't store secrets in code (use Secret Manager)
- Use `gcloud auth` instead of API keys
- Enable audit logs for compliance
- Use separate projects for dev/prod

---

## 🎓 Quick Reference

### Essential Commands
```bash
# Navigate to Dav1d
cd ~/Dav1d/dav1d\ brain

# Update code
git pull

# Update dependencies
pip install --user -r requirements.txt --upgrade

# Run Dav1d
python dav1d.py

# Check GCP project
gcloud config get-value project

# View logs
cat ~/.dav1d/logs/*.log
```

### File Locations (Cloud Shell)
```
$HOME/
├── Dav1d/               # Your git repo (persistent)
│   └── dav1d brain/
│       ├── dav1d.py
│       └── requirements.txt
└── .local/              # pip packages (persistent)
    └── lib/python3.9/site-packages/
```

Note: Local cache (`memory/`, `images/`) goes to GCS anyway!

---

## 🌟 Comparison: Cloud Shell vs. Local

**Use Cloud Shell when:**
- ✅ You want to test quickly
- ✅ You're on a restricted machine (work laptop)
- ✅ You're traveling with just a tablet
- ✅ You want zero auth setup
- ✅ You want to demo to others

**Use Local when:**
- ✅ You need offline access
- ✅ You want custom IDE setup
- ✅ You prefer local debugging
- ✅ You have >12 hour sessions

**The Good News:** Both access the SAME cloud data! 🎉

---

## ✨ Summary

**Google Cloud Shell = Perfect Dav1d Runner**

```bash
# Literally this simple:
https://shell.cloud.google.com
git clone <repo>
cd Dav1d/dav1d\ brain
pip install --user -r requirements.txt
python dav1d.py
```

**No `.env`, no API keys, no hassle.** ☁️✨

---

## 📝 Bookmark This

**One-Click Launch:**
```
https://shell.cloud.google.com/?project=gen-lang-client-0285887798&cloudshell_git_repo=https://github.com/YOUR_USERNAME/Dav1d.git&cloudshell_working_dir=dav1d%20brain
```

Replace `YOUR_USERNAME` and bookmark this URL - instant Dav1d launch! 🚀
