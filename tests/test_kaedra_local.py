"""
Test Kaedra Locally Before Deploying
Verifies that the Kaedra query logic works.
"""

import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0939852539"

# Import the Kaedra class
from deploy_reasoning_engine import Kaedra

print("[*] Testing Kaedra locally...")
print()

# Create instance
kaedra = Kaedra()

# Test query
response = kaedra.query("Yo, gimme a quick status check. You online?")

print("[Response]")
print(response['response'])
print()
print(f"[Metadata] Agent: {response['agent']}, Model: {response['model']}, Latency: {response['latency_ms']}ms")
