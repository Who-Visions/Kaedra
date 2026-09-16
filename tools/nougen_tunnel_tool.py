#!/usr/bin/env python3
"""Kaedra & Fleet Tool: NouGen Ngrok Tunnel Bridge.

Spins up an authenticated Ngrok edge tunnel for any local port and prints
a structured JSON payload or human banner with the public TLS endpoint.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add nougenshards to path
venv_pkg = Path.home() / "The Observatory" / "NouGen" / "nougenshards" / "src"
if venv_pkg.exists():
    sys.path.insert(0, str(venv_pkg))

try:
    from nougen_shards import tunnel
except ImportError:
    print(json.dumps({"status": "error", "error": "nougen_shards.tunnel module not found"}))
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="NouGen Ngrok Edge Tunnel Tool")
    parser.add_argument("port", type=int, help="Port to forward")
    parser.add_argument("--service", default="generic", help="Service name")
    parser.add_argument("--domain", default=None, help="Custom Ngrok domain")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    try:
        res = tunnel.start_tunnel(
            port=args.port,
            service_name=args.service,
            domain=args.domain
        )
        if args.json:
            print(json.dumps({
                "status": "online",
                "url": res["url"],
                "port": res["port"],
                "service": res["service"],
                "domain": res["domain"]
            }, indent=2))
        else:
            print("=" * 70)
            print(f"🚇 NOUGEN EDGE TUNNEL ACTIVE [{res['service'].upper()}]")
            print(f"• Forwarding:  http://localhost:{res['port']} -> {res['url']}")
            print(f"• Ingress:     Ngrok Authenticated Edge")
            print("=" * 70)

        # Loop to maintain tunnel
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if not args.json:
            print("\nTunnel closed.")
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}))
        else:
            print(f"❌ Error starting tunnel: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
