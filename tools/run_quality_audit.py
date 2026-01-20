import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from kaedra.services.notion_service import NotionService
import json
from collections import defaultdict

def run_audit():
    service = NotionService()
    print("🚀 Starting Quality Audit...")
    
    # 1. Fetch All Pages
    try:
        pages = service.list_all_universe_pages()
        print(f"📦 Fetched {len(pages)} entities. Auditing...")
    except Exception as e:
        print(f"❌ Failed to fetch pages: {e}")
        return

    # 2. Define Rules
    # Rule check returns list of missing fields
    def check_rules(props):
        cat = service.safe_get_property(props, "Category", "select")
        missing = []
        
        # Global Required
        if not service.safe_get_property(props, "Name", "title"):
            missing.append("Name")

        if not cat:
            # Maybe uncategorized is allowed, but let's flag it
            # missing.append("Category (Missing)") 
            pass
        
        # Category Specific
        if cat == "Organization":
            if not service.safe_get_property(props, "Entity Subtype", "select"): missing.append("Entity Subtype")
            # Themes is multi-select
            if not service.safe_get_property(props, "Themes", "multi_select"): missing.append("Themes")
            
        elif cat == "Culture":
            if not service.safe_get_property(props, "Universe Era", "select"): missing.append("Universe Era")
            if not service.safe_get_property(props, "Home World", "rich_text"): missing.append("Home World")
            if not service.safe_get_property(props, "Themes", "multi_select"): missing.append("Themes")
            
        elif cat == "Creature":
            if not service.safe_get_property(props, "Species/Race", "multi_select"): missing.append("Species/Race")
            
        elif cat == "Planet":
            if not service.safe_get_property(props, "Universe Era", "select"): missing.append("Universe Era")
            if not service.safe_get_property(props, "Description", "rich_text"): missing.append("Description")
            
        elif cat == "Scene":
            if not service.safe_get_property(props, "Story Arc", "select"): missing.append("Story Arc")
            if not service.safe_get_property(props, "Appears In", "multi_select"): missing.append("Appears In")
            if not service.safe_get_property(props, "Timeline Year", "number") and not service.safe_get_property(props, "Timeline Precision", "select"): 
                missing.append("Timeline Data (Year or Precision)")

        return missing, cat

    # 3. Audit
    report = defaultdict(list)
    total_issues = 0
    
    for page in pages:
        props = page.get("properties", {})
        title = service._get_title(page) or "Untitled"
        p_id = page["id"]
        
        missing, cat = check_rules(props)
        
        if missing:
            total_issues += 1
            report[cat or "Uncategorized"].append({
                "title": title,
                "id": p_id,
                "url": page.get("url"),
                "missing": missing
            })

    # 4. Generate Report
    md_lines = [
        "# 🕵️ Notion Quality Audit Report",
        f"**Total Entities Scanned**: {len(pages)}",
        f"**Total Issues Found**: {total_issues}",
        "",
        "## 🚨 Issues by Category"
    ]
    
    for cat, items in sorted(report.items()):
        md_lines.append(f"### {cat} ({len(items)})")
        for item in items:
            md_lines.append(f"- **[{item['title']}]({item['url']})**: Missing `{', '.join(item['missing'])}`")
        md_lines.append("")

    out_path = Path(__file__).parent.parent / "NOTION_QA_REPORT.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"✅ Audit Complete. Found {total_issues} issues. Report saved to {out_path}")

if __name__ == "__main__":
    run_audit()
