"""
Quick verification that NotionService works with new token.
"""
import os
import sys

# Use NOTION_TOKEN from environment
NS_TOKEN = os.getenv("NOTION_TOKEN")

# Now import the service
from kaedra.services.notion import NotionService

def verify_connection():
    print("=" * 60)
    print("🔗 VERIFYING NEW NOTION CONNECTION")
    print("=" * 60)
    
    ns = NotionService()
    
    # 1. Test client initialization
    if ns.client:
        print("✅ Notion client initialized successfully")
    else:
        print("❌ Notion client failed to initialize")
        return False
    
    # 2. Test global search
    print("\n[Testing Global Search for 'Veil']...")
    try:
        results = ns.global_search("Veil", limit=5)
        print(f"✅ Found {len(results)} results")
        for r in results[:3]:
            print(f"   - {r.get('title', 'Untitled')} ({r.get('type', 'N/A')})")
    except Exception as e:
        print(f"❌ Global search failed: {e}")
    
    # 3. Test page read (Ai with Dav3 Cinematic Universe)
    print("\n[Testing Page Read: 'Ai with Dav3 Cinematic Universe']...")
    try:
        content = ns.read_page_content("2e5ca671-311e-811f-8229-d04a1f430059")
        if content and not content.startswith("[Error"):
            print(f"✅ Page read successful ({len(content)} chars)")
            print(f"   Preview: {content[:150]}...")
        else:
            print(f"⚠️ Page read returned: {content[:100]}")
    except Exception as e:
        print(f"❌ Page read failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 60)
    return True

if __name__ == "__main__":
    verify_connection()
