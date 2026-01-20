"""
Autosync Agent Handoffs
Runs the handoff sync script every 5 minutes.
"""
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SYNC_SCRIPT = Path(__file__).parent / "sync_handoffs_to_notion.py"
INTERVAL_SECONDS = 300  # 5 minutes

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def run_sync():
    log("🔄 Starting handoff sync...")
    try:
        # Run the sync script as a subprocess
        result = subprocess.run(
            [sys.executable, str(SYNC_SCRIPT)],
            capture_output=True,
            text=True,
            check=False  # Don't throw exception on non-zero exit
        )
        
        # Log output
        if result.stdout:
            print(result.stdout.strip())
            
        if result.stderr:
            print("STDERR:", result.stderr.strip())
            
        if result.returncode == 0:
            log("✅ Sync successful")
        else:
            log(f"⚠️ Sync completed with exit code {result.returncode}")
            
    except Exception as e:
        log(f"❌ Error running sync: {e}")

def main():
    log(f"🚀 Autosync service started. Interval: {INTERVAL_SECONDS}s")
    
    while True:
        run_sync()
        
        log(f"💤 Sleeping for {INTERVAL_SECONDS}s...")
        try:
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            log("🛑 Autosync stopped by user")
            break

if __name__ == "__main__":
    main()
