# KAEDRA v0.0.6 Quick Start

## Installation

### Option 1: Using Batch Files (Windows)

```bash
# From Watchtower directory
cd kaedra_v006
Install_Dependencies.bat  # Install all requirements
Launch_Kaedra_v006.bat    # Launch KAEDRA

# OR from Watchtower root:
Launch_Kaedra.bat         # Auto-navigates to v0.0.6
```

### Option 2: Manual Python Setup

```bash
cd kaedra_v006

# Install dependencies
py -3 -m pip install -r requirements.txt

# OR
python -m pip install -r requirements.txt

# Launch KAEDRA
python run.py

# OR use the module directly
python -m kaedra
```

### Option 3: Install as Package

```bash
cd kaedra_v006
pip install -e .

# Then run from anywhere:
kaedra
```

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Google Cloud Authentication** (see below)

## Google Cloud Setup

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set project
gcloud config set project gen-lang-client-0285887798
```

## Batch Files Reference

### In `kaedra_v006/` directory:

- **`Launch_Kaedra_v006.bat`** - Full launcher with dependency checking
- **`Launch_Simple.bat`** - Quick launcher, minimal output
- **`Install_Dependencies.bat`** - Install/update all Python packages

### In `Watchtower/` root:

- **`Launch_Kaedra.bat`** - Auto-navigates to kaedra_v006 and launches
- **`Launch_Kaedra_Simple.bat`** - Simplified root launcher

## Troubleshooting

### Python Not Found

If you see "Python not found":

1. Install Python 3.12 from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart your terminal

### Import Errors

If you see import errors:

```bash
cd kaedra_v006
py -3 -m pip install --upgrade google-cloud-aiplatform google-generativeai python-dotenv
```

### No Google Credentials

If you see authentication errors:

```bash
gcloud auth application-default login
```

## Next Steps

Once launched, type `/help` to see all commands.

---

**KAEDRA v0.0.6** | Shadow Tactician | Who Visions LLC
