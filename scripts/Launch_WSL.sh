#!/bin/bash
# KAEDRA v0.0.6 WSL Launcher
# Handles Virtual Environment automatically

echo "==============================================================================="
echo "    KAEDRA v0.0.6 - Shadow Tactician (WSL)"
echo "    Who Visions LLC"
echo "==============================================================================="
echo ""

# Ensure we are in the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Virtual environment location (use Linux home to avoid Windows filesystem issues)
VENV_DIR="$HOME/kaedra_venv"

# Check for Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creating virtual environment at $VENV_DIR..."
    python3 -m venv --without-pip "$VENV_DIR"
    
    # Install pip manually (WSL may lack python3-full)
    echo "[*] Installing pip..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$VENV_DIR/bin/python"
fi

# Check if pip exists in venv
if [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo "[*] Installing pip into virtual environment..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$VENV_DIR/bin/python"
fi

# Check for dependencies
if ! "$VENV_DIR/bin/pip" show google-cloud-aiplatform &> /dev/null; then
    echo "[*] Installing dependencies..."
    "$VENV_DIR/bin/pip" install -r requirements.txt
fi

# Run KAEDRA
echo "[*] Launching KAEDRA..."
echo ""
"$VENV_DIR/bin/python" run.py
