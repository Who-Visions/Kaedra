# Vertex AI Search Integration for DAV1D

## Overview
Integrate Vertex AI Search to enable DAV1D to search through your enterprise documents, websites, and databases with semantic search capabilities.

## Prerequisites

### 1. Enable Vertex AI Search
```bash
gcloud services enable discoveryengine.googleapis.com --project=gen-lang-client-0285887798
```

### 2. Create a Data Store

**Option A: Via Console**
1. Go to [Vertex AI Search Console](https://console.cloud.google.com/gen-app-builder/engines)
2. Click "Create App" → "Search"
3. Choose data source:
   - **Website**: Provide URL to crawl
   - **Cloud Storage**: Point to GCS bucket with PDFs/HTMLs/DOCX
   - **BigQuery**: Connect to structured data
4. Note the `Data Store ID`

**Option B: Via gcloud**
```bash
# Create a data store
gcloud alpha discovery-engine data-stores create who-visions-kb \
    --location=global \
    --industry-vertical=GENERIC \
    --content-config=CONTENT_REQUIRED \
    --project=gen-lang-client-0285887798

# Import documents from Cloud Storage
gcloud alpha discovery-engine import documents \
    --data-store=who-visions-kb \
    --location=global \
    --gcs-uri=gs://your-bucket/documents/* \
    --project=gen-lang-client-0285887798
```

### 3. Get Data Store Resource ID
```bash
gcloud alpha discovery-engine data-stores list \
    --location=global \
    --project=gen-lang-client-0285887798
```

Format: `projects/gen-lang-client-0285887798/locations/global/collections/default_collection/dataStores/YOUR_DATA_STORE_ID`

---

## Implementation

### Option 1: Add to Deployed Agent (deploy.py)

Update `deploy.py` to include Vertex AI Search tool:

```python
def set_up(self):
    """Initialize model with Vertex AI Search"""
    from vertexai.generative_models import GenerativeModel, Tool
    import vertexai as vx
    from vertexai.preview.generative_models import grounding
    
    # Initialize Vertex AI in the cloud environment
    vx.init(project="gen-lang-client-0285887798", location="us-east4")
    
    # Configure Vertex AI Search grounding
    search_grounding = grounding.Grounding(
        sources=[
            grounding.VertexAISearch(
                datastore="projects/gen-lang-client-0285887798/locations/global/collections/default_collection/dataStores/YOUR_DATA_STORE_ID"
            )
        ]
    )
    
    # Create model with grounding
    self.model = GenerativeModel(
        self.model_name,
        tools=[Tool.from_retrieval(search_grounding)]
    )
```

### Option 2: Add to Local Terminal (dav1d.py)

Update the `get_model()` function in `dav1d.py`:

```python
def get_model(model_name: str):
    """Get model with Vertex AI Search grounding enabled."""
    try:
        from vertexai.preview.generative_models import grounding
        from vertexai.generative_models import Tool
        
        # Configure Vertex AI Search
        search_grounding = grounding.Grounding(
            sources=[
                grounding.VertexAISearch(
                    datastore="projects/gen-lang-client-0285887798/locations/global/collections/default_collection/dataStores/YOUR_DATA_STORE_ID"
                )
            ]
        )
        
        return GenerativeModel(
            model_name,
            tools=[Tool.from_retrieval(search_grounding)]
        )
    except Exception as e:
        print(f"{Colors.DIM}[!] Vertex AI Search init failed: {e}{Colors.RESET}")
        return GenerativeModel(model_name)
```

### Option 3: ADK Agent (Using ADK Framework)

If using ADK agents:

```python
from agents.tools import VertexAISearchTool

# Define search tool
search_tool = VertexAISearchTool(
    data_store_ids=[
        "projects/gen-lang-client-0285887798/locations/global/collections/default_collection/dataStores/YOUR_DATA_STORE_ID"
    ]
)

# Create agent with search capability
from agents import Agent

dav1d_agent = Agent(
    model='gemini-exp-1206',
    name='dav1d',
    instruction=DAV1D_PROFILE,
    tools=[search_tool]
)
```

---

## Use Cases for DAV1D

### 1. **Who Visions Knowledge Base**
- Index all project documentation (UniCore, HVAC Go, LexiCore, Oni Weather, KAEDRA)
- Enable DAV1D to answer questions about your portfolio
- Ground responses in actual project specs

### 2. **AI with Dav3 Content**
- Index your blog posts, tutorials, case studies
- DAV1D can reference specific examples when helping users
- Maintain consistency with published content

### 3. **Code Repository Search**
- Index GitHub repositories
- DAV1D can find relevant code examples
- Answer "show me how we implemented X" queries

### 4. **Client Documentation**
- Index client contracts, requirements, meeting notes
- DAV1D becomes a project memory assistant
- Quick lookup of client-specific information

---

## Testing

Once integrated, test with:

```python
# In dav1d.py terminal
/deep How did we implement authentication in UniCore?

# DAV1D will search your indexed docs and provide grounded answers
```

---

## Cost Considerations

**Vertex AI Search Pricing:**
- Data ingestion: ~$0.10 per 1,000 pages
- Search queries: ~$3 per 1,000 queries
- Storage: ~$0.24 per GB/month

**Combined with Gemini:**
- Gemini 2.5 Flash: $0.008/query + search cost
- Gemini 2.5 Pro: $0.031/query + search cost
- Gemini 3.0 Preview: $0.045/query + search cost

---

## Next Steps

1. **Create Data Store** for your most valuable content
2. **Get Data Store ID** from console
3. **Update `get_model()` function** in `dav1d.py` with your Data Store ID
4. **Test** with domain-specific queries
5. **Iterate** - add more data sources as needed

This turns DAV1D into a true knowledge assistant grounded in your enterprise data!
