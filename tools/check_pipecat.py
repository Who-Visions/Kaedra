import importlib
import pkgutil
import pipecat
import os

print("Pipecat imported:", pipecat.__file__)

def list_submodules(package):
    if hasattr(package, "__path__"):
        for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
            print(f"Submodule: {name} (is_pkg={is_pkg})")

print("Scanning pipecat submodules...")
# list_submodules(pipecat) # This might be too verbose

# Try to import directly what we expect from docs
try:
    from pipecat.vad.silero import SileroVADAnalyzer
    print("FOUND: SileroVADAnalyzer")
except ImportError:
    print("NOT FOUND: pipecat.vad.silero.SileroVADAnalyzer")

try:
    from pipecat.vad.vad_analyzer import VADAnalyzer
    print("FOUND: VADAnalyzer")
except ImportError:
    print("NOT FOUND: pipecat.vad.vad_analyzer.VADAnalyzer")
    
# Check for SmartTurn
# Sometimes it is part of vad or separately
try:
    # Guessing path based on naming convention
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    print("FOUND: pipecat.audio.vad.silero.SileroVADAnalyzer")
except ImportError:
    pass

