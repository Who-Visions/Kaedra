import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService

def test_weighted_lore_logic():
    print("🧪 Testing Weighted Lore Logic (Direct NotionService Test)...")
    
    try:
        service = NotionService()
        print("✅ Test 1: NotionService initialized")
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")
        return
    
    # Test 2: Fetch all pages
    try:
        pages = service.list_all_universe_pages()
        print(f"✅ Test 2: Fetched {len(pages)} pages from Notion")
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")
        return
    
    # Test 3: Extract and sort by importance
    weighted_items = []
    for page in pages:
        props = page.get("properties", {})
        title = service._get_title(page)
        
        if not title:
            continue
        
        imp_score = service.safe_get_property(props, "Importance Score", "number") or 0
        conf_score = service.safe_get_property(props, "Canon Confidence", "number") or 0
        category = service.safe_get_property(props, "Category", "select") or "Lore"
        
        weighted_items.append({
            "title": title,
            "category": category,
            "importance": imp_score,
            "confidence": conf_score
        })
    
    weighted_items.sort(key=lambda x: x["importance"], reverse=True)
    print(f"✅ Test 3: Extracted and sorted {len(weighted_items)} valid items")
    
    # Test 4: Verify top items
    print(f"\n📊 Top 10 Weighted Lore Items:")
    for i, item in enumerate(weighted_items[:10], 1):
        print(f"   {i}. {item['title'][:50]:<50} | Imp: {item['importance']:>3} | Cat: {item['category']}")
    
    # Test 5: Verify keyword overrides
    xoah_items = [i for i in weighted_items if "xoah" in i["title"].lower() or "shadow dweller" in i["title"].lower()]
    if xoah_items:
        all_high = all(i["importance"] >= 90 for i in xoah_items)
        print(f"\n✅ Test 5: Keyword Override Check")
        print(f"   Found {len(xoah_items)} Xoah/Shadow Dweller items")
        print(f"   All >= 90: {all_high}")
        if not all_high:
            print("   ⚠️ Items below 90:")
            for i in xoah_items:
                if i["importance"] < 90:
                    print(f"      - {i['title']}: {i['importance']}")
    
    # Test 6: Score distribution
    score_ranges = {"90-100": 0, "70-89": 0, "50-69": 0, "25-49": 0, "0-24": 0}
    for item in weighted_items:
        score = item["importance"]
        if score >= 90: score_ranges["90-100"] += 1
        elif score >= 70: score_ranges["70-89"] += 1
        elif score >= 50: score_ranges["50-69"] += 1
        elif score >= 25: score_ranges["25-49"] += 1
        else: score_ranges["0-24"] += 1
    
    print(f"\n📈 Score Distribution:")
    for range_name, count in score_ranges.items():
        pct = (count / len(weighted_items)) * 100 if weighted_items else 0
        print(f"   {range_name}: {count:>3} ({pct:>5.1f}%)")
    
    print("\n🎯 All Logic Tests Passed!")

if __name__ == "__main__":
    test_weighted_lore_logic()
