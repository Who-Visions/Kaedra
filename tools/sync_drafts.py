import os
import sys
import toml
import requests
import json
from pathlib import Path

# Add root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DRAFT_IDS = {
    "veil_quantum_mechanics": "5357a3702f6e43b0a06a99a35232648a",
    "architects_theory": "3afdc6e85dc34633bb3e4113292b49e5",
    "symbient_corruption": "a04ce38e08e2445c87ff17fd4fef13b7",
    "martian_cataclysm": "94c910c9f550425f89fcf6d2caa43419",
    "liminal_zones": "7382a3a4ae37446ab61bbd476321e23c",
    "dormant_dna": "9af2a52b7609479d9fbcf3adbc782ad4",
    "phobos_station": "d62e0df968514bda83905c62a3471002",
    "column_network": "3e8f46aacb7e45888dd276ee06a67629",
    "magnetic_interface": "fa146db6c6ba429b8dd34877e81716a0",
    "sea_people": "53782efd8c304d2ab4ae11cd9ffb5a51",
    "project_apex": "afcbd1d0e8db406bafbbbf730249a804",
    "veil_os": "9f5dcf3b4fc24d2e9fd95590c93ae6e2"
}

def sync_drafts():
    config_path = ROOT / "kaedra" / "config" / "notion.toml"
    config = toml.load(config_path)
    token = config["notion"]["token"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2025-09-03"
    }
    
    out_dir = ROOT / "lore" / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Bulking syncing {len(DRAFT_IDS)} drafts...")
    
    for name, page_id in DRAFT_IDS.items():
        print(f"   📥 Syncing: {name}...")
        
        # 1. Get Page Title
        page_url = f"https://api.notion.com/v1/pages/{page_id}"
        resp = requests.get(page_url, headers=headers)
        if resp.status_code != 200:
            print(f"      ⚠️ Failed page fetch ({resp.status_code}): {name}")
            continue
            
        # Title extraction is tricky in Notion because it depends on the DB schema or page properties
        # For simplicity, we'll try 'title' or fallback to the key name
        page_data = resp.json()
        title = name
        props = page_data.get("properties", {})
        for pk, pv in props.items():
            if pv.get("type") == "title" and pv.get("title"):
                title = pv["title"][0].get("plain_text", name)
                break
        
        # 2. Get Blocks (Content)
        content_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        content_resp = requests.get(content_url, headers=headers)
        if content_resp.status_code != 200:
            print(f"      ⚠️ Failed content fetch ({content_resp.status_code}): {name}")
            continue
            
        blocks = content_resp.json().get("results", [])
        text_parts = [f"# {title}\n"]
        
        for block in blocks:
            btype = block.get("type")
            if btype in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "callout"]:
                rich_text = block.get(btype, {}).get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text])
                if btype == "heading_1": text = f"\n# {text}"
                elif btype == "heading_2": text = f"\n## {text}"
                elif btype == "heading_3": text = f"\n### {text}"
                elif btype == "bulleted_list_item": text = f"- {text}"
                elif btype == "callout": text = f"> [!NOTE]\n> {text}"
                text_parts.append(text)
        
        # Save as Markdown
        md_path = out_dir / f"{name}.md"
        md_path.write_text("\n".join(text_parts), encoding="utf-8")
        print(f"      ✅ Saved to {md_path.relative_to(ROOT)}")

    print("\n✅ Bulk Sync Complete.")

if __name__ == "__main__":
    sync_drafts()
