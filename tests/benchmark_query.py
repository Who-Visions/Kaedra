"""Quick benchmark test for SQLite-first query layer."""
import sys
sys.path.insert(0, '.')
import time

# Test local query directly
print("=" * 60)
print("SQLITE-FIRST QUERY BENCHMARK")
print("=" * 60)

# 1. Direct local query
from kaedra.services.local_query import LocalQueryService
lqs = LocalQueryService()

print("\n[1] Direct LocalQueryService:")
t = time.time()
result = lqs.find_entity("Yasuke")
elapsed = (time.time() - t) * 1000
print(f"    find_entity('Yasuke'): {elapsed:.1f}ms")
print(f"    Found: {result.get('name') if result else 'None'}")

# 2. Via NotionService (hybrid)
from kaedra.services.notion import NotionService
ns = NotionService()

print("\n[2] Via NotionService (should hit local cache):")
t = time.time()
result = ns.find_entity("Yasuke")
elapsed = (time.time() - t) * 1000
print(f"    find_entity('Yasuke'): {elapsed:.1f}ms")
print(f"    Found: {result.get('name') if result else 'None'}")

# 3. Search
print("\n[3] Search ('shadow'):")
t = time.time()
results = lqs.search("shadow", limit=5)
elapsed = (time.time() - t) * 1000
print(f"    search('shadow'): {elapsed:.1f}ms")
print(f"    Results: {[r.get('name') for r in results]}")

# 4. Stats
print("\n[4] Stats:")
stats = lqs.get_stats()
print(f"    Total entities: {stats.get('total')}")
print(f"    Available: {stats.get('available')}")

print("\n" + "=" * 60)
print("BENCHMARK COMPLETE")
print("=" * 60)
