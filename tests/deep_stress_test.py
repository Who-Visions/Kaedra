"""
KAEDRA Deep Stress Test - Full Pipeline with Invoice Tool
Tests: Gemini API → Invoice Tool → Agent Pipeline

10 runs with latency tracking at each step.
"""

import os
import sys
import time
import asyncio
import statistics
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv()

# Set up paths
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types

print("="*70)
print("KAEDRA DEEP STRESS TEST - Full Pipeline + Invoice Tool")
print("="*70)

RUNS = 10
MODEL = "gemini-3-flash-preview"

# Initialize Gemini client with project
from kaedra.core.config import PROJECT_ID
CLIENT = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Raw Gemini API Latency
# ═══════════════════════════════════════════════════════════════════════════════

def test_gemini_latency(runs=RUNS):
    print(f"\n{'='*50}")
    print(f"TEST 1: Gemini 3 Flash API ({runs} runs)")
    print('='*50)
    
    latencies = []
    
    prompts = [
        "What's 2+2?",
        "Say hello",
        "Name a color",
        "What's the capital of France?",
        "Count to 3",
        "What's your name?",
        "How are you?",
        "What day is it?",
        "Give me a one word response: happy or sad?",
        "Yes or no: is the sky blue?"
    ]
    
    for i in range(runs):
        prompt = prompts[i % len(prompts)]
        start = time.perf_counter()
        try:
            response = CLIENT.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=50
                )
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            text = response.text[:30].replace('\n', ' ') if response.text else "empty"
            print(f"  Run {i+1}: {latency:.0f}ms - \"{text}...\"")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            print(f"  Run {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\n  Results: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms, median={statistics.median(latencies):.0f}ms")
    
    return latencies


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Conversational Chat (Multi-turn)
# ═══════════════════════════════════════════════════════════════════════════════

async def test_chat_latency(runs=RUNS):
    print(f"\n{'='*50}")
    print(f"TEST 2: Gemini Chat Session ({runs} turns)")
    print('='*50)
    
    chat_config = types.GenerateContentConfig(
        system_instruction="You are a helpful assistant. Be brief.",
        temperature=1.0,
        max_output_tokens=100
    )
    
    chat = CLIENT.aio.chats.create(model=MODEL, config=chat_config)
    
    latencies = []
    messages = [
        "Hello!",
        "What's your favorite color?",
        "Tell me a joke",
        "What's 10 times 10?",
        "Say something funny",
        "What's the weather like?",
        "Give me advice",
        "Tell me a fact",
        "What should I do today?",
        "Goodbye!"
    ]
    
    for i in range(runs):
        msg = messages[i % len(messages)]
        start = time.perf_counter()
        try:
            response = await chat.send_message(msg)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            text = response.text[:40].replace('\n', ' ') if response.text else "empty"
            print(f"  Turn {i+1}: {latency:.0f}ms - \"{text}...\"")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            print(f"  Turn {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\n  Results: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms, median={statistics.median(latencies):.0f}ms")
    
    return latencies


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Invoice Tool Execution
# ═══════════════════════════════════════════════════════════════════════════════

def test_invoice_tool(runs=RUNS):
    print(f"\n{'='*50}")
    print(f"TEST 3: Invoice Tool Direct ({runs} runs)")
    print('='*50)
    
    from kaedra.tools.invoices import invoice_action
    
    latencies = []
    actions = [
        ("status", {}),
        ("list", {"provider": "stripe", "limit": 5}),
        ("list", {"provider": "square", "limit": 5}),
        ("revenue", {"provider": "stripe", "days": 30}),
        ("revenue", {"provider": "square", "days": 30}),
        ("status", {}),
        ("list", {"provider": "both", "limit": 3}),
        ("revenue", {"provider": "both", "days": 7}),
        ("status", {}),
        ("generate", {"customer_name": "Test", "customer_email": "test@test.com", "items": [{"description": "Item", "amount": 100}]})
    ]
    
    for i in range(runs):
        action, kwargs = actions[i % len(actions)]
        start = time.perf_counter()
        try:
            result = invoice_action(action=action, **kwargs)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            status = "OK" if "error" not in result else f"ERR: {result['error'][:30]}"
            print(f"  Run {i+1}: {latency:.0f}ms - {action} → {status}")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            print(f"  Run {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\n  Results: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms, median={statistics.median(latencies):.0f}ms")
    
    return latencies


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4: Kaedra Agent with Invoice Prompt
# ═══════════════════════════════════════════════════════════════════════════════

async def test_kaedra_invoice_pipeline(runs=RUNS):
    print(f"\n{'='*50}")
    print(f"TEST 4: Kaedra Agent + Invoice Tool ({runs} runs)")
    print('='*50)
    
    from kaedra.agents.kaedra import KAEDRA_PROFILE
    
    # Full Kaedra system prompt with invoice tool
    system_prompt = KAEDRA_PROFILE + """
[INVOICE TOOL]
To manage invoices (Stripe + Square), output:
[TOOL: invoice_action(action="list", provider="both", status="open")]
[TOOL: invoice_action(action="revenue", provider="both", days=30)]
[TOOL: invoice_action(action="status")]

Actions: list, get, create, send, revenue, search, status, generate
Providers: stripe, square, both
"""
    
    chat_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=1.0,
        max_output_tokens=200
    )
    
    chat = CLIENT.aio.chats.create(model=MODEL, config=chat_config)
    
    latencies = []
    prompts = [
        "What's my invoice status?",
        "Show me my revenue",
        "Check my Stripe connection",
        "How much did I make this week?",
        "List my open invoices",
        "Check payment status",
        "What's the invoice situation?",
        "Revenue report please",
        "Are my payment APIs connected?",
        "Show me Square invoices"
    ]
    
    for i in range(runs):
        prompt = prompts[i % len(prompts)]
        start = time.perf_counter()
        try:
            response = await chat.send_message(prompt)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            
            # Check if tool was invoked
            text = response.text if response.text else ""
            has_tool = "[TOOL:" in text
            tool_status = "TOOL" if has_tool else "CHAT"
            preview = text[:40].replace('\n', ' ')
            print(f"  Run {i+1}: {latency:.0f}ms [{tool_status}] - \"{preview}...\"")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            print(f"  Run {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\n  Results: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms, median={statistics.median(latencies):.0f}ms")
    
    return latencies


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5: Full Pipeline (Agent + Tool Execution)
# ═══════════════════════════════════════════════════════════════════════════════

