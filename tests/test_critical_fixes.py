import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kaedra.story.engine import StoryEngine
from kaedra.core.retry import RetryPolicy
from kaedra.story.context import ContextManager

async def test_context_budget():
    """Test context budget enforcement."""
    print("🧪 Testing Context Budget...")
    # Mock engine/client not needed for pure context logic test if we mock client
    class MockClient:
        pass
        
    ctx = ContextManager(MockClient(), max_context_tokens=1000) # Small limit for testing
    
    # Fill context
    # "test " is 5 chars. ~1 token per 4 chars. So 1000 "test " words is ~5000 chars ~1250 tokens
    long_text = "test " * 1000 
    ctx.add_text("user", long_text)
    
    status = ctx.get_budget_status()
    print(f"   Budget Status: {status}")
    
    assert status['usage_percent'] > 100, "Context should be overflowing initially"
    assert status['should_prune'] == True, "Should flag for pruning"
    print("   ✅ Overflow detected correctly")

async def test_retry_policy():
    """Test retry with circuit breaker."""
    print("\n🧪 Testing Retry Policy...")
    
    policy = RetryPolicy(max_attempts=3, base_delay=0.1)
    attempts = 0
    
    async def failing_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("Temporary failure")
        return "Success"
    
    result = await policy.execute_async(failing_func)
    print(f"   Result: {result}, Attempts: {attempts}")
    assert result == "Success"
    assert attempts == 3
    print("   ✅ Retry logic worked")
    
    # Test Circuit Breaker
    print("\n🧪 Testing Circuit Breaker...")
    policy = RetryPolicy(max_attempts=3, base_delay=0.01)
    
    async def always_fail():
        raise Exception("Persistent failure")
        
    # Trip the breaker (threshold is 5 failures)
    # Each execute_async call that fails fully counts as 1 failure in logic (checking implementation)
    # My implementation increments _successive_failures when ALL attempts fail.
    
    for i in range(5):
        try:
            await policy.execute_async(always_fail)
        except:
            pass
            
    assert policy._circuit_open == True, "Circuit breaker should be OPEN after 5 failures"
    
    try:
        await policy.execute_async(always_fail)
        assert False, "Should have raised Circuit Breaker exception"
    except Exception as e:
        assert "Circuit Breaker OPEN" in str(e)
        print("   ✅ Circuit Breaker blocked execution")

if __name__ == "__main__":
    asyncio.run(test_context_budget())
    asyncio.run(test_retry_policy())
    print("\n🎉 All critical fixes validated successfully")
