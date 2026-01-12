"""
Core Retry Policy & Circuit Breaker
Implements robust error handling with exponential backoff and jitter.
"""
import asyncio
import random
from typing import TypeVar, Callable, Any

T = TypeVar("T")

class RetryPolicy:
    """
    Circuit Breaker & Exponential Backoff Policy.
    """
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._circuit_open = False
        self._successive_failures = 0
        self._circuit_threshold = 5

    async def execute_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute an async function with retries."""
        # Check Circuit
        if self._circuit_open:
            # Simple auto-reset check? For now, just raise.
            # In a real system we'd check time elapsed.
            # Assuming external manual reset or app restart for strict safety.
            raise Exception("Circuit Breaker OPEN: High failure rate detected.")

        last_error = None
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                self._successive_failures = 0 # Reset circuit
                return result
            except Exception as e:
                last_error = e
                # Don't trip circuit on minor network glitches unless persistent

                if attempt == self.max_attempts - 1:
                    # Failed all attempts
                    self._successive_failures += 1
                    if self._successive_failures >= self._circuit_threshold:
                        self._circuit_open = True
                    break

                # Jitter Backoff
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                delay *= (0.5 + random.random()) # Jitter 0.5-1.5x
                await asyncio.sleep(delay)

        raise last_error

    def reset_circuit(self):
        self._circuit_open = False
        self._successive_failures = 0
