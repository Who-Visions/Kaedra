import time
from collections import deque
from config import (
    MODEL_COSTS, TOOL_COSTS, Colors, 
    HOURLY_BUDGET, WINDOW_SIZE_SECONDS,
    GEMINI_CREDIT_REMAINING, MONTHLY_CREDIT_REMAINING, APP_BUILDER_CREDIT_REMAINING
)


# Rate Limits (Default to Tier 1 for safety)
RATE_LIMITS = {
    "gemini-2.5-pro": {"rpm": 2, "tpm": 125000, "rpd": 50},
    "gemini-2.5-flash": {"rpm": 10, "tpm": 250000, "rpd": 250},
    "gemini-3-pro-preview": {"rpm": 2, "tpm": 32000, "rpd": 50}, # Conservative estimate for preview
    "default": {"rpm": 5, "tpm": 32000, "rpd": 50}
}

class RateLimitManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimitManager, cls).__new__(cls)
            cls._instance.requests = {} # model -> deque of timestamps
            cls._instance.tokens = {}   # model -> deque of (timestamp, count)
            cls._instance.daily_requests = {} # model -> count (reset manually or by time)
            cls._instance.last_reset = time.time()
    
    def check_limit(self, model_name: str, estimated_tokens: int = 0) -> bool:
        """Check if request is within rate limits."""
        limits = RATE_LIMITS.get(model_name, RATE_LIMITS["default"])
        now = time.time()
        
        # Reset daily if needed (simplified 24h reset)
        if now - self._instance.last_reset > 86400:
            self._instance.daily_requests = {}
            self._instance.last_reset = now
            
        # 1. Check RPD
        daily_count = self._instance.daily_requests.get(model_name, 0)
        if daily_count >= limits["rpd"]:
            print(f"{Colors.NEON_RED}[LIMIT] Daily limit reached for {model_name}{Colors.RESET}")
            return False

        # 2. Check RPM
        if model_name not in self._instance.requests:
            self._instance.requests[model_name] = deque()
        
        # Prune requests older than 1 minute
        while self._instance.requests[model_name] and now - self._instance.requests[model_name][0] > 60:
            self._instance.requests[model_name].popleft()
            
        if len(self._instance.requests[model_name]) >= limits["rpm"]:
            print(f"{Colors.NEON_RED}[LIMIT] RPM limit reached for {model_name}{Colors.RESET}")
            return False
            
        # 3. Check TPM (Input)
        if model_name not in self._instance.tokens:
            self._instance.tokens[model_name] = deque()
            
        # Prune tokens older than 1 minute
        current_tpm = 0
        while self._instance.tokens[model_name] and now - self._instance.tokens[model_name][0][0] > 60:
            self._instance.tokens[model_name].popleft()
            
        current_tpm = sum(t[1] for t in self._instance.tokens[model_name])
        
        if current_tpm + estimated_tokens > limits["tpm"]:
            print(f"{Colors.NEON_RED}[LIMIT] TPM limit reached for {model_name}{Colors.RESET}")
            return False
            
        return True

    def record_request(self, model_name: str, token_count: int):
        """Record a successful request."""
        now = time.time()
        
        # Record request
        if model_name not in self._instance.requests:
            self._instance.requests[model_name] = deque()
        self._instance.requests[model_name].append(now)
        
        # Record tokens
        if model_name not in self._instance.tokens:
            self._instance.tokens[model_name] = deque()
        self._instance.tokens[model_name].append((now, token_count))
        
        # Record daily
        self._instance.daily_requests[model_name] = self._instance.daily_requests.get(model_name, 0) + 1

rate_limiter = RateLimitManager()

class CostManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CostManager, cls).__new__(cls)
            cls._instance.usage_history = deque() # List of (timestamp, cost)
            cls._instance.total_cost_window = 0.0
        return cls._instance


    def record_tool_usage(self, tool_name: str, count: int = 1):
        """Record tool usage cost."""
        unit_cost = TOOL_COSTS.get(tool_name, 0.0)
        cost = unit_cost * count
        
        if cost > 0:
            now = time.time()
            self.usage_history.append((now, cost))
            self.total_cost_window += cost
            self._prune_history(now)
            
            print(f"{Colors.DIM}[COST] +${cost:.4f} (Tool: {tool_name}){Colors.RESET}")

    def record_usage(self, model_key: str, input_tokens: int, output_tokens: int):
        """Record usage and update running cost."""
        
        # 1. Record Rate Limit Usage
        rate_limiter.record_request(model_key, input_tokens)
        
        # 2. Calculate Cost
        cost_entry = MODEL_COSTS.get(model_key, 0.0)
        
        if isinstance(cost_entry, dict):
            # Handle split pricing (input vs output)
            input_cost = (input_tokens / 1000.0) * cost_entry.get("input", 0.0)
            output_cost = (output_tokens / 1000.0) * cost_entry.get("output", 0.0)
            cost = input_cost + output_cost
        else:
            # Handle legacy single float (blended/per-1k)
            total_tokens = input_tokens + output_tokens
            cost = (total_tokens / 1000.0) * cost_entry
        
        now = time.time()
        self.usage_history.append((now, cost))
        self.total_cost_window += cost
        
        # Prune old entries
        self._prune_history(now)
        
        # Log if cost is accumulating
        if cost > 0.01:
            print(f"{Colors.DIM}[COST] +${cost:.4f} ({self.total_cost_window:.4f}/hr){Colors.RESET}")

    def _prune_history(self, now):
        """Remove entries older than the window."""
        while self.usage_history and (now - self.usage_history[0][0] > WINDOW_SIZE_SECONDS):
            _, expired_cost = self.usage_history.popleft()
            self.total_cost_window -= expired_cost
            
        # Safety clamp
        if self.total_cost_window < 0:
            self.total_cost_window = 0.0

    def check_budget(self) -> bool:
        """Return True if within budget, False if exceeded."""
        self._prune_history(time.time())
        return self.total_cost_window < HOURLY_BUDGET

    def get_safe_model(self, requested_model: str) -> str:
        """Return fallback model if budget or rate limit exceeded."""
        
        # 1. Check Budget
        if not self.check_budget():
            if "gemini-3-pro" in requested_model:
                print(f"{Colors.NEON_RED}[BUDGET] Hourly limit exceeded (${self.total_cost_window:.2f}). Falling back to 2.5 Pro.{Colors.RESET}")
                return "gemini-2.5-pro"
        
        # 2. Check Rate Limits
        if not rate_limiter.check_limit(requested_model):
            print(f"{Colors.NEON_RED}[LIMIT] Rate limit hit for {requested_model}. Falling back to 2.5 Flash.{Colors.RESET}")
            return "gemini-2.5-flash"
            
        return requested_model

    def get_remaining_credits(self) -> dict:
        """Return current credit status."""
        return {
            "gemini": GEMINI_CREDIT_REMAINING,
            "monthly": MONTHLY_CREDIT_REMAINING,
            "app_builder": APP_BUILDER_CREDIT_REMAINING,
            "hourly_spend": self.total_cost_window
        }

cost_manager = CostManager()
