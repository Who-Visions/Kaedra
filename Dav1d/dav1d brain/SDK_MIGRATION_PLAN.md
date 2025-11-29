# DAV1D - Google Gen AI SDK Migration Plan

## Why Migrate?
The `vertexai.generative_models` module is **deprecated** and will be removed on **June 24, 2026**.
The new `google-genai` SDK has full feature parity + additional capabilities.

## Installation
```bash
pip install --upgrade google-genai
```

## Key Changes for DAV1D

### 1. **Imports**
**Before:**
```python
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
```

**After:**
```python
from google import genai
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch, HttpOptions
```

### 2. **Client Initialization**
**Before:**
```python
vertexai.init(project=PROJECT_ID, location=LOCATION)
```

**After:**
```python
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
    http_options=HttpOptions(api_version="v1")
)
```

### 3. **Google Search Grounding**
**Before:**
```python
google_search_tool = Tool.from_google_search()
model = GenerativeModel(model_name, tools=[google_search_tool])
```

**After:**
```python
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents='query',
    config=GenerateContentConfig(
        tools=[Tool(google_search=GoogleSearch())]
    )
)
```

### 4. **System Instructions**
**Before:**
```python
model = GenerativeModel(
    model_name,
    system_instruction=DAV1D_PROFILE
)
```

**After:**
```python
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents='query',
    config=GenerateContentConfig(
        system_instruction=DAV1D_PROFILE
    )
)
```

### 5. **Generation Config**
**Before:**
```python
from vertexai.generative_models import GenerationConfig

response = model.generate_content(
    content,
    generation_config=GenerationConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=8192
    )
)
```

**After:**
```python
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents=content,
    config=GenerateContentConfig(
        temperature=1.0,
        top_p=0.95,
        max_output_tokens=8192,
        system_instruction=DAV1D_PROFILE,
        tools=[Tool(google_search=GoogleSearch())]
    )
)
```

### 6. **Chat Sessions**
**Before:**
```python
model = GenerativeModel(model_name)
chat = model.start_chat()
response = chat.send_message("Hello")
```

**After:**
```python
chat = client.chats.create(model='gemini-2.5-flash-lite')
response = chat.send_message('Hello')
```

### 7. **Streaming**
**Before:**
```python
stream = model.generate_content(content, stream=True)
for chunk in stream:
    print(chunk.text, end='')
```

**After:**
```python
for chunk in client.models.generate_content_stream(
    model='gemini-2.5-flash-lite',
    contents=content
):
    print(chunk.text, end='')
```

## Migration Strategy for DAV1D

### Phase 1: Update `get_model()` function
Replace the current implementation with a client-based approach:

```python
def get_dav1d_client():
    """Get configured Gen AI client with Vertex AI."""
    from google import genai
    from google.genai.types import HttpOptions
    
    return genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
        http_options=HttpOptions(api_version="v1")
    )

def generate_with_grounding(client, model_name: str, user_input: str, mode: str = "default"):
    """Generate content with Google Search grounding."""
    from google.genai.types import GenerateContentConfig, Tool, GoogleSearch
    
    # Build config based on mode
    if mode == "deep":
        config = GenerateContentConfig(
            system_instruction=DAV1D_PROFILE,
            tools=[Tool(google_search=GoogleSearch())],
            temperature=0.7,
            thinkingConfig={"thinkingLevel": "HIGH", "thinkingBudget": 8192}
        )
    else:
        config = GenerateContentConfig(
            system_instruction=DAV1D_PROFILE,
            tools=[Tool(google_search=GoogleSearch())],
            temperature=1.0
        )
    
    response = client.models.generate_content(
        model=model_name,
        contents=user_input,
        config=config
    )
    
    return response.text
```

### Phase 2: Update main loop
Replace `GenerativeModel` calls with client-based generation.

### Phase 3: Update deploy.py
Migrate cloud deployment to use new SDK.

## Benefits After Migration

1. ✅ **Future-proof** - No deprecation warnings
2. ✅ **Cleaner API** - More consistent interface
3. ✅ **Better tooling** - Improved type hints and IDE support
4  ✅ **New features** - Access to latest capabilities
5. ✅ **Performance** - Optimized networking and streaming

## Timeline
- **Now**: Install `google-genai` alongside existing SDK
- **This week**: Migrate `dav1d.py` to new SDK
- **Next week**: Migrate `deploy.py` to new SDK
- **Before June 2026**: Remove old SDK dependency

## Notes
- Both SDKs can coexist during transition
- The new SDK has simpler, more Pythonic interfaces
- Google Search grounding works correctly with new API
- All DAV1D features are supported in new SDK
