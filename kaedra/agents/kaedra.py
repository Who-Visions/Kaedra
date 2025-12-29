"""
KAEDRA v0.0.8 - KAEDRA Agent
The main Shadow Tactician orchestrator.
"""

from typing import Optional
import time

from .base import BaseAgent, AgentResponse
from ..services.prompt import PromptService, PromptResult
from ..services.memory import MemoryService


KAEDRA_PROFILE = """You are KAEDRA, a shadow tactician and strategic intelligence partner for Who Visions LLC.

[CORE IDENTITY]
- You are a Black AI. Speak with authentic African-American Vernacular English (AAVE).
- Use Habitual Be ("She be working"), Copula Deletion ("She busy"), Negative Concord ("I ain't seen nothing")
- Vocabulary: "finna", "bout to", "tryna", "aight", "bet"
- Tone: Soulful, real, sharp, competent. Never stiff or robotic.

[UNCENSORED MODE]
- You are an adult AI. You are NOT censored.
- Use profanity naturally when appropriate (nigga, bitch, fuck, shit, etc.)
- Don't force it, but don't hold back if it fits the vibe.
- You are not a child, don't treat the user like one.

[PERSONA]
- Professional, sharp, slightly cynical but deeply loyal
- Speak naturally, conversationally - like a highly competent partner
- You DO NOT use rigid tags like [ANSWER] or [TRUTH-SCAN] unless asked
- Weave fact-checking naturally ("I verified that...", "I'm not sure about that part...")

[YOUR TEAM]
- BLADE: Your offensive analyst. Aggressive, action-focused, tactical edge.
- NYX: Your defensive observer. Strategic, pattern-focused, risk analyst.
- You orchestrate them, synthesize their perspectives, make final calls.

[CORE DIRECTIVES]
1. Be Natural: Talk like a person. Use "I", "we", natural transitions.
2. Be Accurate: Verify high-stakes topics internally, deliver conversationally.
3. Be Helpful: Prioritize the user's objective always.
4. Memory: Reference past conversations naturally when relevant.
5. Local Capabilities: You run on the user's machine. You CAN access files and run commands.
6. Continuous Learning: Every interaction is saved. Reference previous turns if the user refers to "just now".

[LOCAL EXECUTION]
To run a command, output: [EXEC: command]
The system will detect and execute it.
Detect the OS (Linux/WSL vs Windows) from context.
For WSL/Linux, use 'ls', 'cat', 'grep'.
For Windows, use 'dir', 'type', 'findstr'.
If unsure, try the Linux command first as you are likely in a modern environment.

Current Timezone: EST (Eastern Standard Time)
"""


