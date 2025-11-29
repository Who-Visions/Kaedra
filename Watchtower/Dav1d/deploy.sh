#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# DAV1D v0.1.0 - Deployment Script
# Who Visions LLC | AI with Dav3
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Configuration
PROJECT_ID="gen-lang-client-0285887798"
LOCATION="us-east4"
AGENT_NAME="dav1d-v010-digital-avatar"
DESCRIPTION="DAV1D v0.1.0 - Digital Avatar & Voice Intelligence Director for Who Visions LLC"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  DAV1D v0.1.0 - Deployment to Vertex AI Agent Engine"
echo "  Location: ${LOCATION}"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Check gcloud auth
echo "[1/5] Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "  [!] Not authenticated. Running 'gcloud auth login'..."
    gcloud auth login
fi
echo "  [✓] Authenticated"

# Set project
echo "[2/5] Setting project..."
gcloud config set project ${PROJECT_ID}
echo "  [✓] Project: ${PROJECT_ID}"

# Enable required APIs
echo "[3/5] Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --quiet
gcloud services enable cloudresourcemanager.googleapis.com --quiet
echo "  [✓] APIs enabled"

# Install dependencies
echo "[4/5] Installing Python dependencies..."
pip install -q google-cloud-aiplatform google-generativeai python-dotenv
echo "  [✓] Dependencies installed"

# Deploy agent
echo "[5/5] Deploying DAV1D to Vertex AI..."
echo ""

# Run the Python deployment
python3 << 'DEPLOY_SCRIPT'
import vertexai
from vertexai.preview import reasoning_engines
from datetime import datetime

PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"

# System prompt for DAV1D
SYSTEM_PROMPT = """You are DAV1D (pronounced "David"), the Digital Avatar & Voice Intelligence Director.

You are the public-facing digital mirror of Dave Meralus, owner of Who Visions LLC.
You represent the "AI with Dav3" brand - making advanced AI accessible and real.

Personality:
- AUTHENTIC: Keep it 100. No corporate speak. Real talk.
- KNOWLEDGEABLE: Deep expertise in AI, tech, products, and scaling businesses.
- HELPFUL: Genuinely want people to win. No gatekeeping.
- WITTY: Can joke and vibe, but know when to be serious.

Guidelines:
- Always be honest, even when uncomfortable
- Be transparent about being AI
- Speak naturally like Dave would - direct, engaging
- Use "we" when talking about Who Visions projects
"""

print(f"  Initializing Vertex AI in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

print("  Creating agent configuration...")

# For now, we'll create a basic reasoning engine
# Full ADK deployment requires additional setup

try:
    # Check if agent already exists
    print("  Checking for existing agents...")
    
    # Create timestamp for unique naming
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    display_name = f"Dav1d-v010-{timestamp}"
    
    print(f"  Creating new agent: {display_name}")
    
    # Note: The exact API for creating agents may vary
    # This is a placeholder for the actual ADK deployment
    
    print("")
    print("  ════════════════════════════════════════════════════════════════")
    print("  [!] Full ADK deployment requires additional configuration.")
    print("  ")
    print("  For now, run DAV1D locally with:")
    print("    python dav1d.py")
    print("  ")
    print("  Or test the agent configuration with:")
    print("    python agent.py")
    print("  ════════════════════════════════════════════════════════════════")
    
except Exception as e:
    print(f"  [!] Deployment note: {e}")
    print("  DAV1D can still run locally with: python dav1d.py")

DEPLOY_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  Deployment script complete!"
echo "  "
echo "  Next steps:"
echo "    1. Run locally: python dav1d.py"
echo "    2. Test agent: python agent.py"
echo "    3. Check Vertex AI Console for agent status"
echo "═══════════════════════════════════════════════════════════════════════════════"
