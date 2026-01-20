import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService

def check_categories():
    service = NotionService()
    print("📊 Category Distribution Audit Initiated...", flush=True)
    
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Fetched {len(pages)} entities.", flush=True)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    cat_counts = defaultdict(int)
    valid_count = 0
    
    for page in pages:
        props = page.get("properties", {})
        
        # Skip ghosts logic
        title = service._get_title(page)
        cat = service.safe_get_property(props, "Category", "select")
        
        if not title and not cat:
            continue
            
        valid_count += 1
        
        cat_key = cat if cat else "[Uncategorized]"
        cat_counts[cat_key] += 1

    print(f"\n📈 CATEGORY ANALYSIS (N={valid_count})", flush=True)
    
    # Sort by count desc
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    
    for cat, count in sorted_cats:
        pct = (count / valid_count) * 100 if valid_count else 0
        bar = "█" * int(pct / 2)
        print(f"  {cat:<25} : {count:>3} ({pct:>5.1f}%) {bar}", flush=True)

if __name__ == "__main__":
    check_categories()
