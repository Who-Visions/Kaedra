"""
KAEDRA v1.0 - Notion Service Bridge
Provides a 2-stage search pipeline (Local SQLite + Notion API) and high-level
abstractions for managing the VeilVerse cinematic universe.
"""

import functools
import random
import re
import time
from datetime import datetime
from typing import Optional, List, Any, Dict, Tuple

import httpx
from notion_client import Client, APIResponseError

from kaedra.core.config import NOTION_TOKEN

# Local SQLite Query Layer (Fast Path)
try:
    from kaedra.services.local_query import get_local_query_service
    _LOCAL_QUERY = get_local_query_service()
except ImportError:
    _LOCAL_QUERY = None

# Gold Standard IDs (Kaedra Rulebook) - Dav3's Space (Jan 2026)
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
UNIVERSE_DB_ID = "2e5ca671-311e-811f-b3d7-c7f3b9150afe"  # VeilVerse Universe Best
DATA_SOURCE_ID = "2e5ca671-311e-8182-abfc-000be91b3354"  # Data source for SQL

# Logic Caches (v7.17)
_SEARCH_CACHE: Dict[str, Tuple[float, List[str]]] = {}
_LIST_CACHE: Dict[str, Tuple[float, List[str]]] = {}
CACHE_TTL = 600  # 10 minutes

# Global Init Flag
_NOTION_INIT_LOGGED = False

