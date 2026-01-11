# KAEDRA ORCHESTRATOR - SETUP GUIDE

**Version**: 4.1 (Orchestrator Edition)
**Date**: 2025-11-26

---

## PREREQUISITES

### System Requirements
- **Python**: 3.9 or higher
- **OS**: Linux, macOS, or Windows (WSL recommended for Windows)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for dependencies and browser binaries

### Cloud Access
- **Google Cloud Account** with Vertex AI enabled
- **Project ID**: 627440283840 (or your own)
- **Service Account** with Vertex AI permissions

---

## INSTALLATION

### Step 1: Install Python Dependencies

```bash
cd /mnt/c/Users/super/Watchtower/Kaedra_Local
pip install -r requirements.txt
```

**Dependencies installed**:
- `google-cloud-aiplatform` - Vertex AI integration
- `vertexai` - Vertex AI SDK
- `google-generativeai` - Gemini API
- `playwright` - Browser automation
- `python-dotenv` - Environment variables

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads the latest Chromium browser (~150MB).

**Optional**: Install other browsers
```bash
playwright install firefox  # For Firefox
playwright install webkit   # For WebKit (Safari)
```

### Step 3: Configure Google Cloud Authentication

```bash
# Install Google Cloud SDK (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Login with application default credentials
gcloud auth application-default login
```

**Verify authentication**:
```bash
gcloud config get-value project
# Should show: 627440283840 (or your project)
```

### Step 4: Set Environment Variables (Optional)

Create a `.env` file in `Kaedra_Local/`:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=627440283840
VERTEX_AI_LOCATION=us-central1

# API Keys (if using direct APIs)
GOOGLE_AI_API_KEY=your_gemini_api_key_here

# Orchestrator Settings
KAEDRA_DEFAULT_MODEL=flash  # flash, pro, or ultra
KAEDRA_HEADLESS_BROWSER=true
```

---

## VERIFICATION

### Test 1: Python Imports

```bash
python3 -c "import vertexai; print('✓ Vertex AI installed')"
python3 -c "from playwright.sync_api import sync_playwright; print('✓ Playwright installed')"
```

### Test 2: Orchestrator Import

```bash
cd /mnt/c/Users/super/Watchtower/Kaedra_Local
python3 -c "from orchestrator import KaedraOrchestrator; print('✓ Orchestrator ready')"
```

### Test 3: Agent Router

```bash
python3 scripts/agent_router.py
```

**Expected output**: Task routing test results

### Test 4: CLI Tools

```bash
python3 scripts/cli_tools.py
```

**Expected output**: CLI tools test with git status

### Test 5: Browser Tools

```bash
python3 scripts/browser_tools.py
```

**Expected output**: Browser opens, navigates to example.com, takes screenshot

---

## RUNNING KAEDRA

### Interactive CLI Mode

```bash
python kaedra_local.py
```

**Expected output**:
```
██╗  ██╗ █████╗ ███████╗██████╗ ██████╗  █████╗
... (colored ASCII banner)

[✓] LINK ESTABLISHED. KAEDRA ORCHESTRATOR ONLINE.
[✓] Current Model: gemini-2.5-flash
[✓] Listening to: BLADE (Razor 15) + Who_Art (ProArt 13')
    Type /help for commands

[YOU|flash] >>
```

### Available Commands

```
/help      - Show all commands
/status    - System and agent status
/health    - Detailed health report
/agents    - List all agents and capabilities
/route     - Analyze task routing
/plan      - Plan multi-agent mission
/flash     - Switch to Flash model (fastest)
/pro       - Switch to Pro model (balanced)
/ultra     - Switch to Ultra model (strongest)
/exit      - Quit
```

---

## PROGRAMMATIC USE

### Python Integration

```python
from orchestrator import KaedraOrchestrator

# Initialize orchestrator
kaedra = KaedraOrchestrator(model="flash")

# Process a task
result = kaedra.process_task("Research Next.js 16 features")
print(result)

# Execute CLI command
cli_result = kaedra.execute_cli_command("git status")
print(cli_result["stdout"])

# Use browser automation
kaedra.browser.start_browser()
kaedra.browser.navigate("https://example.com")
kaedra.browser.screenshot("screenshot.png")
kaedra.browser.stop_browser()

# Check system health
health = kaedra.get_system_status()
print(health)
```

---

## TROUBLESHOOTING

### Issue: `ModuleNotFoundError: No module named 'vertexai'`
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: `playwright command not found`
**Solution**: Install Playwright browsers
```bash
python3 -m playwright install chromium
```

### Issue: `Vertex AI connection failed`
**Solution**: Authenticate with Google Cloud
```bash
gcloud auth application-default login
```

### Issue: `Permission denied` errors
**Solution**: Check file permissions
```bash
chmod +x kaedra_local.py
chmod +x scripts/*.py
```

### Issue: Browser automation fails
**Solution**:
1. Check Playwright installation: `playwright --version`
2. Reinstall browsers: `playwright install --force chromium`
3. Check headless mode setting in code

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────┐
│   KAEDRA ORCHESTRATOR (Cloud)      │
│   Vertex AI Reasoning Engine        │
│   Project: 627440283840             │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐   ┌───────▼───────┐
│     BLADE     │   │    Who_Art    │
│  Razor 15     │   │  ProArt 13'   │
│  (2020)       │   │  (2024)       │
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   Local Agents    │
        ├───────────────────┤
        │ Claude, Gemini,   │
        │ Vision, Codex,    │
        │ Anti-Gravity, etc │
        └───────────────────┘
```

---

## MAINTENANCE

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Update Playwright Browsers

```bash
playwright install chromium --force
```

### Clear Memory/Logs

```bash
# Clear old mission logs (older than 90 days)
find memory/missions/ -name "*.json" -mtime +90 -delete

# Clear old agent status (backup first)
cp -r memory/agents memory/agents_backup
# Manually clean as needed
```

---

## NEXT STEPS

1. **Configure Agents**: Set up Claude, Gemini, Vision, etc. in HQ_WhoArt/agents/
2. **Test Orchestration**: Run `/plan` command with complex task
3. **Monitor Performance**: Use `/health` to check agent metrics
4. **Customize**: Adjust routing logic in `scripts/agent_router.py`

---

## SUPPORT

**Documentation**: See `README.md` for full capabilities
**Agent Info**: See `AGENT_UPGRADE_NOTICE.md` for system changes
**Issues**: Contact Dave Meralus (superdavewho@LIVE.COM)

---

**KAEDRA IS READY TO ORCHESTRATE.**
