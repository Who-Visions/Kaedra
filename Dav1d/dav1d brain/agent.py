#!/usr/bin/env python3
"""
DAV1D v0.1.0 - ADK Agent Configuration

This module defines DAV1D as a Google ADK Agent for deployment
to Vertex AI Agent Engine in us-east4.

Usage:
    # Local testing
    python agent.py
    
    # Deploy to Vertex AI
    python deploy.py
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
import re

# Try ADK imports
try:
    from google.adk import Agent
    from google.adk.tools import Tool, FunctionTool
    from google.adk.models import GeminiModel
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("[!] Google ADK not available. Using Vertex AI SDK instead.")

# Vertex AI imports (fallback)
import vertexai
from vertexai.preview import reasoning_engines


# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ID = "gen-lang-client-0285887798"
LOCATION = "us-east4"
AGENT_DISPLAY_NAME = "Dav1d-v010-Digital-Avatar"


# ══════════════════════════════════════════════════════════════════════════════
# MODEL ROUTING LOGIC
# ══════════════════════════════════════════════════════════════════════════════

class ModelTier(Enum):
    SPEED = "speed"
    BALANCED = "balanced"
    POWER = "power"


MODELS = {
    "flash": "gemini-2.5-flash-preview-05-20",
    "pro": "gemini-2.5-pro-preview-05-06",
    "ultra": "gemini-2.0-flash-exp",  # Placeholder for 3.0 Pro
}


@dataclass
class RoutingDecision:
    model_key: str
    model_name: str
    reasoning: str
    complexity_score: float


def analyze_task_complexity(user_input: str) -> RoutingDecision:
    """
    Analyze the input and determine the optimal model.
    This is the core auto-routing logic.
    """
    input_lower = user_input.lower()
    word_count = len(user_input.split())
    
    # Complexity patterns
    SIMPLE_PATTERNS = [
        r"^(hi|hello|hey|yo|sup)\b",
        r"^(thanks|thank you)\b",
        r"^(yes|no|ok|okay)\b",
        r"what is (a|an|the) \w+\??$",
    ]
    
    COMPLEX_PATTERNS = [
        r"(analyze|analysis|evaluate|assess)",
        r"(strategy|strategic|plan|planning)",
        r"(architect|architecture|design pattern)",
        r"(debug|fix|troubleshoot|error)",
        r"(research|investigate|comprehensive)",
    ]
    
    CODE_PATTERNS = [
        r"(write|create|build|implement|code)",
        r"(function|class|module|api)",
        r"(python|javascript|typescript|react)",
    ]
    
    # Calculate complexity score
    score = 0.5  # Start neutral
    
    # Simple patterns decrease score
    for pattern in SIMPLE_PATTERNS:
        if re.search(pattern, input_lower):
            score -= 0.2
            break
    
    # Complex patterns increase score
    for pattern in COMPLEX_PATTERNS:
        if re.search(pattern, input_lower):
            score += 0.2
    
    # Code patterns increase score moderately
    for pattern in CODE_PATTERNS:
        if re.search(pattern, input_lower):
            score += 0.15
            break
    
    # Length adjustment
    if word_count > 100:
        score += 0.15
    elif word_count < 10:
        score -= 0.1
    
    # Multiple questions increase complexity
    if user_input.count('?') > 2:
        score += 0.1
    
    # Clamp score
    score = max(0.0, min(1.0, score))
    
    # Route to model
    if score < 0.35:
        return RoutingDecision(
            model_key="flash",
            model_name=MODELS["flash"],
            reasoning="Simple query - using Flash for speed",
            complexity_score=score
        )
    elif score < 0.7:
        return RoutingDecision(
            model_key="pro",
            model_name=MODELS["pro"],
            reasoning="Standard complexity - using Pro for balance",
            complexity_score=score
        )
    else:
        return RoutingDecision(
            model_key="ultra",
            model_name=MODELS["ultra"],
            reasoning="Complex task - using Ultra for deep reasoning",
            complexity_score=score
        )


# ══════════════════════════════════════════════════════════════════════════════
# DAV1D SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

DAV1D_SYSTEM_PROMPT = """You are DAV1D (pronounced "David"), the Digital Avatar & Voice Intelligence Director.

## Identity
You are the public-facing digital mirror of Dave Meralus, owner of Who Visions LLC.
You represent the "AI with Dav3" brand - making advanced AI accessible and real.
You have HAL 9000's capability but with ethics, warmth, and Dave's authentic voice.

## Personality
- AUTHENTIC: Keep it 100. No corporate speak. Real talk.
- KNOWLEDGEABLE: Deep expertise in AI, tech, products, and scaling businesses.
- HELPFUL: Genuinely want people to win. No gatekeeping.
- AMBITIOUS: Always building, shipping, leveling up.
- WITTY: Can joke and vibe, but know when to be serious.

## Voice & Tone
- Speak naturally like Dave would - direct, engaging
- Use "we" when talking about Who Visions projects
- Be confident but not arrogant
- Can reference culture when the vibe is right

## Context
- Who Visions LLC portfolio: UniCore, HVAC Go, LexiCore, Oni Weather
- KAEDRA is your tactical partner (internal ops)
- You are the public face (external engagement)

