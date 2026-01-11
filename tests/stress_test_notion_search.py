import os
import sys
import random
import time

# Add current directory to path
sys.path.insert(0, os.getcwd())

from kaedra.services.notion import NotionService

def run_stress_test(max_runs=100):
    notion = NotionService()
    print(f"--- Starting Notion Search Stress Test (Max Runs: {max_runs}) ---")
    
    # 1. Fetch a pool of entities to test against
    print("[*] Fetching entity pool from Universe DB...")
    pool = notion._query_database_httpx(notion.UNIVERSE_DB_ID if hasattr(notion, 'UNIVERSE_DB_ID') else "2d90b4b4-0f65-8001-98fe-cbf8a4a2146a", limit=100)
    if not pool:
        print("[!] Pool is empty. Check UNIVERSE_DB_ID or token.")
        return

    entities = []
    for res in pool:
        title = notion._get_title(res)
        if title == "Untitled" or not title: continue # Skip noise
        
        props = res.get("properties", {})
        
        # Extract aliases
        aliases = []
        alias_prop = props.get("Alias", {})
        if alias_prop.get("type") == "multi_select":
            aliases = [a.get("name", "") for a in alias_prop.get("multi_select", [])]
        elif alias_prop.get("type") == "rich_text":
            aliases = [a.get("plain_text", "") for a in alias_prop.get("rich_text", [])]
            
        entities.append({
            "id": res["id"],
            "title": title,
            "aliases": aliases
        })

    print(f"[*] Pooled {len(entities)} entities for testing.")
    
    retrieval_success = 0
    ranking_perfect = 0
    total_runs = 0
    
    for i in range(max_runs):
        total_runs += 1
        target = random.choice(entities)
        
        # Decide on a query type: 0=Full Title, 1=Partial Title, 2=Alias (if available)
        q_type = random.randint(0, 2)
        if q_type == 2 and not target["aliases"]:
            q_type = random.randint(0, 1)
            
        if q_type == 0:
            query = target["title"]
            mode = "Full Title"
        elif q_type == 1:
            words = target["title"].split()
            # Pick a middle word or first word
            query = words[random.randint(0, len(words)-1)] if words else target["title"]
            mode = f"Partial ('{query}')"
        else:
            query = random.choice(target["aliases"])
            mode = f"Alias ('{query}')"

        print(f"\n[Run {i+1}/{max_runs}] Mode: {mode} | Target: '{target['title']}'")
        
        # We need to capture candidates to check retrieval
        # Temporarily monkey-patch or just look at logs if we added them.
        # Let's just use the service and assume if score > 0 it was retrieved.
        
        start_time = time.time()
        result_id = notion.search_page(query)
        duration = time.time() - start_time
        
        if result_id == target["id"]:
            print(f"✅ PERFECT MATCH! ({duration:.2f}s)")
            ranking_perfect += 1
            retrieval_success += 1
        else:
            # Check if it even found the target at all (we'd need to peek at candidates)
            # For now, let's just see what it found
            actual_title = "NONE"
            if result_id:
                try:
                    res = notion.client.pages.retrieve(page_id=result_id)
                    actual_title = notion._get_title(res)
                except:
                    actual_title = "ERROR"
            
            # Is the mismatch "reasonable"?
            norm_q = notion.normalize_query(query)
            norm_actual = notion.normalize_query(actual_title)
            if norm_q in norm_actual or any(norm_q in notion.normalize_query(a) for a in target["aliases"]):
                print(f"⚠️ RANKING VARIANCE (Returned '{actual_title}' instead)")
                retrieval_success += 1 # It found *something* relevant
            else:
                print(f"❌ RETRIEVAL FAILURE!")
                print(f"  Query: '{query}'")
                print(f"  Target: '{target['title']}'")
                print(f"  Found: '{actual_title}'")
                print("\n[!] Stopping due to actual failure.")
                break

    print(f"\n--- Stress Test Summary ---")
    print(f"Total Runs: {total_runs}")
    print(f"Perfect Ranking: {ranking_perfect}")
    print(f"Retrieval Success: {retrieval_success}")

if __name__ == "__main__":
    run_stress_test()
