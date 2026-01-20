import httpx
import json
import asyncio

BASE_URL = "http://127.0.0.1:8000"

async def verify_lore():
    print("🔍 Verifying Lore API...")
    
    async with httpx.AsyncClient() as client:
        # 1. Check Root
        try:
            r = await client.get(f"{BASE_URL}/health")
            print(f"Health: {r.status_code}")
        except Exception as e:
            print(f"❌ Server not reachable: {e}")
            return

        # 2. Check /lore/feed
        print("\nChecking /lore/feed...")
        r = await client.get(f"{BASE_URL}/lore/feed")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Feed Status: {r.status_code}")
            print(f"   Items: {len(data)}")
            if data:
                print(f"   First Item: {data[0]['title']} ({data[0]['category']})")
        else:
            print(f"❌ Feed Failed: {r.status_code} - {r.text}")

        # 3. Check /lore/search
        print("\nChecking /lore/search?q=Shadow...")
        r = await client.get(f"{BASE_URL}/lore/search?q=Shadow")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Search Status: {r.status_code}")
            print(f"   Results: {len(data)}")
        else:
            print(f"❌ Search Failed: {r.status_code} - {r.text}")
            
        # 4. Check /lore/weighted
        print("\nChecking /lore/weighted...")
        r = await client.get(f"{BASE_URL}/lore/weighted")
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Weighted Status: {r.status_code}")
            print(f"   Items: {len(data)}")
        else:
            print(f"❌ Weighted Failed: {r.status_code} - {r.text}")

if __name__ == "__main__":
    asyncio.run(verify_lore())
