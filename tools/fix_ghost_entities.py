import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.loredb import LoreDB
from kaedra.services.notion_service import NotionService
import sqlite3

def fix_ghosts():
    service = NotionService()
    print("👻 Ghostbuster Protocol Initiated (VERIFICATION MODE)...")
    
    # 1. Initialize LoreDB Paths (Read-Only Check)
    # We found multiple potential DBs, let's check ALL of them to be safe.
    loredb_paths = [
        ROOT / "lore/worlds/world_bee9d6ac/lore.db",
        ROOT / "lore/worlds/world_f1a51f5a/lore.db",
        ROOT / "kaedra/lore/worlds/world_f1a51f5a/lore.db",
        ROOT / "lore/worlds/stress_test_world/lore.db",
        ROOT / "data/veilverse_backup.db"
    ]
    
    active_conns = []
    for p in loredb_paths:
        if p.exists():
            print(f"📚 Found LoreDB at: {p}")
            try:
                c = sqlite3.connect(p)
                c.row_factory = sqlite3.Row
                active_conns.append(c)
            except Exception as e:
                print(f"⚠️ Could not connect to {p}: {e}")
    
    if not active_conns:
        print("⚠️ Warning: No local LoreDB found. Proceeding with caution.")
    else:
        print(f"🔗 Connected to {len(active_conns)} local databases for cross-reference.")

    # 2. Fetch Candidates
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Scanned {len(pages)} entities.")
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return

    ghosts = []
    preserved_count = 0
    
    for page in pages:
        props = page.get("properties", {})
        title = service._get_title(page)
        cat = service.safe_get_property(props, "Category", "select")
        
        # Definition of a Ghost: No Name AND No Category
        if not title and not cat:
            # CROSS REFERENCE
            p_id = page["id"]
            clean_id = p_id.replace("-", "")
            is_safe = False
            
            for conn in active_conns:
                try:
                    # Check Blocks
                    row = conn.execute(
                        "SELECT id FROM blocks WHERE id = ? OR id = ? OR attrs LIKE ?", 
                        (p_id, clean_id, f'%{p_id}%')
                    ).fetchone()
                    if row:
                        print(f"🛡️ PRESERVED (Block Match): {p_id}")
                        is_safe = True
                        break
                        
                    # Check Links (Bilateral)
                    link_row = conn.execute(
                        "SELECT source_id FROM links WHERE source_id = ? OR target_id = ?",
                        (p_id, p_id)
                    ).fetchone()
                    if link_row:
                        print(f"🛡️ PRESERVED (Link Match): {p_id}")
                        is_safe = True
                        break
                        
                except Exception:
                    pass
            
            if is_safe:
                preserved_count += 1
            else:
                # Analyze what remains
                alt_name = service.safe_get_property(props, "Display Name", "rich_text")
                aliases = service.safe_get_property(props, "Alias", "multi_select") or []
                created_time = page.get("created_time", "")
                
                ghosts.append({
                    "data": page,
                    "alt_name": alt_name,
                    "aliases": aliases,
                    "created": created_time
                })

    print(f"👻 Found {len(ghosts)} Unsafe Ghost Entities. (Preserved {preserved_count} matched entities)")
    
    if not ghosts:
        print("✅ No ghosts found. Exiting.")
        return

    # 3. Output Sample for Verification
    print("\n🔍 GHOST MANIFEST (Deep Scan):")
    # Sort by created time to group batch creations
    ghosts.sort(key=lambda x: x['created'])
    
    for g in ghosts:
        page = g['data']
        ident = g['alt_name'] or str(g['aliases']) if g['aliases'] else "[NO DATA]"
        print(f"📄 {page['url']}")
        print(f"   └── 🆔 Metadata: {ident} | 📅 {g['created']} | 🔗 ID: {page['id']}")
        
    print(f"\nTotal: {len(ghosts)} candidates ready for purge.")
    
    # Close connections
    for c in active_conns:
        c.close()

if __name__ == "__main__":
    fix_ghosts()
