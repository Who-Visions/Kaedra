"""
KAEDRA Comprehensive Stress Test - 50 Turns
Tests: Gemini API → Tools (Invoice, Wispr) → Agent Response
Features: 429 Rate Limit Handling (Exponential Backoff), Latency Tracking, Effectiveness Metrics.
"""

import os
import sys
import time
import asyncio
import json
import random
import re
import statistics
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Set up paths
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types
from google.api_core import exceptions

# Kaedra Imports
from kaedra.core.config import PROJECT_ID
from kaedra.agents.kaedra import KAEDRA_PROFILE
from kaedra.tools.invoices import invoice_action
from kaedra.tools.wispr import get_flow_context

# Config
TURNS = 50
MODEL = "gemini-3-flash-preview"  # Use project standard model
CLIENT = genai.Client(vertexai=True, project=PROJECT_ID, location="global") # Preview models require global

# System Prompt including all tools
SYSTEM_PROMPT = KAEDRA_PROFILE + """
[AVAILABLE TOOLS]

1. INVOICE TOOL: To manage invoices (Stripe + Square)
   Output format: [TOOL: invoice_action(action="...", provider="...", ...)]
   Actions: list, revenue, status, generate
   Providers: stripe, square, both

2. WISPR TOOL: To access dictation history/context
   Output format: [TOOL: get_flow_context(action="...", query="...", limit=5)]
   Actions: recent, search

ALWAYS use these tools when the user asks about payments, revenue, status, or their recent thoughts/dictations.
"""

class StressTester:
    def __init__(self):
        self.latencies = []
        self.tool_successes = 0
        self.tool_attempts = 0
        self.errors = 0
        self.results = []

    async def call_with_retry(self, chat, message, max_retries=5):
        backoff = 2
        for i in range(max_retries):
            try:
                start = time.perf_counter()
                response = await chat.send_message(message)
                latency = (time.perf_counter() - start) * 1000
                return response, latency
            except exceptions.ResourceExhausted as e:
                print(f"  [429] Rate limit hit. Retrying in {backoff}s... (Attempt {i+1}/{max_retries})")
                await asyncio.sleep(backoff)
                backoff *= 2
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {e}")
                raise e
        raise Exception("Max retries exceeded for 429 error.")

    async def run_turn(self, chat, turn_id, prompt):
        print(f"\n> Turn {turn_id+1}: \"{prompt}\"")
        
        turn_start = time.perf_counter()
        
        try:
            # Step 1: Agent Step (Initial Response / Tool Call Generation)
            response, agent_latency = await self.call_with_retry(chat, prompt)
            text = response.text if response.text else ""
            
            tool_latency = 0
            final_latency = 0
            tool_called = None
            tool_result = None
            
            # Step 2: Tool Execution if detected
            if "[TOOL:" in text:
                self.tool_attempts += 1
                tool_start = time.perf_counter()
                
                # Simple Regex Parser for our stress test
                # Detect invoice_action
                inv_match = re.search(r'\[TOOL: invoice_action\((.*?)\)\]', text)
                wis_match = re.search(r'\[TOOL: get_flow_context\((.*?)\)\]', text)
                
                try:
                    if inv_match:
                        tool_called = "invoice_action"
                        # For stress test simplicity, we execute a default 'status' or 'list' if parsing complex args fails
                        tool_result = invoice_action(action="status")
                    elif wis_match:
                        tool_called = "get_flow_context"
                        tool_result = get_flow_context(action="recent", limit=3)
                    
                    if tool_result:
                        tool_latency = (time.perf_counter() - tool_start) * 1000
                        self.tool_successes += 1
                        
                        # Step 3: Feed Tool result back to agent
                        final_response, final_latency = await self.call_with_retry(chat, f"[SYSTEM] Tool Output: {json.dumps(tool_result)}")
                        text = final_response.text if final_response.text else text
                except Exception as te:
                    print(f"  [TOOL ERR] {te}")
            
            total_turn_time = (time.perf_counter() - turn_start) * 1000
            self.latencies.append(total_turn_time)
            
            # Log turn info
            turn_data = {
                "turn": turn_id + 1,
                "prompt": prompt,
                "latency_ms": total_turn_time,
                "agent_ms": agent_latency,
                "tool_ms": tool_latency,
                "final_ms": final_latency,
                "tool_called": tool_called,
                "response_preview": text[:100].replace('\n', ' ') + "..."
            }
            self.results.append(turn_data)
            
            status = f"[{tool_called or 'CHAT'}]"
            print(f"  Result: {total_turn_time:.0f}ms {status} - {text[:80]}...")
            
        except Exception as e:
            self.errors += 1
            print(f"  [TURN FAILED] {e}")

    async def run_test(self):
        print("="*70)
        print(f"STARTING 50-TURN STRESS TEST (Model: {MODEL})")
        print("="*70)
        
        chat_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
            max_output_tokens=500
        )
        
        chat = CLIENT.aio.chats.create(model=MODEL, config=chat_config)
        
        prompts = [
            "Hi Kaedra, who are you?",
            "What's my current invoice status?",
            "Can you see my recent Wispr notes?",
            "Show me my revenue for the last 30 days.",
            "What was I talking about in my recent dictations?",
            "Check both Stripe and Square for open invoices.",
            "Tell me a bit about your persona and soul.",
            "Search my Wispr history for 'AI with Dav3'.",
            "Are my payment APIs connected and working?",
            "Give me a summary of my financial health and my recent thoughts.",
        ] * 5  # 50 turns
        
        for i, prompt in enumerate(prompts):
            await self.run_turn(chat, i, prompt)
            # Small delay to reduce immediate 429 risk
            await asyncio.sleep(0.5)

        # Final Summary
        print("\n" + "="*70)
        print("STRESS TEST COMPLETE")
        print("="*70)
        
        if self.latencies:
            avg = statistics.mean(self.latencies)
            med = statistics.median(self.latencies)
            print(f"Turns: {len(self.latencies)} / {TURNS}")
            print(f"Errors: {self.errors}")
            print(f"Tool Success: {self.tool_successes} / {self.tool_attempts}")
            print(f"Avg Latency: {avg:.0f}ms")
            print(f"Median Latency: {med:.0f}ms")
            print(f"Min/Max: {min(self.latencies):.0f}ms / {max(self.latencies):.0f}ms")
        
        # Save results
        with open("stress_test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "turns": len(self.latencies),
                    "errors": self.errors,
                    "tool_success_rate": self.tool_successes / self.tool_attempts if self.tool_attempts > 0 else 0,
                    "avg_latency": statistics.mean(self.latencies) if self.latencies else 0,
                },
                "turns": self.results
            }, f, indent=2)
        print("\nResults saved to stress_test_results.json")

if __name__ == "__main__":
    tester = StressTester()
    asyncio.run(tester.run_test())