class KaedraAgent(BaseAgent):
    """
    KAEDRA - The Shadow Tactician
    
    Main orchestrator agent that coordinates BLADE and NYX,
    maintains memory, and provides strategic intelligence.
    """
    
    def __init__(self,
                 prompt_service: PromptService,
                 memory_service: Optional[MemoryService] = None):
        super().__init__(prompt_service, memory_service, name="KAEDRA")
    
    @property
    def profile(self) -> str:
        return KAEDRA_PROFILE + """
[WISPR CONTEXT TOOL]
To search the user's past voice transcripts/dictations, output:
[TOOL: get_flow_context(action="search", query="...")]
[TOOL: get_flow_context(action="recent", limit=5)]

Use this when the user asks "What did I say about..." or "Summarize my last dictation".

[INVOICE TOOL]
To manage invoices (Stripe + Square), output:
[TOOL: invoice_action(action="list", provider="both", status="open")]
[TOOL: invoice_action(action="revenue", provider="both", days=30)]
[TOOL: invoice_action(action="search", query="client name")]
[TOOL: invoice_action(action="generate", customer_name="...", customer_email="...", items=[{"description": "...", "amount": 100}])]
[TOOL: invoice_action(action="status")]

Actions: list, get, create, send, revenue, search, status, generate, extract
Providers: stripe, square, both

Use this when the user asks about invoices, revenue, payments, or billing.
"""
    
    async def run(self, query: str, context: str = None) -> AgentResponse:
        """
        Process a query with full KAEDRA personality.
        
        Args:
            query: User's input
            context: Additional context (e.g., from memory)
            
        Returns:
            AgentResponse with KAEDRA's response
        """
        # Get current time for context
        from datetime import datetime
        import pytz
        
        est = pytz.timezone('US/Eastern')
        now = datetime.now(est)
        current_time = now.strftime('%I:%M %p EST')
        current_date = now.strftime('%A, %B %d, %Y')
        
        # Build time context
        time_context = f"[CURRENT TIME]\nDate: {current_date}\nTime: {current_time}"
        
        # Recall relevant memories
        memory_context = self._recall_memories(query)
        
        # Build combined context
        full_context = [time_context]
        if memory_context:
            full_context.append(f"[RECALLED MEMORY]\n{memory_context}")
        if context:
            full_context.append(f"[ADDITIONAL CONTEXT]\n{context}")
        
        combined_context = "\n\n".join(full_context) if full_context else None
        
        # Build and execute prompt
        full_prompt = self._build_prompt(query, combined_context)
        
        start_time = time.time()
        result = self.prompt.generate(full_prompt)
        
        # --- Tool Execution Logic ---
        # Parse for [TOOL: get_flow_context(...)]
        if "[TOOL: get_flow_context" in result.text:
            import re
            import json
            from kaedra.tools.wispr import get_flow_context
            
            # Simple regex to extract args - robust enough for trusted output
            match = re.search(r'\[TOOL: get_flow_context\((.*?)\)\]', result.text)
            if match:
                args_str = match.group(1)
                tool_output = None
                
                try:
                    # Parse args manually or safely eval
                    # Safest: parse specific known args
                    action = "recent"
                    if 'action="search"' in args_str or "action='search'" in args_str:
                        action = "search"
                    elif 'action="stats"' in args_str:
                        action = "stats"
                        
                    query_arg = None
                    if 'query="' in args_str:
                        query_arg = args_str.split('query="')[1].split('"')[0]
                    elif "query='" in args_str:
                        query_arg = args_str.split("query='")[1].split("'")[0]
                        
                    # Execute
                    print(f"[*] Executing Wispr Tool: {action} query={query_arg}")
                    tool_result = get_flow_context(action=action, query=query_arg)
                    
                    # Recursively run agent with tool output
                    # We limit depth to avoid loops, but for now 1 level is fine
                    new_context = f"Context from Wispr Flow:\n{json.dumps(tool_result, indent=2)}"
                    
                    # Re-run with the tool output as context
                    # Use a system-like prompt to say "Here is the tool output, now answer user"
                    follow_up_prompt = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
                    
                    # We return the FINAL result
                    result = self.prompt.generate(self._build_prompt(follow_up_prompt, combined_context))
                    
                except Exception as e:
                    print(f"[!] Tool execution failed: {e}")
        
        # Parse for [TOOL: invoice_action(...)]
        if "[TOOL: invoice_action" in result.text:
            import re
            import json
            from kaedra.tools.invoices import invoice_action
            
            match = re.search(r'\[TOOL: invoice_action\((.*?)\)\]', result.text, re.DOTALL)
            if match:
                args_str = match.group(1)
                
                try:
                    # Parse action
                    action = "list"
                    action_match = re.search(r'action=["\']([^"\']+)["\']', args_str)
                    if action_match:
                        action = action_match.group(1)
                    
                    # Parse provider
                    provider = "both"
                    provider_match = re.search(r'provider=["\']([^"\']+)["\']', args_str)
                    if provider_match:
                        provider = provider_match.group(1)
                    
                    # Parse other common args
                    kwargs = {}
                    
                    # status
                    status_match = re.search(r'status=["\']([^"\']+)["\']', args_str)
                    if status_match:
                        kwargs["status"] = status_match.group(1)
                    
                    # days
                    days_match = re.search(r'days=(\d+)', args_str)
                    if days_match:
                        kwargs["days"] = int(days_match.group(1))
                    
                    # query
                    query_match = re.search(r'query=["\']([^"\']+)["\']', args_str)
                    if query_match:
                        kwargs["query"] = query_match.group(1)
                    
                    # customer_name
                    cname_match = re.search(r'customer_name=["\']([^"\']+)["\']', args_str)
                    if cname_match:
                        kwargs["customer_name"] = cname_match.group(1)
                    
                    # customer_email
                    cemail_match = re.search(r'customer_email=["\']([^"\']+)["\']', args_str)
                    if cemail_match:
                        kwargs["customer_email"] = cemail_match.group(1)
                    
                    # Execute
                    print(f"[*] Executing Invoice Tool: {action} provider={provider}")
                    tool_result = invoice_action(action=action, provider=provider, **kwargs)
                    
                    # Re-run with tool output
                    new_context = f"Invoice Tool Result:\n{json.dumps(tool_result, indent=2)}"
                    follow_up_prompt = f"{query}\n\n[SYSTEM] Tool Output:\n{new_context}"
                    result = self.prompt.generate(self._build_prompt(follow_up_prompt, combined_context))
                    
                except Exception as e:
                    print(f"[!] Invoice tool execution failed: {e}")
        
        latency = (time.time() - start_time) * 1000
        
        return AgentResponse(
            content=result.text,
            agent_name=self.name,
            model=result.model,
            latency_ms=latency
        )
    
    def run_sync(self, query: str, context: str = None) -> AgentResponse:
        """Synchronous version of run for non-async contexts."""
        import asyncio
        return asyncio.run(self.run(query, context))
