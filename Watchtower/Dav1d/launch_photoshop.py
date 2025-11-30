import os
import subprocess
import sys

def launch_photoshop():
    # DEEP RESEARCH: Common installation paths for Adobe Photoshop
    potential_paths = [
        r"C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2023\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2022\Photoshop.exe",
        r"C:\Program Files\Adobe\Adobe Photoshop 2021\Photoshop.exe",
    ]

    target_path = None
    print(f"[*] DAV1D System: Scanning for Photoshop executable...")

    for path in potential_paths:
        if os.path.exists(path):
            target_path = path
            break

    if target_path:
        print(f"[*] Target acquired: {target_path}")
        print("[*] Executing launch sequence...")
        try:
            # Detach process so it doesn't close when the script ends
            if sys.platform == 'win32':
                subprocess.Popen([target_path], close_fds=True)
            else:
                # Fallback for testing/non-windows (though Photoshop is Windows/Mac)
                print(f"[!] Detected non-Windows OS: {sys.platform}. Cannot launch .exe directly.")
            print("[*] Photoshop launch initiated successfully.")
        except Exception as e:
            print(f"[!] Execution failed: {e}")
    else:
        print("[!] Error: Photoshop executable not found in standard directories.")

if __name__ == "__main__":
    launch_photoshop()
