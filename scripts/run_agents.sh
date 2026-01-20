#!/bin/bash
# ============================================================================
# KAEDRA Autonomous Agent Runner
# Run Blade/Nyx agents in Cloud Shell with Vertex AI authentication
# ============================================================================

set -e

# Configuration
WORKSPACE="${HOME}/Kaedra"
PROTOCOL_FILE="${WORKSPACE}/.agent/AGENT_PROTOCOL.md"
LOG_FILE="${WORKSPACE}/.agent/agent_loop.log"
MAX_LOOPS=50
LOOP_DELAY=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${PURPLE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  KAEDRA Autonomous Agent Runner v1.0      ║${NC}"
echo -e "${PURPLE}║  BLADE + NYX Multi-Agent Loop             ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Check authentication
echo -e "${CYAN}[*] Checking Vertex AI authentication...${NC}"
if gcloud auth application-default print-access-token &>/dev/null; then
    echo -e "${GREEN}[✓] Authenticated with GCP${NC}"
else
    echo -e "${RED}[!] Not authenticated. Running gcloud auth...${NC}"
    gcloud auth application-default login
fi

# Clone or update repository
if [ -d "$WORKSPACE" ]; then
    echo -e "${CYAN}[*] Updating Kaedra repository...${NC}"
    cd "$WORKSPACE"
    git pull
else
    echo -e "${CYAN}[*] Cloning Kaedra repository...${NC}"
    git clone https://github.com/Who-Visions/Kaedra.git "$WORKSPACE"
    cd "$WORKSPACE"
fi

# Install dependencies
echo -e "${CYAN}[*] Installing dependencies...${NC}"
pip install -q -r requirements.txt 2>/dev/null || pip install -q google-genai httpx toml

# Create agent directory
mkdir -p "${WORKSPACE}/.agent"

# Initialize protocol file if not exists
if [ ! -f "$PROTOCOL_FILE" ]; then
    echo -e "${CYAN}[*] Initializing agent protocol...${NC}"
    cat > "$PROTOCOL_FILE" << 'EOF'
# Agent Protocol - Initialized by Runner
## Active Agent: BLADE
## Loop Count: 0
## Status: READY
EOF
fi

# Main loop function
run_agent_loop() {
    local loop_count=0
    local agent="BLADE"
    
    echo -e "${GREEN}[*] Starting autonomous loop...${NC}"
    echo "[$(date)] Agent loop started" >> "$LOG_FILE"
    
    while [ $loop_count -lt $MAX_LOOPS ]; do
        loop_count=$((loop_count + 1))
        echo ""
        echo -e "${PURPLE}═══════════════════════════════════════════${NC}"
        echo -e "${PURPLE} Loop $loop_count | Agent: $agent${NC}"
        echo -e "${PURPLE}═══════════════════════════════════════════${NC}"
        
        # Run agent
        if [ "$agent" = "BLADE" ]; then
            echo -e "${CYAN}[BLADE] Executing technical task...${NC}"
            python3 -c "
from kaedra.agents.blade import BladeAgent
agent = BladeAgent()
# Execute next task from protocol
result = agent.query('Check AGENT_PROTOCOL.md and execute next unclaimed B-task')
print(result)
" 2>&1 | tee -a "$LOG_FILE"
            agent="NYX"
        else
            echo -e "${PURPLE}[NYX] Executing creative/research task...${NC}"
            python3 -c "
from kaedra.agents.nyx import NyxAgent
agent = NyxAgent()
# Execute next task from protocol
result = agent.query('Check AGENT_PROTOCOL.md and execute next unclaimed N-task')
print(result)
" 2>&1 | tee -a "$LOG_FILE"
            agent="BLADE"
        fi
        
        # Check exit signal
        if grep -q "EXIT_SIGNAL: true" "$PROTOCOL_FILE" 2>/dev/null; then
            echo -e "${GREEN}[✓] EXIT_SIGNAL detected. Stopping loop.${NC}"
            break
        fi
        
        # Delay between loops
        echo -e "${CYAN}[*] Waiting ${LOOP_DELAY}s before next loop...${NC}"
        sleep $LOOP_DELAY
    done
    
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  Agent loop complete                      ║${NC}"
    echo -e "${GREEN}║  Total loops: $loop_count                        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo "[$(date)] Agent loop complete. Loops: $loop_count" >> "$LOG_FILE"
}

# Parse arguments
case "${1:-run}" in
    run)
        run_agent_loop
        ;;
    status)
        echo -e "${CYAN}[*] Agent Status:${NC}"
        cat "$PROTOCOL_FILE" 2>/dev/null || echo "No protocol file found"
        ;;
    logs)
        echo -e "${CYAN}[*] Recent Logs:${NC}"
        tail -50 "$LOG_FILE" 2>/dev/null || echo "No logs found"
        ;;
    reset)
        echo -e "${CYAN}[*] Resetting agent state...${NC}"
        rm -f "$PROTOCOL_FILE" "$LOG_FILE"
        echo -e "${GREEN}[✓] Reset complete${NC}"
        ;;
    *)
        echo "Usage: $0 {run|status|logs|reset}"
        exit 1
        ;;
esac