async def test_full_pipeline(runs=5):
    print(f"\n{'='*50}")
    print(f"TEST 5: Full Pipeline: Agent → Tool → Response ({runs} runs)")
    print('='*50)
    
    from kaedra.agents.kaedra import KAEDRA_PROFILE
    from kaedra.tools.invoices import invoice_action
    import re
    import json
    
    system_prompt = KAEDRA_PROFILE + """
[INVOICE TOOL - ALWAYS USE]
When asked about invoices/revenue/payments, ALWAYS output:
[TOOL: invoice_action(action="status")]
"""
    
    chat_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=1.0,
        max_output_tokens=300
    )
    
    latencies = []
    
    for i in range(runs):
        chat = CLIENT.aio.chats.create(model=MODEL, config=chat_config)
        
        overall_start = time.perf_counter()
        
        # Step 1: Agent generates tool call
        step1_start = time.perf_counter()
        response = await chat.send_message("Check my invoice connection status")
        step1_time = (time.perf_counter() - step1_start) * 1000
        
        text = response.text if response.text else ""
        
        # Step 2: Execute tool if present
        step2_time = 0
        tool_result = None
        if "[TOOL:" in text:
            step2_start = time.perf_counter()
            # Parse and execute
            match = re.search(r'\[TOOL: invoice_action\((.*?)\)\]', text)
            if match:
                try:
                    tool_result = invoice_action(action="status")
                    step2_time = (time.perf_counter() - step2_start) * 1000
                except Exception as e:
                    tool_result = {"error": str(e)}
                    step2_time = (time.perf_counter() - step2_start) * 1000
        
        # Step 3: Agent responds with tool output
        step3_time = 0
        if tool_result:
            step3_start = time.perf_counter()
            final = await chat.send_message(f"[SYSTEM] Tool Output: {json.dumps(tool_result)}")
            step3_time = (time.perf_counter() - step3_start) * 1000
        
        total_time = (time.perf_counter() - overall_start) * 1000
        latencies.append(total_time)
        
        print(f"  Run {i+1}: {total_time:.0f}ms total (Agent: {step1_time:.0f}ms, Tool: {step2_time:.0f}ms, Response: {step3_time:.0f}ms)")
    
    if latencies:
        print(f"\n  Results: min={min(latencies):.0f}ms, max={max(latencies):.0f}ms, avg={statistics.mean(latencies):.0f}ms")
    
    return latencies


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    all_results = {}
    
    # Test 1
    all_results["gemini_raw"] = test_gemini_latency()
    
    # Test 2
    all_results["gemini_chat"] = await test_chat_latency()
    
    # Test 3
    all_results["invoice_tool"] = test_invoice_tool()
    
    # Test 4
    all_results["kaedra_prompt"] = await test_kaedra_invoice_pipeline()
    
    # Test 5
    all_results["full_pipeline"] = await test_full_pipeline()
    
    # Summary
    print(f"\n{'='*70}")
    print("DEEP STRESS TEST SUMMARY")
    print('='*70)
    
    for name, latencies in all_results.items():
        if latencies:
            avg = statistics.mean(latencies)
            med = statistics.median(latencies)
            print(f"  {name:20s}: avg={avg:6.0f}ms, median={med:6.0f}ms, n={len(latencies)}")
        else:
            print(f"  {name:20s}: NO DATA")
    
    # Overall assessment
    print(f"\n{'='*70}")
    print("PERFORMANCE ASSESSMENT")
    print('='*70)
    
    if all_results.get("gemini_raw"):
        gemini_avg = statistics.mean(all_results["gemini_raw"])
        if gemini_avg < 500:
            print("✓ Gemini API: FAST")
        elif gemini_avg < 1000:
            print("⚠ Gemini API: MODERATE")
        else:
            print("✗ Gemini API: SLOW")
    
    if all_results.get("invoice_tool"):
        tool_avg = statistics.mean(all_results["invoice_tool"])
        if tool_avg < 300:
            print("✓ Invoice Tool: FAST")
        elif tool_avg < 600:
            print("⚠ Invoice Tool: MODERATE")
        else:
            print("✗ Invoice Tool: SLOW - consider caching")
    
    if all_results.get("full_pipeline"):
        pipe_avg = statistics.mean(all_results["full_pipeline"])
        if pipe_avg < 2000:
            print("✓ Full Pipeline: ACCEPTABLE for voice (<2s)")
        elif pipe_avg < 4000:
            print("⚠ Full Pipeline: BORDERLINE for voice (2-4s)")
        else:
            print("✗ Full Pipeline: TOO SLOW for voice (>4s)")
    
    print("\nDeep stress test complete! ✓")


if __name__ == "__main__":
    asyncio.run(main())
