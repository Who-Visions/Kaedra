import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService

def verify_distribution():
    service = NotionService()
    print("📊 Score Distribution Audit Initiated...")
    
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Fetched {len(pages)} entities.")
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    # Metrics
    imp_scores = []
    conf_scores = []
    
    imp_buckets = defaultdict(int)
    conf_buckets = defaultdict(int)
    
    valid_count = 0
    
    for page in pages:
        props = page.get("properties", {})
        
        # Skip ghosts logic (reused)
        title = service._get_title(page)
        cat = service.safe_get_property(props, "Category", "select")
        if not title and not cat:
            continue
            
        valid_count += 1
        
        imp = service.safe_get_property(props, "Importance Score", "number") or 0
        conf = service.safe_get_property(props, "Canon Confidence", "number") or 0
        
        imp_scores.append(imp)
        conf_scores.append(conf)
        
        # Bucketize
        # 90-100, 70-89, 50-69, 25-49, 0-24
        def get_bucket(val):
            if val >= 90: return "90-100 (Major)"
            if val >= 70: return "70-89 (Supporting)"
            if val >= 50: return "50-69 (Mid)"
            if val >= 25: return "25-49 (Minor)"
            return "00-24 (Background)"
            
        imp_buckets[get_bucket(imp)] += 1
        conf_buckets[get_bucket(conf)] += 1

    print(f"\n📈 ANALYSIS (N={valid_count})", flush=True)
    
    print("\n🔹 Importance Score Distribution:", flush=True)
    order = ["90-100 (Major)", "70-89 (Supporting)", "50-69 (Mid)", "25-49 (Minor)", "00-24 (Background)"]
    for b in order:
        count = imp_buckets[b]
        pct = (count / valid_count) * 100 if valid_count else 0
        bar = "█" * int(pct / 2)
        print(f"  {b:<20} : {count:>3} ({pct:>5.1f}%) {bar}", flush=True)
        
    print("\n🔸 Canon Confidence Distribution:", flush=True)
    for b in order:
        count = conf_buckets[b]
        pct = (count / valid_count) * 100 if valid_count else 0
        bar = "█" * int(pct / 2)
        print(f"  {b:<20} : {count:>3} ({pct:>5.1f}%) {bar}", flush=True)

if __name__ == "__main__":
    verify_distribution()
