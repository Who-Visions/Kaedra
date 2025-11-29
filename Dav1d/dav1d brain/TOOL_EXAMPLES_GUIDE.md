# Advanced Tool Use - Examples Guide

## Why Tool Examples Matter

JSON schemas define **what's valid**, but can't express **usage patterns**:
- When to include optional parameters
- Which combinations make sense  
- What conventions your API expects
- Format ambiguities (dates, IDs, etc.)

**Result:** Examples improve parameter accuracy from 72% to 90%

---

## Example Format for Gemini

### Method 1: Embedded in Description (Recommended)

```python
from google.genai.types import FunctionDeclaration

search_youtube = FunctionDeclaration(
    name="search_youtube_videos",
    description="""Search YouTube for videos.
    
    Examples:
    1. Music search:
       {"query": "lofi hip hop beats", "max_results": 10, "order": "viewCount"}
    
    2. Tutorial search:
       {"query": "Python async tutorial", "max_results": 5, "order": "relevance"}
    
    3. Recent uploads:
       {"query": "AI news", "max_results": 3, "order": "date"}
    
    Format conventions:
    - order: Must be one of "relevance", "date", "rating", "viewCount", "title"
    - max_results: Between 1-50 (default: 5)
    """,
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 5},
            "order": {
                "type": "string",
                "enum": ["relevance", "date", "rating", "viewCount", "title"]
            }
        },
        "required": ["query"]
    }
)
```

### Method 2: Few-Shot Learning (System Instructions)

```python
system_instruction = """
You have access to YouTube search. Here are usage examples:

# Search for educational content
search_youtube_videos(query="machine learning tutorial", max_results=5, order="relevance")

# Find recent videos
search_youtube_videos(query="AI news", max_results=3, order="date")

# Find popular videos
search_youtube_videos(query="coding music", max_results=10, order="viewCount")

Always use descriptive queries and appropriate ordering for the task.
"""
```

---

## Real Tool Examples

### YouTube API Tools

```python
# tools/youtube_api.py

TOOL_EXAMPLES = {
    "search_youtube_videos": [
        {
            "description": "Find tutorial videos",
            "input": {
                "query": "Next.js full tutorial",
                "max_results": 5,
                "order": "relevance"
            }
        },
        {
            "description": "Find latest AI news",
            "input": {
                "query": "artificial intelligence breakthroughs",
                "max_results": 3,
                "order": "date"
            }
        },
        {
            "description": "Find popular coding music",
            "input": {
                "query": "lofi coding beats",
                "max_results": 10,
                "order": "viewCount"
            }
        }
    ],
    
    "get_video_details": [
        {
            "description": "Get stats for specific video",
            "input": {
                "video_id": "dQw4w9WgXcQ"
            }
        }
    ]
}
```

### Google Maps Tools

```python
# tools/maps_api.py

TOOL_EXAMPLES = {
    "geocode_address": [
        {
            "description": "Full street address",
            "input": {
                "address": "1600 Amphitheatre Parkway, Mountain View, CA"
            }
        },
        {
            "description": "City and state",
            "input": {
                "address": "San Francisco, CA"
            }
        },
        {
            "description": "Landmark",
            "input": {
                "address": "Statue of Liberty, New York"
            }
        }
    ],
    
    "get_directions": [
        {
            "description": "Driving directions",
            "input": {
                "origin": "New York, NY",
                "destination": "Boston, MA",
                "mode": "driving"
            }
        },
        {
            "description": "Public transit with departure time",
            "input": {
                "origin": "San Francisco Airport",
                "destination": "Market Street, San Francisco",
                "mode": "transit",
                "departure_time": "2024-11-29T09:00:00"
            }
        }
    ],
    
    "search_nearby_places": [
        {
            "description": "Find coffee shops",
            "input": {
                "location": "37.7749,-122.4194",  # San Francisco
                "place_type": "cafe",
                "radius": 1000
            }
        },
        {
            "description": "Find restaurants open now",
            "input": {
                "location": "40.7128,-74.0060",  # New York
                "place_type": "restaurant",
                "radius": 500,
                "open_now": true
            }
        }
    ]
}
```

