"""Quick cache test for invoice tool."""
import time
from kaedra.tools.invoices import invoice_action

print("Testing invoice tool cache...")

# First call - should hit API
t1 = time.perf_counter()
r1 = invoice_action("status")
t2 = time.perf_counter()

# Second call - should be cached
r2 = invoice_action("status")
t3 = time.perf_counter()

print(f"First call: {(t2-t1)*1000:.0f}ms")
print(f"Second call (cached): {(t3-t2)*1000:.0f}ms")
print(f"Cached flag: {r2.get('_cached', False)}")
print(f"Speedup: {((t2-t1)/(t3-t2)):.1f}x")
