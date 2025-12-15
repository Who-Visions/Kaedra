"""
KAEDRA v0.0.6 - Custom Exceptions
Structured error handling for better debugging and recovery.
"""


class KaedraError(Exception):
    """Base exception for all KAEDRA errors."""
    
    def __init__(self, message: str, code: str = "KAEDRA_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class AgentError(KaedraError):
    """Error in agent execution."""
    
    def __init__(self, message: str, agent: str, details: dict = None):
        super().__init__(
            message=message,
            code=f"AGENT_{agent.upper()}_ERROR",
            details={"agent": agent, **(details or {})}
        )


class ServiceError(KaedraError):
    """Error in a service."""
    
    def __init__(self, message: str, service: str, details: dict = None):
        super().__init__(
            message=message,
            code=f"SERVICE_{service.upper()}_ERROR",
            details={"service": service, **(details or {})}
        )


class PromptError(ServiceError):
    """Error in prompt generation or LLM call."""
    
    def __init__(self, message: str, model: str = None, details: dict = None):
        super().__init__(
            message=message,
            service="prompt",
            details={"model": model, **(details or {})}
        )


class MemoryError(ServiceError):
    """Error in memory operations."""
    
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(
            message=message,
            service="memory",
            details={"operation": operation, **(details or {})}
        )


class ConfigError(KaedraError):
    """Configuration error."""
    
    def __init__(self, message: str, key: str = None, details: dict = None):
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            details={"key": key, **(details or {})}
        )


class NotionError(ServiceError):
    """Error in Notion integration."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            service="notion",
            details=details
        )


class StrategyError(KaedraError):
    """Error in prompt strategy execution."""
    
    def __init__(self, message: str, strategy: str, details: dict = None):
        super().__init__(
            message=message,
            code=f"STRATEGY_{strategy.upper()}_ERROR",
            details={"strategy": strategy, **(details or {})}
        )


class RateLimitError(PromptError):
    """Rate limit exceeded on LLM API."""
    
    def __init__(self, model: str, retry_after: int = None):
        super().__init__(
            message=f"Rate limit exceeded for model {model}",
            model=model,
            details={"retry_after_seconds": retry_after}
        )


class AuthenticationError(KaedraError):
    """Authentication failed."""
    
    def __init__(self, message: str, service: str = "vertex"):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            details={"service": service}
        )