def retry_with_backoff(initial_delay: float = 15.0, max_retries: int = 5):
    """
    Decorator for exponential backoff on 429 (Rate Limit) errors.
    Starts at 15 seconds per user requirement.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except APIResponseError as e:
                    if e.status == 429:
                        wait = delay + random.uniform(0, 1)
                        print(f"[!] Notion Rate Limit (429). Retrying in {wait:.1f}s... "
                              f"(Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait)
                        delay *= 2
                    else:
                        raise e
                except (RuntimeError, ValueError, AttributeError) as e:
                    err_str = str(e).lower()
                    if any(k in err_str for k in ["429", "resource_exhausted", "rate limit"]):
                        wait = delay + random.uniform(0, 1)
                        print(f"[!] Rate Limit detected. Retrying in {wait:.1f}s... "
                              f"(Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait)
                        delay *= 2
                    else:
                        raise e
            return func(*args, **kwargs) # Last attempt
        return wrapper
    return decorator

class NotionService:
    """
    Service for interacting with Notion databases and pages.
    """
    # pylint: disable=too-many-public-methods
    def __init__(self):
        global _NOTION_INIT_LOGGED
        self._client = None

        # Lazy initialization check
        if not NOTION_TOKEN and not _NOTION_INIT_LOGGED:
             # Just log once if missing, but don't fail init
            print("[!] Notion Token not found. Notion service disabled.")
            _NOTION_INIT_LOGGED = True

    @property
    def client(self):
        """Lazy-loaded Notion Client."""
        if self._client is None and NOTION_TOKEN:
            try:
                self._client = Client(auth=NOTION_TOKEN)
                global _NOTION_INIT_LOGGED
                if not _NOTION_INIT_LOGGED:
                    print("[✅] Notion Service Initialized")
                    _NOTION_INIT_LOGGED = True
            except (RuntimeError, ValueError, AttributeError) as init_err:
                print(f"[!] Failed to initialize Notion Service: {init_err}")
                self._client = None
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def __getstate__(self):
        """Exclude client from pickling."""
        state = self.__dict__.copy()
        if "_client" in state:
            del state["_client"]
        return state

    def __setstate__(self, state):
        """Restore state."""
        self.__dict__.update(state)
        self._client = None

    def normalize_query(self, query: str) -> str:
        """Normalize query for improved matching."""
        if not query:
            return ""
        # Lowercase, strip punctuation, replace -/_ with space, collapse whitespace
        q = query.lower().strip()
        q = re.sub(r"[-_]", " ", q)
        q = re.sub(r"[^\w\s]", "", q)
        q = re.sub(r"^(a|an|the|my|his|her|its|our|their)\s+", "", q)
        return " ".join(q.split())

    def score_result(self,
                     query: str,
                     title: str,
                     aliases: List[str] = None,
                     category: str = "") -> float:
        """
        Industrial ranking logic based on exact matches, aliases, and word boundaries.
        """
        q = self.normalize_query(query)
        t = self.normalize_query(title)
        al = [self.normalize_query(a) for a in (aliases or [])]

        if not q or not t:
            return 0.0

        # 1. Base Score
        score = 0.0
        if q == t:
            score = 1.0
        elif al and q in al:
            score = 0.95
        elif q in t:
            # Substring match starts at 0.7
            score = 0.7

            # Position Bonus (Earlier in title is better)
            pos = t.find(q)
            if pos == 0:
                score += 0.1
            elif pos < 15:
                score += 0.05

            # Whole Word Bonus
            # Use regex to check for word boundaries or start/end
            pattern = rf"(^|\s){re.escape(q)}(\s|$)"
            if re.search(pattern, t):
                score += 0.1

            # Overlap Ratio (Shorter titles are more specific)
            overlap_ratio = len(q) / len(t)
            score += (overlap_ratio * 0.1)
        else:
            # Token overlap (last resort)
            q_sets = set(q.split())
            t_sets = set(t.split())
            overlap = len(q_sets & t_sets)
            if overlap:
                score = (overlap / max(len(q_sets), len(t_sets))) * 0.6

        # 2. Category Boost
        if category:
            cat_low = category.lower()
            if cat_low in ["character", "location", "item"]:
                score += 0.15
            elif cat_low in ["quest", "faction"]:
                score += 0.05

        return min(1.0, score)

    def _get_notion_headers(self) -> dict:
        """Build headers for Notion API requests."""
        return {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        }

    def _query_database_httpx(self, database_id: str, filter_obj: dict = None, limit: int = 100) -> List[Dict]:
        """Query a Notion database using httpx with pagination support."""
        url = f"{NOTION_API_BASE}/databases/{database_id}/query"
        results = []
        has_more = True
        start_cursor = None

        try:
            with httpx.Client(timeout=30.0) as client:
                while has_more and len(results) < limit:
                    payload = {"page_size": min(limit - len(results), 100)}
                    if filter_obj: payload["filter"] = filter_obj
                    if start_cursor: payload["start_cursor"] = start_cursor

                    response = client.post(url, headers=self._get_notion_headers(), json=payload)
                    response.raise_for_status()
                    data = response.json()
                    results.extend(data.get("results", []))
                    has_more = data.get("has_more", False)
                    start_cursor = data.get("next_cursor")
                    if not start_cursor: break
                return results
        except (httpx.HTTPStatusError, httpx.RequestError) as http_err:
            print(f"[!] httpx query failed: {http_err}")
            return results  # Return whatever we got

    def _build_token_filter(self, query: str) -> Dict:
        """Build an OR filter: full query exact, and token contains."""
        norm_q = self.normalize_query(query)
        tokens = [t for t in norm_q.split() if t]

        token_filters = []
        # Full query match (Highest priority)
        token_filters.append({"property": "Name", "title": {"equals": query}})
        token_filters.append({"property": "Alias", "multi_select": {"contains": query}})

        # Token-based matches (Medium priority)
        for tok in tokens:
            if not tok or len(tok) < 3: continue
            token_filters.append({"property": "Name", "title": {"contains": tok}})
            token_filters.append({"property": "Alias", "multi_select": {"contains": tok}})
            token_filters.append({"property": "Description", "rich_text": {"contains": tok}})
            token_filters.append({"property": "Notes", "rich_text": {"contains": tok}})

        if not token_filters:
            return {}
        return token_filters[0] if len(token_filters) == 1 else {"or": token_filters[:90]}

    @retry_with_backoff()
    def search_page(self, query: str, category_hint: str = None) -> Optional[str]:
        """Search for a page ID using 2-stage pipeline: Scoped DB -> Global Fallback."""
        if not self.client or not query:
            return None

        norm_q = self.normalize_query(query)
        cache_key = f"search:{norm_q}:{category_hint or 'all'}"
        now = time.time()

        if cache_key in _SEARCH_CACHE:
            ts, val = _SEARCH_CACHE[cache_key]
            if now - ts < CACHE_TTL:
                return val[0] if val else None

        tokens = [t for t in norm_q.split() if t]
        if not tokens:
            return None

        candidates: List[Dict[str, Any]] = []

        # STAGE 1: Scoped Database Query via httpx (Deterministic)
        try:
            name_filter = self._build_token_filter(query)
            if category_hint:
                filter_params = {
                    "and": [
                        {"property": "Category", "select": {"equals": category_hint}},
                        name_filter
                    ]
                }
            else:
                filter_params = name_filter

            db_results = self._query_database_httpx(UNIVERSE_DB_ID, filter_params)

            for res in db_results:
                props = res.get("properties", {})
                title = self._get_title(res)

                alias_prop = props.get("Alias", {})
                alias_list: List[str] = []
                if alias_prop.get("type") == "multi_select":
                    alias_list = [a.get("name", "") for a in alias_prop.get("multi_select", [])]
                elif alias_prop.get("type") == "rich_text":
                    alias_list = [a.get("plain_text", "") for a in alias_prop.get("rich_text", [])]

                cat_select = props.get("Category", {}).get("select")
                cat = cat_select.get("name", "") if cat_select else ""

                score = self.score_result(query, title, alias_list, cat)
                if score > 0.4:
                    candidates.append({"id": res["id"], "score": score, "title": title})
                    print(f"  [Candidate] '{title}' (Score: {score:.3f}) - [S1]")

        except (RuntimeError, ValueError, AttributeError) as s1_err:
            print(f"[!] Scoped DB Search failed: {s1_err}")

        # STAGE 2: Global Search Fallback (Only if no high-confidence candidate)
        if not candidates or max(c["score"] for c in candidates) < 0.8:
            try:
                # SDK search is fine for global fallback
                global_results = self.client.search(
                    query=query,
                    filter={"property": "object", "value": "page"},
                    page_size=10
                ).get("results", [])

                for res in global_results:
                    title = self._get_title(res)
                    props = res.get("properties", {})

                    alias_list: List[str] = []
                    alias_prop = props.get("Alias", {})
                    if alias_prop.get("type") == "multi_select":
                        alias_list = [a.get("name", "") for a in alias_prop.get("multi_select", [])]
                    elif alias_prop.get("type") == "rich_text":
                        alias_list = [a.get("plain_text", "") for a in alias_prop.get("rich_text", [])]

                    cat_select = props.get("Category", {}).get("select")
                    cat = cat_select.get("name", "") if cat_select else ""

                    score = self.score_result(query, title, alias_list, cat)
                    if score > 0.3:
                        candidates.append({"id": res["id"], "score": score, "title": title})
                        print(f"  [Candidate] '{title}' (Score: {score:.3f}) - [S2]")
            except (RuntimeError, ValueError, AttributeError) as s2_err:
                print(f"[!] Global search fallback failed: {s2_err}")

        if not candidates:
            return None

        candidates.sort(key=lambda x: x["score"], reverse=True)
        best = candidates[0]

        _SEARCH_CACHE[cache_key] = (now, [best["id"]])
        return best["id"]

    def _get_title(self, page_res: dict) -> str:
        """Helper to extract title from page results."""
        props = page_res.get("properties", {})
        title_list = props.get("title", {}).get("title", []) or props.get("Name", {}).get("title", [])
        if not title_list:
            title_list = page_res.get("title", [])
        return title_list[0].get("plain_text", "") if title_list else "Untitled"

    @retry_with_backoff()
    def global_search(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search across the entire workspace for pages or databases."""
        if not self.client:
            return []
        try:
            print(f"[Notion] Global Workspace Search: '{query}'...")
            results = []
            has_more = True
            start_cursor = None

            while has_more and len(results) < limit:
                response = self.client.search(
                    query=query,
                    page_size=min(limit - len(results), 100),
                    start_cursor=start_cursor
                )
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                if not start_cursor: break

            matches = []
            for res in results:
                obj_type = res.get("object")
                # Handle Pages
                if obj_type == "page":
                    props = res.get("properties", {})
                    title_prop = props.get("title") or props.get("Name") or {}
                    title_list = title_prop.get("title", [])
                    title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"
                    matches.append({"type": "PAGE", "title": title, "id": res["id"]})
                # Handle Databases
                elif obj_type == "database":
                    title_list = res.get("title", [])
                    title = title_list[0].get("plain_text", "Untitled DB") if title_list else "Untitled DB"
                    matches.append({"type": "DB", "title": title, "id": res["id"]})
            return matches
        except (RuntimeError, ValueError, AttributeError) as glob_err:
            print(f"[!] Notion Global Search Error: {glob_err}")
            return []

    @retry_with_backoff()
    def append_children(self, block_id: str, children: List[Any]):
        """Append blocks to a page or block."""
        if not self.client:
            return
        try:
            self.client.blocks.children.append(block_id=block_id, children=children)
            print(f"[Notion] Appended {len(children)} blocks to {block_id}")
        except (RuntimeError, ValueError, AttributeError) as append_err:
            print(f"[!] Notion Append Error: {append_err}")

    @retry_with_backoff()
    def create_page(self,
                    title: str,
                    parent_page_id: str = None,
                    content_blocks: List[Dict] = None) -> Optional[str]:
        """Create a new page with optional content."""
        if not self.client:
            return None

        try:
            # Resulting Parent ID
            target_parent_id = parent_page_id

            # KNOWN IDs (Autodiscovered from Dav3's Space - Jan 2026)
            KNOWN_UNIVERSE_ID = "2e5ca671-311e-811f-8229-d04a1f430059"  # Ai with Dav3 Cinematic Universe

            # If no parent specified, try to find the Root Universe Page
            if not target_parent_id:
                # 1. Try Known ID (Fastest/Safest)
                try:
                    self.client.pages.retrieve(KNOWN_UNIVERSE_ID)
                    target_parent_id = KNOWN_UNIVERSE_ID
                except:
                    pass

                # 2. Key Parent Search
                if not target_parent_id:
                    target_parent_id = self.search_page("Veil Verse") or self.search_page("Ai with Dav3 Cinematic Universe")

            if not target_parent_id:
                print("[!] Cannot create page: No parent page found.")
                return None

            # Default Content if none provided
            children = content_blocks if content_blocks else [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": f"Welcome to {title}"}}]
                    }
                }
            ]

            new_page = self.client.pages.create(
                parent={"page_id": target_parent_id},
                properties={
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                children=children
            )
            page_id = new_page["id"]
            print(f"[✅] Created Notion Page: '{title}' (ID: {page_id})")
            return page_id

        except (RuntimeError, ValueError, AttributeError) as create_err:
            print(f"[!] Notion Create Page Error: {create_err}")
            return None

    @retry_with_backoff()
    def create_database(self, parent_id: str, title: str, properties: Dict) -> Optional[str]:
        """Create a new database with specified properties."""
        if not self.client:
            return None
        try:
            new_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_id},
                title=[{"type": "text", "text": {"content": title}}],
                properties=properties
            )
            print(f"[✅] Created Notion Database: '{title}'")
            return new_db["id"]
        except (RuntimeError, ValueError, AttributeError) as db_err:
            print(f"[!] Notion Create DB Error: {db_err}")
            return None

    @retry_with_backoff()
    def create_comment(self, page_id: str, text: str) -> Optional[str]:
        """Add a comment to a page."""
        if not self.client:
            return None
        try:
            comment = self.client.comments.create(
                parent={"page_id": page_id},
                rich_text=[{"text": {"content": text}}]
            )
            print(f"[✅] Added Comment to {page_id}")
            return comment["id"]
        except (RuntimeError, ValueError, AttributeError) as comm_err:
            print(f"[!] Notion Comment Error: {comm_err}")
            return None

    @retry_with_backoff()
    def get_users(self) -> List[Dict]:
        """List all users in the workspace."""
        if not self.client:
            return []
        try:
            users = self.client.users.list().get("results", [])
            return [{"id": u["id"], "name": u.get("name", "Unknown"), "type": u.get("type")}
                    for u in users]
        except (RuntimeError, ValueError, AttributeError) as user_err:
            print(f"[!] Notion Get Users Error: {user_err}")
            return []

    def log_universe_idea(self, text: str):
        """High-level helper to log an idea to the Universe control page."""
        if not self.client: return

        # 1. Find or Create "Ai with Dav3 Cinematic Universe" page
        page_id = self.search_page("Ai with Dav3 Cinematic Universe")
        if not page_id:
             # Try generic search
            page_id = self.search_page("Cinematic Universe")

        if not page_id:
            print("[!] Could not find 'Cinematic Universe' page in Notion. Please create it and share with integration.")
            return

        # 2. Append the text
        paragraph_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }
        self.append_children(page_id, [paragraph_block])

    def _extract_id(self, text: str) -> Optional[str]:
        """Extract Notion UUID from URL or text (handles hyphenated and 32-char hex)."""
        # Standardize: remove hyphens to check for 32-char hex
        clean_text = text.replace("-", "")
        # Check if the entire text is a valid UUID (fast path)
        if len(clean_text) == 32 and re.fullmatch(r"[a-f0-9]+", clean_text, re.IGNORECASE):
            return text  # Return original

        # Regex for 32-char hex within a URL
        match = re.search(r'([a-f0-9]{32})', clean_text)
        if match:
            raw = match.group(1)
            return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
        return None


    def read_page_content(self, page_identifier: str) -> Optional[str]:
        """Read page content. Accepts Title, URL, or ID."""
        if not self.client: return None

        # 1. Try to extract ID from URL/text
        page_id = self._extract_id(page_identifier)

        # 2. If no ID found, search by Title
        if not page_id:
            page_id = self.search_page(page_identifier)

        if not page_id:
            return f"[Page '{page_identifier}' not found]"

        try:
            text_parts = []

            # [ENHANCEMENT] Database Property Extraction
            # If the page has properties, dump the useful ones first
            props = self.client.pages.retrieve(page_id).get("properties", {})
            if props:
                meta = []
                # Priority Fields
                for key in ["Canon Status", "Universe Era", "Category", "Power Level", "Status", "Tags"]:
                    if val := self._extract_prop_val(props.get(key)):
                        meta.append(f"**{key}**: {val}")

                # Text Fields (Description, Notes)
                for key in ["Description", "Notes", "Abilities/Powers"]:
                    if val := self._extract_prop_val(props.get(key)):
                        meta.append(f"\n**{key}**:\n{val}")

                if meta:
                    text_parts.append("### [METADATA]\n" + "\n".join(meta) + "\n\n### [BODY]")

            has_more = True
            start_cursor = None
            while has_more:
                response = self.client.blocks.children.list(block_id=page_id, start_cursor=start_cursor)
                blocks = response.get("results", [])
                for block in blocks:
                    block_type = block.get("type")
                    if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "callout", "quote"]:
                        rich_text = block.get(block_type, {}).get("rich_text", [])
                        prefix = ""
                        if block_type == "callout": prefix = "💡 " # Emojis are in 'icon', but let's just mark it
                        if block_type == "quote": prefix = "> "

                        text = "".join([rt.get("plain_text", "") for rt in rich_text])
                        if text:
                            text_parts.append(f"{prefix}{text}")
                    elif block_type == "image":
                        image_data = block.get("image", {})
                        url = ""
                        if "file" in image_data:
                            url = image_data["file"].get("url", "")
                        elif "external" in image_data:
                            url = image_data["external"].get("url", "")

                        if url:
                            text_parts.append(f"[IMAGE FOUND: {url}]")
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                if not has_more:
                    break

            return "\n".join(text_parts) if text_parts else "[Page is empty]"
        except (RuntimeError, ValueError, AttributeError) as read_err:
            return f"[Error reading page: {read_err}]"

    def _extract_prop_val(self, prop: Dict) -> str:
        """Helper to extract plain text using Rulebook null-safe patterns."""
        if not prop: return ""
        dtype = prop.get("type")

        try:
            if dtype == "title":
                arr = prop.get("title", [])
                return arr[0].get("text", {}).get("content", "") if arr else ""
            elif dtype == "rich_text":
                arr = prop.get("rich_text", [])
                return arr[0].get("text", {}).get("content", "") if arr else ""
            elif dtype == "select":
                sel = prop.get("select")
                return sel.get("name", "") if sel else ""
            elif dtype == "multi_select":
                arr = prop.get("multi_select", [])
                return ", ".join([item.get("name", "") for item in arr if item.get("name")])
            elif dtype == "status":
                stat = prop.get("status")
                return stat.get("name", "") if stat else ""
            elif dtype == "number":
                return str(prop.get("number", ""))
            elif dtype == "url":
                return prop.get("url", "")
            elif dtype == "date":
                d_obj = prop.get("date")
                return d_obj.get("start", "") if d_obj else ""
        except (KeyError, IndexError, AttributeError):
            return ""
        return ""


    def list_subpages(self, parent_title: str = "Veil Verse") -> List[str]:
        """List all child pages under a parent page. Cached for 10 mins."""
        if not self.client: return []

        # Check Cache First
        now = time.time()
        if parent_title in _LIST_CACHE:
            ts, items = _LIST_CACHE[parent_title]
            if now - ts < CACHE_TTL:
                return items

        # Try primary title
        page_id = self.search_page(parent_title)

        # Fallback 1: "VeilVerse" (no space variant)
        if not page_id:
            print(f"[Notion] '{parent_title}' not found. Trying 'VeilVerse'...")
            page_id = self.search_page("VeilVerse")

        # Fallback 2: "Cinematic Universe"
        if not page_id:
            print(f"[Notion] 'VeilVerse' not found. Trying 'Cinematic Universe'...")
            page_id = self.search_page("Cinematic Universe")

        if not page_id:
            print(f"[Notion] Index Scan Failed: Could not find parent page '{parent_title}' or fallbacks.")
            return []

        print(f"[Notion] Scanning children of {page_id}...")

        try:
            sub_items = []
            has_more = True
            start_cursor = None

            while has_more:
                response = self.client.blocks.children.list(block_id=page_id, start_cursor=start_cursor)
                blocks = response.get("results", [])
                for block in blocks:
                    b_type = block.get("type")
                    if b_type == "child_page":
                        title = block.get("child_page", {}).get("title", "Untitled")
                        sub_items.append(f"[PAGE] {title}")
                    elif b_type == "child_database":
                        title = block.get("child_database", {}).get("title", "Untitled")
                        sub_items.append(f"[DB] {title}")

                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                if not has_more: break

            _LIST_CACHE[parent_title] = (now, sub_items)
            return sub_items
        except (RuntimeError, ValueError, AttributeError) as list_err:
            print(f"[!] Error listing sub_items: {list_err}")
            return []

    def get_universe_summary(self) -> str:
        """Get a categorized summary of all universe content for context injection."""
        if not self.client: return "[Notion not connected]"

        # 1. Get raw entities from current Universe DB
        results = self._query_database_httpx(UNIVERSE_DB_ID, limit=500)

        stats = {}
        examples = {}

        for res in results:
            cat_prop = res.get("properties", {}).get("Category")
            cat = self._extract_prop_val(cat_prop) or "Uncategorized"
            stats[cat] = stats.get(cat, 0) + 1
            if cat not in examples:
                examples[cat] = []
            if len(examples[cat]) < 3:
                examples[cat].append(self._get_title(res))

        summary_parts = [f"Universe Profile ({len(results)} entities):"]
        for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            ex_list = ", ".join(examples[cat])
            summary_parts.append(f"- {cat} ({count}): {ex_list}")

        return "\n".join(summary_parts)

    def list_entities_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Fetch entities filtered by category."""
        if not self.client: return []
        filter_params = {"property": "Category", "select": {"equals": category}}
        results = self._query_database_httpx(UNIVERSE_DB_ID, filter_params, limit=limit)
        return [{"id": r["id"], "title": self._get_title(r)} for r in results]
    def append_to_page(self, page_identifier: str, text: str) -> str:
        """Append text to a page by Title, URL, or ID."""
        if not self.client: return "[Notion not connected]"

        # 1. Try ID/URL
        page_id = self._extract_id(page_identifier)

        # 2. Try Title
        if not page_id:
            page_id = self.search_page(page_identifier)

        if not page_id:
            return f"[Page '{page_identifier}' not found]"

        paragraph_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }

        try:
            self.append_children(page_id, [paragraph_block])
            return f"[Updated '{page_identifier}' with new lore]"
        except (RuntimeError, ValueError, AttributeError) as app_err:
            return f"[Error updating page: {app_err}]"

    @retry_with_backoff()
    def ensure_script_index_database(self, parent_page_id: Optional[str] = None) -> Optional[str]:
        """Find or create the 'Master Script Index' database."""
        if not self.client: return None

        # 1. Search for existing database
        try:
            results = self.client.search(
                query="Master Script Index",
                filter={"property": "object", "value": "database"}
            ).get("results", [])

            for res in results:
                title_list = res.get("title", [{}])
                if title_list[0].get("plain_text") == "Master Script Index":
                    return res["id"]
        except (RuntimeError, ValueError, AttributeError) as sc_err:
            print(f"[!] Notion DB Search Error: {sc_err}")

        # 2. Create if not found
        if not parent_page_id:
            parent_page_id = self.search_page("Ai with Dav3 Cinematic Universe") or self.search_page("VeilVerse")

        if not parent_page_id:
            print("[!] Cannot create Script Index: No parent page found.")
            return None

        try:
            new_db = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": "Master Script Index"}}],
                properties={
                    "Project Title": {"title": {}},
                    "Status": {"select": {"options": [
                        {"name": "Concept", "color": "gray"},
                        {"name": "Outline", "color": "blue"},
                        {"name": "Drafting", "color": "yellow"},
                        {"name": "Polish", "color": "green"},
                        {"name": "Complete", "color": "purple"}
                    ]}},
                    "Drive URL": {"url": {}},
                    "Last Sync": {"date": {}},
                    "Milestones": {"rich_text": {}}
                }
            )
            db_id = new_db["id"]
            print(f"[✅] Created Notion Database: 'Master Script Index' (ID: {db_id})")
            return db_id
        except (RuntimeError, ValueError, AttributeError) as db_cr_err:
            print(f"[!] Notion DB Create Error: {db_cr_err}")
            return None

    @retry_with_backoff()
    def list_all_databases(self) -> List[str]:
        """List all accessible databases in the workspace (Paginated)."""
        if not self.client:
            return []
        try:
            results = []
            has_more = True
            start_cursor = None

            while has_more:
                # Search ALL objects
                response = self.client.search(
                    start_cursor=start_cursor,
                    page_size=100
                )
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                if not start_cursor: break

            dbs = [r for r in results if r.get("object") == "database"]
            return [f"[DB] {db['title'][0]['plain_text']} (ID: {db['id']})"
                    for db in dbs if db.get("title")]
        except (RuntimeError, ValueError, AttributeError) as list_db_err:
            print(f"[!] Notion List DB Error: {list_db_err}")
            return []

    @retry_with_backoff()
    def sync_roadmap_item(self, title: str, drive_url: str, status: str = "Outline", milestones: str = "") -> str:
        """Create or update a script entry in the Master Script Index."""
        if not self.client: return "[Notion not connected]"

        db_id = self.ensure_script_index_database()
        if not db_id: return "[Could not find/create Master Script Index]"

        from datetime import datetime
        now_iso = datetime.now().isoformat()

        try:
            query_filter = {"property": "Project Title", "title": {"equals": title}}
            query_results = self._query_database_httpx(db_id, query_filter)

            properties = {
                "Project Title": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": status}},
                "Drive URL": {"url": drive_url},
                "Last Sync": {"date": {"start": now_iso}},
                "Milestones": {"rich_text": [{"text": {"content": milestones}}]}
            }

            if query_results:
                page_id = query_results[0]["id"]
                self.client.pages.update(page_id=page_id, properties=properties)
                return f"[Updated Notion Index: '{title}']"
            else:
                self.client.pages.create(parent={"database_id": db_id}, properties=properties)
                return f"[Created Notion Entry: '{title}']"

        except Exception as e:
            return f"[Error syncing to Notion: {e}]"

    def find_entity(self, name: str, category: str = None) -> Optional[Dict]:
        """Smart entity retrieval with fallback chain (Rulebook compliant).
        
        Query Flow:
        1. Local SQLite (fast, ~5ms)
        2. Notion API (fallback, ~500ms)
        """
        # FAST PATH: Local SQLite first
        if _LOCAL_QUERY and _LOCAL_QUERY.is_available():
            local_result = _LOCAL_QUERY.find_entity(name, category)
            if local_result:
                return local_result
        
        # FALLBACK: Notion API
        if not self.client: return None

        # 1. Try category-specific if provided
        if category:
            filter_params = {
                "and": [
                    {"property": "Name", "title": {"equals": name}},
                    {"property": "Category", "select": {"equals": category}}
                ]
            }
            results = self._query_database_httpx(UNIVERSE_DB_ID, filter_params)
            if results: return results[0]

        # 2. Fallback: search by name only (handles uncategorized)
        results = self._query_database_httpx(UNIVERSE_DB_ID, {"property": "Name", "title": {"equals": name}})
        return results[0] if results else None

    def get_entity(self, name: str) -> Optional[Dict]:
        """Find any entity by name, regardless of Category."""
        return self.find_entity(name)

