
import sys
try:
    from playwright.sync_api import sync_playwright
    print("Playwright imported successfully!")
except ImportError as e:
    print(f"Playwright import failed: {e}")
    sys.exit(1)
