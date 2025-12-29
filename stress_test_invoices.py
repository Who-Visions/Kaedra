"""
Invoice Service Stress Test - 10 runs with latency tracking
"""

import os
import time
import statistics
from dotenv import load_dotenv

load_dotenv()

# Set env vars
os.environ.setdefault("STRIPE_SECRET_KEY", os.getenv("STRIPE_SECRET_KEY", ""))
os.environ.setdefault("SQUARE_ACCESS_TOKEN", os.getenv("SQUARE_ACCESS_TOKEN", ""))
os.environ.setdefault("SQUARE_ENVIRONMENT", os.getenv("SQUARE_ENVIRONMENT", "production"))

RUNS = 10

def test_stripe(runs=RUNS):
    """Stress test Stripe API."""
    print(f"\n{'='*50}")
    print(f"STRIPE STRESS TEST ({runs} runs)")
    print('='*50)
    
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    latencies = []
    errors = 0
    
    for i in range(runs):
        start = time.perf_counter()
        try:
            result = stripe.Customer.list(limit=5)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            print(f"  Run {i+1}: {latency:.0f}ms - {len(result.data)} customers")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            errors += 1
            print(f"  Run {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\nResults:")
        print(f"  Min: {min(latencies):.0f}ms")
        print(f"  Max: {max(latencies):.0f}ms")
        print(f"  Avg: {statistics.mean(latencies):.0f}ms")
        print(f"  Median: {statistics.median(latencies):.0f}ms")
        if len(latencies) > 1:
            print(f"  StdDev: {statistics.stdev(latencies):.0f}ms")
        print(f"  Errors: {errors}/{runs}")
    
    return latencies


def test_square(runs=RUNS):
    """Stress test Square API."""
    print(f"\n{'='*50}")
    print(f"SQUARE STRESS TEST ({runs} runs)")
    print('='*50)
    
    from square import Square
    client = Square(token=os.getenv("SQUARE_ACCESS_TOKEN"))
    
    latencies = []
    errors = 0
    
    for i in range(runs):
        start = time.perf_counter()
        try:
            result = client.locations.list()
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)
            locs = result.locations or []
            print(f"  Run {i+1}: {latency:.0f}ms - {len(locs)} locations")
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            errors += 1
            print(f"  Run {i+1}: {latency:.0f}ms - ERROR: {e}")
    
    if latencies:
        print(f"\nResults:")
        print(f"  Min: {min(latencies):.0f}ms")
        print(f"  Max: {max(latencies):.0f}ms")
        print(f"  Avg: {statistics.mean(latencies):.0f}ms")
        print(f"  Median: {statistics.median(latencies):.0f}ms")
        if len(latencies) > 1:
            print(f"  StdDev: {statistics.stdev(latencies):.0f}ms")
        print(f"  Errors: {errors}/{runs}")
    
    return latencies


def main():
    print("="*50)
    print("INVOICE SERVICE STRESS TEST")
    print("="*50)
    
    stripe_latencies = test_stripe()
    square_latencies = test_square()
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    
    if stripe_latencies:
        print(f"Stripe: {statistics.mean(stripe_latencies):.0f}ms avg ({len(stripe_latencies)}/{RUNS} success)")
    else:
        print("Stripe: No successful runs")
    
    if square_latencies:
        print(f"Square: {statistics.mean(square_latencies):.0f}ms avg ({len(square_latencies)}/{RUNS} success)")
    else:
        print("Square: No successful runs")
    
    # Combined
    if stripe_latencies and square_latencies:
        total_avg = (statistics.mean(stripe_latencies) + statistics.mean(square_latencies)) / 2
        print(f"\nCombined avg: {total_avg:.0f}ms")
        
        # Recommendations
        print("\n" + "="*50)
        print("OPTIMIZATION RECOMMENDATIONS")
        print("="*50)
        
        if statistics.mean(stripe_latencies) > 500:
            print("⚠ Stripe latency high - consider caching customer data")
        else:
            print("✓ Stripe latency acceptable")
            
        if statistics.mean(square_latencies) > 500:
            print("⚠ Square latency high - consider caching location data")
        else:
            print("✓ Square latency acceptable")


if __name__ == "__main__":
    main()
