#!/usr/bin/env python3
"""
KAEDRA v0.0.6 - Quick Launch Script
Run with: python run.py

Uses Rich CLI by default, falls back to standard CLI if Rich unavailable.
"""

# Try Rich CLI first, fallback to standard
try:
    from kaedra.interface.rich_cli import main
except ImportError:
    from kaedra.interface.cli import main

if __name__ == "__main__":
    main()
