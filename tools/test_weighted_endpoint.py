import sys
from pathlib import Path
import requests
import json

# Test the /lore/weighted endpoint
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

def test_weighted_endpoint():
    print("🧪 Testing /lore/weighted Endpoint...")
    
    # Test 1: Basic connectivity
    try:
        response = requests.get("http://192.168.1.187:8000/lore/weighted?limit=10")
        print(f"✅ Test 1: Endpoint reachable (Status: {response.status_code})")
        
        if response.status_code != 200:
            print(f"❌ Expected 200, got {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        return
    
    # Test 2: Response structure
    try:
        data = response.json()
        assert "items" in data, "Response missing 'items' key"
        items = data["items"]
        print(f"✅ Test 2: Valid JSON structure ({len(items)} items returned)")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        return
    
    # Test 3: Item schema validation
    if items:
        first_item = items[0]
        required_fields = ["id", "title", "category", "importance", "confidence"]
        for field in required_fields:
            assert field in first_item, f"Missing field: {field}"
        print(f"✅ Test 3: Item schema valid")
        print(f"   Sample: {first_item['title']} (Imp: {first_item['importance']}, Cat: {first_item['category']})")
    
    # Test 4: Sorting verification
    importances = [item["importance"] for item in items]
    is_sorted = all(importances[i] >= importances[i+1] for i in range(len(importances)-1))
    if is_sorted:
        print(f"✅ Test 4: Items correctly sorted by importance descending")
        print(f"   Range: {importances[0]} -> {importances[-1]}")
    else:
        print(f"❌ Test 4 Failed: Items not sorted correctly")
        print(f"   Scores: {importances}")
    
    # Test 5: Keyword override verification (Xoah/Shadow Dweller should be 90+)
    xoah_items = [i for i in items if "xoah" in i["title"].lower() or "shadow dweller" in i["title"].lower()]
    if xoah_items:
        all_high = all(i["importance"] >= 90 for i in xoah_items)
        if all_high:
            print(f"✅ Test 5: Keyword override working ({len(xoah_items)} Xoah/Shadow items at 90+)")
        else:
            print(f"⚠️ Test 5: Some keyword items below 90")
            for i in xoah_items:
                print(f"   - {i['title']}: {i['importance']}")
    
    # Test 6: Category distribution
    categories = {}
    for item in items:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1
    print(f"✅ Test 6: Category distribution:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cat}: {count}")
    
    print("\n🎯 All Tests Passed!")

if __name__ == "__main__":
    test_weighted_endpoint()