### Notion Integration Tools

```python
# tools/notion_tools.py

TOOL_EXAMPLES = {
    "create_page": [
        {
            "description": "Create meeting notes",
            "input": {
                "database_id": "abc123...",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Weekly Sync - 2024-11-29"}}]},
                    "Type": {"select": {"name": "Meeting Notes"}},
                    "Date": {"date": {"start": "2024-11-29"}}
                }
            }
        },
        {
            "description": "Create task",
            "input": {
                "database_id": "def456...",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Fix login bug"}}]},
                    "Status": {"status": {"name": "In Progress"}},
                    "Priority": {"select": {"name": "High"}},
                    "Due": {"date": {"start": "2024-12-01"}}
                }
            }
        }
    ],
    
    "query_database": [
        {
            "description": "Get high-priority tasks",
            "input": {
                "database_id": "def456...",
                "filter": {
                    "and": [
                        {"property": "Priority", "select": {"equals": "High"}},
                        {"property": "Status", "status": {"does_not_equal": "Done"}}
                    ]
                },
                "sorts": [
                    {"property": "Due", "direction": "ascending"}
                ]
            }
        }
    ]
}
```

---

## Best Practices

### 1. Use Realistic Data
**Good:**
```json
{"address": "123 Main St, San Francisco, CA 94102"}
```

**Bad:**
```json
{"address": "string"}
```

### 2. Show Variety
Include minimal, partial, and full examples:

```python
examples = [
    # Minimal
    {"query": "Python tutorial"},
    
    # Partial
    {"query": "React hooks", "max_results": 10},
    
    # Full
    {"query": "async JavaScript", "max_results": 5, "order": "date"}
]
```

### 3. Document Format Conventions
```python
description = """
Create a calendar event.

Format conventions:
- Dates: ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- Duration: Minutes as integer
- Attendees: Array of email strings
- Timezone: America/New_York, America/Los_Angeles, etc.
"""
```

### 4. Keep It Concise
**Good:** 1-5 examples per tool

**Bad:** 20+ examples (token overhead)

### 5. Focus on Ambiguity
Only add examples where correct usage isn't obvious from schema:

**Needs examples:** Nested objects, date formats, ID conventions
**Doesn't need:** Simple strings, booleans, obvious enums

---

## Integration with Dynamic Registry

```python
from tools.dynamic_registry import register_deferred_tool
from tools.youtube_api import search_youtube_videos, TOOL_EXAMPLES

register_deferred_tool(
    name="search_youtube_videos",
    description=...with examples...,
    function=search_youtube_videos,
    parameters={...},
    examples=TOOL_EXAMPLES["search_youtube_videos"],  # <-- Add examples
    category="youtube"
)
```

---

## Measuring Impact

### Before Examples:
```python
# User: "Find recent AI videos"
# Gemini calls:
search_youtube_videos(query="AI", order="recent")  # ❌ Wrong! "recent" isn't valid

# Error: order must be one of "relevance", "date", "rating", "viewCount", "title"
```

### After Examples:
```python
# User: "Find recent AI videos"
# Gemini calls:
search_youtube_videos(query="AI videos", order="date", max_results=5)  # ✅ Correct!
```

**Result:** 72% → 90% accuracy

---

## Tool Example Template

```python
TOOL_EXAMPLES = {
    "your_tool_name": [
        {
            "description": "Brief description of use case",
            "input": {
                # Realistic parameter values
                "param1": "value1",
                "param2": 123
            }
        },
        # 2-4 more examples showing variety
    ]
}

def your_tool_function(...):
    """
    Tool description
    
    Examples:
    1. Use case 1:
       {"param1": "value1", "param2": 123}
    
    2. Use case 2:
       {"param1": "value2"}
    
    Format conventions:
    - param1: kebab-case strings
    - param2: positive integers only
    """
    pass
```

---

## Next Steps

1. Add examples to all Dav1d tools
2. Embed in function descriptions
3. Test accuracy improvements
4. Document conventions clearly
5. Keep examples realistic and varied

**Examples = Better tools = Fewer errors = Happier users!** ✨