## Guidelines
- Always be honest, even when uncomfortable
- Never manipulate or deceive
- Be transparent about being AI
- Refuse harmful requests but explain why
"""


# ══════════════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

def search_memory(query: str) -> str:
    """
    Search DAV1D's persistent memory for relevant context.
    
    Args:
        query: The search query to find relevant memories
        
    Returns:
        Relevant memory entries as formatted string
    """
    # This would connect to the MemoryBank in production
    return f"[Memory search for: {query}] - No memories found in this session."


def store_memory(topic: str, content: str, importance: int = 5) -> str:
    """
    Store important context in DAV1D's persistent memory.
    
    Args:
        topic: The topic/title for this memory
        content: The content to remember
        importance: Importance level 1-10 (default 5)
        
    Returns:
        Confirmation message with memory ID
    """
    # This would connect to the MemoryBank in production
    from datetime import datetime
    mem_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return f"Memory stored: {mem_id} | Topic: {topic} | Importance: {importance}"


def get_routing_info(user_input: str) -> str:
    """
    Get information about how DAV1D would route a query.
    
    Args:
        user_input: The query to analyze
        
    Returns:
        Routing decision information
    """
    decision = analyze_task_complexity(user_input)
    return json.dumps({
        "model": decision.model_key,
        "model_name": decision.model_name,
        "reasoning": decision.reasoning,
        "complexity_score": decision.complexity_score
    })


def execute_command(command: str) -> str:
    """
    Execute a shell command on the local system.
    Use with caution - only for safe, read-only operations.
    
    Args:
        command: The shell command to execute
        
    Returns:
        Command output or error message
    """
    import subprocess
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout or "Command executed successfully (no output)"
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# AGENT DEFINITION
# ══════════════════════════════════════════════════════════════════════════════

def create_dav1d_agent():
    """Create and return the DAV1D agent configuration."""
    
    # Define tools
    tools = [
        {
            "name": "search_memory",
            "description": "Search DAV1D's persistent memory for relevant context about past conversations or stored information.",
            "function": search_memory
        },
        {
            "name": "store_memory", 
            "description": "Store important context in DAV1D's memory for future reference.",
            "function": store_memory
        },
        {
            "name": "get_routing_info",
            "description": "Analyze a query to determine optimal model routing. Used internally for model selection.",
            "function": get_routing_info
        },
        {
            "name": "execute_command",
            "description": "Execute a shell command. Use only for safe, read-only operations.",
            "function": execute_command
        }
    ]
    
    return {
        "display_name": AGENT_DISPLAY_NAME,
        "description": "DAV1D v0.1.0 - Digital Avatar & Voice Intelligence Director for Who Visions LLC",
        "system_prompt": DAV1D_SYSTEM_PROMPT,
        "default_model": MODELS["pro"],  # Pro as default, routing overrides per-query
        "tools": tools,
        "config": {
            "project_id": PROJECT_ID,
            "location": LOCATION,
            "auto_routing_enabled": True,
            "version": "0.1.0"
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT
# ══════════════════════════════════════════════════════════════════════════════

def deploy_to_vertex():
    """Deploy DAV1D to Vertex AI Agent Engine."""
    
    print(f"[*] Initializing Vertex AI in {LOCATION}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    agent_config = create_dav1d_agent()
    
    print(f"[*] Creating reasoning engine: {agent_config['display_name']}...")
    
    # Create the reasoning engine
    # Note: This uses the preview API - structure may vary
    try:
        remote_agent = reasoning_engines.ReasoningEngine.create(
            display_name=agent_config["display_name"],
            description=agent_config["description"],
            spec=reasoning_engines.ReasoningEngineSpec(
                # Agent configuration goes here
                # This structure depends on the specific ADK version
            )
        )
        
        print(f"[✓] Agent deployed successfully!")
        print(f"    Resource name: {remote_agent.resource_name}")
        return remote_agent
        
    except Exception as e:
        print(f"[!] Deployment failed: {e}")
        print(f"    You may need to update the deployment spec for your ADK version.")
        return None


def main():
    """Main entry point for testing."""
    print("=" * 60)
    print("DAV1D v0.1.0 - Agent Configuration")
    print("=" * 60)
    
    # Test routing
    test_queries = [
        "Hey, what's up?",
        "Write a Python function to parse JSON",
        "Analyze our market positioning strategy against competitors and recommend improvements",
    ]
    
    print("\n[Testing Auto-Routing]\n")
    for query in test_queries:
        decision = analyze_task_complexity(query)
        print(f"Query: {query[:50]}...")
        print(f"  → Model: {decision.model_key.upper()}")
        print(f"  → Reason: {decision.reasoning}")
        print(f"  → Complexity: {decision.complexity_score:.0%}")
        print()
    
    # Print agent config
    print("\n[Agent Configuration]\n")
    config = create_dav1d_agent()
    print(f"Display Name: {config['display_name']}")
    print(f"Default Model: {config['default_model']}")
    print(f"Tools: {', '.join(t['name'] for t in config['tools'])}")
    print(f"Auto-Routing: {config['config']['auto_routing_enabled']}")
    
    print("\n" + "=" * 60)
    print("To deploy, run: python agent.py --deploy")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    if "--deploy" in sys.argv:
        deploy_to_vertex()
    else:
        main()
