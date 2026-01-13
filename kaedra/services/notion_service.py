import httpx
import os
import toml
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import time
import functools

# Constants from API Contract
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
# Metric ID from Rulebook was 2d90b4b4-0f65-8001-98fe-cbf8a4a2146a (likely placeholder)
# Actual Discovered Universe DB: 'VeilVerse Universe Best'
UNIVERSE_DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"

CONFIG_PATH = Path(__file__).parent.parent.parent / "kaedra" / "config" / "notion.toml"

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x)
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

class NotionService:
    def __init__(self, token: Optional[str] = None):
        if token:
            self.token = token
        else:
            self.token = self._load_token()
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }
        # We also maintain a httpx client for robust queries as per contract
        self.client = httpx.Client(timeout=30.0, headers=self.headers)

    def _load_token(self) -> str:
        """Load token from environment or toml config."""
        # Priority 1: Env Var
        env_token = os.environ.get("NOTION_API_KEY")
        if env_token:
            return env_token
            
        # Priority 2: Config File
        if CONFIG_PATH.exists():
            try:
                config = toml.load(CONFIG_PATH)
                return config["notion"]["token"]
            except Exception as e:
                print(f"Warning: Failed to load token from config: {e}")
        
        raise ValueError("No Notion Token found in Environment (NOTION_API_KEY) or config/notion.toml")

    def _query_universe_db_httpx(self, filter_obj: Dict[str, Any] = None, sorts: List[Dict] = None, page_size: int = 100, start_cursor: str = None) -> List[Dict]:
        """
        Query VeilVerse Universe using httpx fallback (Contract verified).
        """
        url = f"{NOTION_API_BASE}/databases/{UNIVERSE_DB_ID}/query"
        
        payload = {"page_size": page_size}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        if start_cursor:
            payload["start_cursor"] = start_cursor
            
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            print(f"[!] httpx query failed: {e}")
            return []

    def _build_name_token_filter(self, tokens: List[str], kind: str = "title") -> Dict:
        """
        Build an OR filter across tokens for Name property.
        kind: "title" or "rich_text"
        """
        token_filters = []
        for tok in tokens:
            if not tok:
                continue
            token_filters.append({"property": "Name", kind: {"contains": tok}})
        
        if not token_filters:
            return {}
        return token_filters[0] if len(token_filters) == 1 else {"or": token_filters}

    def normalize_query(self, query: str) -> str:
        """Simple normalization: lowercase."""
        return query.lower().strip() if query else ""
    
    def _get_title(self, item: Dict) -> str:
        """Safe title extraction."""
        return self.safe_get_property(item.get("properties", {}), "Name", "title")

    @retry_with_backoff()
    def search_page(self, query: str, category_hint: str = None) -> Optional[str]:
        """
        Search for a page ID using 2-stage pipeline: Scoped DB -> Global Fallback.
        Implementation generally matches the contract provided.
        """
        if not query:
            return None
        
        norm_q = self.normalize_query(query)
        tokens = [t for t in norm_q.split() if t]
        if not tokens:
            return None
        
        candidates = []
        
        # STAGE 1: Scoped Database Query via httpx (Deterministic)
        try:
            name_filter = self._build_name_token_filter(tokens, kind="title")
            
            if category_hint:
                filter_params = {
                    "and": [
                        {"property": "Category", "select": {"equals": category_hint}},
                        name_filter
                    ]
                }
            else:
                filter_params = name_filter
            
            # Use httpx instead of SDK logic
            db_results = self._query_universe_db_httpx(filter_obj=filter_params, page_size=25)
            
            # If no results, retry with rich_text filter (schema variance)
            if not db_results:
                name_filter_rt = self._build_name_token_filter(tokens, kind="rich_text")
                if category_hint:
                    filter_params_rt = {
                        "and": [
                            {"property": "Category", "select": {"equals": category_hint}},
                            name_filter_rt
                        ]
                    }
                else:
                    filter_params_rt = name_filter_rt
                db_results = self._query_universe_db_httpx(filter_obj=filter_params_rt, page_size=25)
            
            for res in db_results:
                props = res.get("properties", {})
                title = self._get_title(res)
                
                # Extract aliases
                alias_prop = props.get("Alias", {})
                alias_list = []
                if alias_prop.get("type") == "multi_select":
                    alias_list = [a.get("name", "") for a in alias_prop.get("multi_select", [])]
                elif alias_prop.get("type") == "rich_text":
                    alias_list = [a.get("plain_text", "") for a in alias_prop.get("rich_text", [])]
                
                cat = self.safe_get_property(props, "Category", "select") or ""
                score = self._score_result(norm_q, title, alias_list, cat)
                
                if score > 0.4:
                    candidates.append({"id": res["id"], "score": score, "title": title})
        
        except Exception as e:
            print(f"[!] Scoped DB Search failed: {e}")
        
        # STAGE 2: Global Search Fallback (Only if no high-confidence candidate)
        if not candidates or max((c["score"] for c in candidates), default=0) < 0.8:
            try:
                # Global search requires 'search' endpoint
                url = f"{NOTION_API_BASE}/search"
                payload = {
                    "query": query,
                    "filter": {"property": "object", "value": "page"},
                    "page_size": 10
                }
                resp = self.client.post(url, json=payload)
                if resp.status_code == 200:
                    global_results = resp.json().get("results", [])
                    for res in global_results:
                        title = self._get_title(res)
                        score = self._score_result(norm_q, title)
                        if score > 0.3:
                            candidates.append({"id": res["id"], "score": score, "title": title})
            except Exception as e:
                print(f"[!] Global search fallback failed: {e}")
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[0]["id"]

    def _score_result(self, query: str, title: str, aliases: List[str] = None, category: str = "") -> float:
        """Simple scoring logic based on exact/partial matches."""
        query = query.lower()
        title = title.lower()
        
        if query == title:
            return 1.0
        if query in title:
            return 0.8
        
        if aliases:
            for alias in aliases:
                a_lower = alias.lower()
                if query == a_lower:
                    return 0.95
                if query in a_lower:
                    return 0.7
        return 0.0

    def find_entity(self, name: str, category: str = None) -> Optional[Dict]:
        """
        Smart entity retrieval with fallback chain (Contract).
        """
        # 1. Try category-specific if provided
        if category:
            results = self._query_universe_db_httpx(
                filter_obj={
                    "and": [
                        {"property": "Name", "title": {"equals": name}},
                        {"property": "Category", "select": {"equals": category}}
                    ]
                }
            )
            if results:
                return results[0]
        
        # 2. Fallback: search by name only
        results = self._query_universe_db_httpx(
            filter_obj={"property": "Name", "title": {"equals": name}}
        )
        return results[0] if results else None

    def get_entity_fuzzy(self, name: str) -> List[Dict]:
        """
        Find entities containing the search term.
        """
        return self._query_universe_db_httpx(
            filter_obj={"property": "Name", "title": {"contains": name}}
        )

    def list_all_universe_pages(self) -> List[Dict]:
        """Get ALL pages with pagination from Universe DB."""
        all_pages = []
        has_more = True
        start_cursor = None
        
        while has_more:
            results = self._query_universe_db_httpx(
                page_size=100,
                start_cursor=start_cursor
            )
            # The _query helper returns list, we need to handle pagination manually 
            # if we use that helper which strips metadata. 
            # Actually, the user contract helper returns 'results' list.
            # To get cursor, I need access to the full response in the loop.
            # Let's reimplement the loop using a direct call pattern for full response access.
            
            url = f"{NOTION_API_BASE}/databases/{UNIVERSE_DB_ID}/query"
            payload = {"page_size": 100}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            resp = self.client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            items = data.get("results", [])
            all_pages.extend(items)
            
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return all_pages

    def _calculate_search_score(self, item: Dict, query: str) -> float:
        """
        Weighted scoring with importance bias (Rulebook Implementation).
        """
        props = item.get("properties", {})
        
        # 1. Base Score (Fuzzy Match)
        title = self._get_title(item)
        base_score = self._score_result(query, title)
        
        # Also check aliases for base score match
        alias_prop = self.safe_get_property(props, "Alias", "multi_select")
        if alias_prop:
             # simple check if any alias matches
             for alias in alias_prop:
                 alias_score = self._score_result(query, alias)
                 if alias_score > base_score:
                     base_score = alias_score
        
        if base_score < 0.2:
            return 0.0 # Irrelevant
            
        # 2. Importance Multiplier
        importance = self.safe_get_property(props, "Importance", "select")
        importance_mult = {
            "Major": 3.0,
            "Supporting": 2.0,
            "Minor": 1.5,
            "Background": 1.0
        }.get(importance, 1.0)
        
        # 3. Anchor Node Boost
        is_anchor = self.safe_get_property(props, "Anchor Node", "checkbox")
        anchor_mult = 2.0 if is_anchor else 1.0
        
        # 4. Node Tier Boost
        node_tier = self.safe_get_property(props, "Node Tier", "select")
        tier_mult = {
            "Tier 1": 2.5,
            "Tier 2": 2.0,
            "Tier 3": 1.5,
            "Background": 1.0
        }.get(node_tier, 1.0)
        
        # 5. Canon Priority
        canon_status = self.safe_get_property(props, "Canon Status", "select")
        canon_mult = {
            "Canon Locked": 1.5,
            "Soft Canon": 1.2,
            "Pending Review": 1.0,
            "Contradicted": 0.8,
            "Replaced": 0.5
        }.get(canon_status, 1.0)
        
        # 6. Importance Score Additive Boost (0-100 -> 0.0-1.0)
        imp_score_val = self.safe_get_property(props, "Importance Score", "number")
        score_boost = (imp_score_val / 100.0) if imp_score_val else 0.0
        
        # Final Calculation
        final_score = (base_score * importance_mult * anchor_mult * tier_mult * canon_mult) + score_boost
        
        return final_score

    def contextual_search(self, query: str, context_filter: Dict = None) -> List[Dict]:
        """
        Advanced search with implicit filters and weighted ranking.
        """
        if not query:
            return []
            
        norm_q = self.normalize_query(query)
        
        # 1. Build optimized filter
        # Start with context if provided, else broad name search
        base_filter = self._build_name_token_filter(norm_q.split(), "title")
        
        if context_filter:
            final_filter = {"and": [context_filter, base_filter]}
        else:
            final_filter = base_filter
            
        # 2. Fetch Candidates (Stage 1)
        results = self._query_universe_db_httpx(filter_obj=final_filter, page_size=50)
        
        # 3. Re-Rank with Multi-Tier Score
        scored = []
        for item in results:
            score = self._calculate_search_score(item, norm_q)
            if score > 0:
                scored.append((item, score))
                
        # Sort desc by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the items
        return [s[0] for s in scored]

    def calculate_importance_score(self, props: Dict) -> int:
        """
        Calculates Importance Score (0-100) based on SOP.
        
        Base Score:
        - Major = 90
        - Supporting = 65
        - Minor = 37
        - Background = 17
        
        Modifiers:
        + Anchor Node = true → +20
        + Canon Status = "Canon Locked" → +10
        + Has Description → +5
        + Has Connections → +5
        + Appears In → +5 per appearance (cap +15)
        """
        importance = self.safe_get_property(props, "Importance", "select")
        base_map = {
            "Major": 90,
            "Supporting": 65,
            "Minor": 37,
            "Background": 17
        }
        score = base_map.get(importance, 0)
        
        # Modifiers
        if self.safe_get_property(props, "Anchor Node", "checkbox"):
            score += 20
            
        canon = self.safe_get_property(props, "Canon Status", "select")
        if canon == "Canon Locked":
            score += 10
            
        desc = self.safe_get_property(props, "Description", "rich_text")
        if desc:
            score += 5
            
        # Connections (Relation) checks
        # "Connected To" and "Connected To 1"
        conns1 = props.get("Connected To", {}).get("relation", [])
        conns2 = props.get("Connected To 1", {}).get("relation", [])
        if conns1 or conns2:
            score += 5
            
        # Appears In
        appears_in = self.safe_get_property(props, "Appears In", "multi_select") or []
        app_bonus = min(len(appears_in) * 5, 15)
        score += app_bonus
        
        # KEYWORD OVERRIDES (User Request)
        # Force high importance for central lore concepts regardless of metadata
        title = self._get_title({"properties": props}).lower()
        
        # Primary keywords - if title contains ANY of these, boost to 90+
        primary_keywords = ["shadow dweller", "kage tanak", "yasuke", "oda nobunaga"]
        
        # Xoah-related - if title contains "xoah" in any form, boost to 90+
        is_xoah_related = "xoah" in title
        
        # Check primary keywords
        has_primary = any(kw in title for kw in primary_keywords)
        
        if is_xoah_related or has_primary:
            score += 40
            # Ensure it hits Major tier if it was low
            if score < 90:
                score = max(score, 90)
        
        return min(max(score, 0), 100)

    def calculate_canon_confidence(self, props: Dict) -> int:
        """
        Calculates Canon Confidence (0-100) based on SOP.
        
        Base Confidence:
        - Canon Locked = 100
        - Soft Canon = 80
        - Pending Review = 50
        - Contradicted = 20
        - Replaced = 5
        
        Modifiers:
        + Has Source URL → +10
        + Has Description → +5
        + Timeline Year set → +5
        + No Continuity Flags → +10
        - Has "Contradiction" flag → -20
        - Has "Needs Retcon" flag → -15
        """
        canon = self.safe_get_property(props, "Canon Status", "select")
        base_map = {
            "Canon Locked": 100,
            "Soft Canon": 80,
            "Pending Review": 50,
            "Contradicted": 20,
            "Replaced": 5
        }
        confidence = base_map.get(canon, 0)
        
        # Modifiers
        if self.safe_get_property(props, "Source URL", "url"):
            confidence += 10
            
        if self.safe_get_property(props, "Description", "rich_text"):
            confidence += 5
            
        if self.safe_get_property(props, "Timeline Year", "number") is not None:
            confidence += 5
            
        flags = self.safe_get_property(props, "Continuity Flags", "multi_select") or []
        if not flags:
            confidence += 10
        else:
            if "Contradiction" in flags:
                confidence -= 20
            if "Needs Retcon" in flags:
                confidence -= 15
                
        return min(max(confidence, 0), 100)

    def safe_get_property(self, props: dict, prop_name: str, prop_type: str) -> Any:
        """Null-safe property extraction (Contract)."""
        prop = props.get(prop_name, {})
        
        if prop_type == "title":
            arr = prop.get("title", [])
            return arr[0].get("text", {}).get("content", "") if arr else ""
        
        elif prop_type == "rich_text":
            arr = prop.get("rich_text", [])
            return arr[0].get("text", {}).get("content", "") if arr else ""
        
        elif prop_type == "select":
            sel = prop.get("select")
            return sel.get("name") if sel else None
        
        elif prop_type == "multi_select":
            arr = prop.get("multi_select", [])
            val = [item.get("name") for item in arr if item.get("name")]
            return val
        
        elif prop_type == "status":
            status = prop.get("status")
            return status.get("name") if status else None
        
        elif prop_type == "number":
            return prop.get("number")
        
        elif prop_type == "url":
            return prop.get("url")
        
        elif prop_type == "date":
            date = prop.get("date")
            return date.get("start") if date else None
        
        return None

    def create_ops_task(self, title: str, status: str = "Ready", properties: Dict = None) -> Optional[str]:
        """
        Creates a row in the Ops/Tasks Database (Autonomy Control Plane).
        """
        # Placeholder ID - in real usage this would be configurable or discovered
        OPS_DB_ID = "2e7ca671311e80e6ae14eded33870f70" 
        
        target_props = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Status": {"status": {"name": status}},
        }
        
        # Merge optional properties (Ralph Schema)
        if properties:
            for key, val in properties.items():
                if key == "Exit Signal":
                    target_props[key] = {"checkbox": val}
                elif key == "Loop Count":
                    target_props[key] = {"number": val}
                elif key == "Risk Score":
                    target_props[key] = {"number": val}
                elif key == "Autonomy Status":
                    target_props[key] = {"select": {"name": val}}
                elif key == "Session ID":
                    target_props[key] = {"rich_text": [{"text": {"content": val}}]}
                    
        url = f"{NOTION_API_BASE}/pages"
        payload = {
            "parent": {"database_id": OPS_DB_ID},
            "properties": target_props
        }
        
        try:
            resp = self.client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["id"]
        except Exception as e:
            print(f"❌ Failed to create Ops Task: {e}")
            return None

if __name__ == "__main__":
    # Self-test
    try:
        service = NotionService()
        print(f"✅ Service initialized. Token: {service.token[:4]}...")
        
        # Test Search
        results = service.get_entity_fuzzy("Veil")
        print(f"🔍 Fuzzy search for 'Veil' found {len(results)} items.")
        if results:
            print(f"   First hit: {service._get_title(results[0])}")
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
