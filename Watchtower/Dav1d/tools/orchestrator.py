"""
Tool Orchestration via Code Execution
Enables Gemini to call tools programmatically through Python code
Similar to Claude's Programmatic Tool Calling
"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
import json
import asyncio
from io import StringIO
import sys


@dataclass
class ToolExecutionResult:
    """Result from executing a tool."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


class ToolProxy:
    """
    Proxy object that wraps a tool function.
    Allows tools to be called from code execution environment.
    """
    
    def __init__(self, name: str, function: Callable, is_async: bool = False):
        self.name = name
        self.function = function
        self.is_async = is_async
        self.call_history: List[dict] = []
    
    def __call__(self, *args, **kwargs):
        """
        Call the underlying tool function.
        Records call history for debugging.
        """
        self.call_history.append({
            "args": args,
            "kwargs": kwargs
        })
        
        try:
            if self.is_async:
                # For async tools, return awaitable
                return self.function(*args, **kwargs)
            else:
                # Sync tools execute immediately
                result = self.function(*args, **kwargs)
                return result
        except Exception as e:
            print(f"Error calling {self.name}: {e}", file=sys.stderr)
            raise


class ToolOrchestrator:
    """
    Executes Gemini-generated Python code with tool access.
    
    Key features:
    - Sandboxed execution environment
    - Tool proxies injected into namespace
    - Async/await support for parallel execution
    - Captures stdout/stderr
    - Only final result enters Gemini context
    """
    
    def __init__(self):
        self.available_tools: Dict[str, ToolProxy] = {}
        self.execution_history: List[dict] = []
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        is_async: bool = False
    ):
        """Register a tool for use in code execution."""
        proxy = ToolProxy(name, function, is_async)
        self.available_tools[name] = proxy
    
    def create_sandbox_namespace(self) -> dict:
        """
        Create a safe namespace for code execution.
        Includes standard library + tools.
        """
        import json
        import math
        import re
        import datetime
        from collections import Counter, defaultdict
        
        namespace = {
            # Standard library
            'json': json,
            'math': math,
            're': re,
            'datetime': datetime,
            'Counter': Counter,
            'defaultdict': defaultdict,
            'asyncio': asyncio,
            
            # Utilities
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'sum': sum,
            'max': max,
            'min': min,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'range': range,
        }
        
        # Add tool proxies
        for tool_name, proxy in self.available_tools.items():
            namespace[tool_name] = proxy
        
        return namespace
    
    async def execute_code(self, code: str, timeout: int = 30) -> dict:
        """
        Execute Python code in sandboxed environment.
        
        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "result": Any,
                "error": Optional[str],
                "tool_calls": List[dict]
            }
        """
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Create namespace
            namespace = self.create_sandbox_namespace()
            
            # Check if code uses async/await
            is_async_code = 'await ' in code or 'async def' in code or 'asyncio.gather' in code
            
            if is_async_code:
                # Wrap in async function and execute
                wrapped_code = f"""
async def __orchestrator_main__():
{chr(10).join('    ' + line for line in code.split(chr(10)))}

__result__ = asyncio.run(__orchestrator_main__())
"""
                exec(wrapped_code, namespace)
                result = namespace.get('__result__')
            else:
                # Sync execution
                exec(code, namespace)
                result = namespace.get('__result__')  # If code sets __result__
            
            # Collect tool call history
            tool_calls = []
            for tool_name, proxy in self.available_tools.items():
                if proxy.call_history:
                    tool_calls.append({
                        "tool": tool_name,
                        "calls": len(proxy.call_history),
                        "history": proxy.call_history
                    })
            
            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "result": result,
                "error": None,
                "tool_calls": tool_calls
            }
        
        except Exception as e:
            return {
                "success": False,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "result": None,
                "error": str(e),
                "tool_calls": []
            }
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def get_statistics(self) -> dict:
        """Get orchestrator statistics."""
        total_calls = sum(
            len(proxy.call_history) 
            for proxy in self.available_tools.values()
        )
        
        return {
            "registered_tools": len(self.available_tools),
            "total_executions": len(self.execution_history),
            "total_tool_calls": total_calls,
        }


def create_orchestration_prompt() -> str:
    """
    Generate system prompt explaining code orchestration to Gemini.
    
    Returns instructions for when to use code vs direct tool calls.
    """
    return """
You can orchestrate tools in two ways:

1. **Direct Tool Calling** (simple tasks):
   - Single tool invocation
   - No data transformation needed
   - Results should be seen immediately

2. **Code Orchestration** (complex workflows):
   - Multiple dependent tool calls
   - Data filtering/transformation needed
   - Parallel execution beneficial
   - Intermediate results not relevant

When using code orchestration:
- Write Python code that calls tools as functions
- Use asyncio.gather() for parallel calls
- Filter/transform data in code
- Only print/return final results
- Intermediate data stays in code (saves tokens!)

Example:
```python
# Fetch data in parallel
team = get_team_members('engineering')
budgets = {level: get_budget_by_level(level) 
           for level in set(m['level'] for m in team)}

# Process locally
exceeded = []
for member in team:
    expenses = get_expenses(member['id'], 'Q3')
    total = sum(e['amount'] for e in expenses)
    if total > budgets[member['level']]['limit']:
        exceeded.append({'name': member['name'], 'total': total})

# Only final results enter context
print(json.dumps(exceeded))
```

Benefits:
- 1 inference pass instead of 20+
- Only final results in context (not raw data)
- Clearer logic with explicit code
"""


# Global orchestrator instance
orchestrator = ToolOrchestrator()
