import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService

def batch_score():
    service = NotionService()
    print("🚀 Batch Scoring Initiated...")
    
    # 1. Fetch All
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Fetched {len(pages)} entities.")
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    updated_count = 0
    skipped_count = 0
    ghost_count = 0
    
    print("⚡ Starting Score Calculation...")
    
    for page in pages:
        props = page.get("properties", {})
        p_id = page["id"]
        
        # Check Validity (Skip Ghosts)
        title = service._get_title(page)
        cat = service.safe_get_property(props, "Category", "select")
        
        if not title and not cat:
            ghost_count += 1
            print(f"   👻 Skipping Ghost: {p_id}")
            continue
            
        # Calculate Scores
        imp_score = service.calculate_importance_score(props)
        conf_score = service.calculate_canon_confidence(props)
        
        # Check if update needed
        current_imp = service.safe_get_property(props, "Importance Score", "number")
        current_conf = service.safe_get_property(props, "Canon Confidence", "number")
        
        if current_imp == imp_score and current_conf == conf_score:
            skipped_count += 1
            continue
            
        # Update
        try:
            update_payload = {
                "properties": {
                    "Importance Score": {"number": imp_score},
                    "Canon Confidence": {"number": conf_score}
                }
            }
            
            # Using raw client patch
            service.client.patch(
                 f"https://api.notion.com/v1/pages/{p_id}",
                 json=update_payload
            )
            updated_count += 1
            print(f"   ✅ Scored '{title}': Imp={imp_score}, Conf={conf_score}")
            
        except Exception as e:
            print(f"   ❌ Failed to score '{title}': {e}")

    print("\n🏁 Scoring Complete.")
    print(f"   - Updated: {updated_count}")
    print(f"   - Skipped (No Change): {skipped_count}")
    print(f"   - Ghosts Ignored: {ghost_count}")

if __name__ == "__main__":
    batch_score()
