from typing import Dict, Any, List
from kaedra.services.wispr import WisprService

# We need access to the running service instance if possible, 
# or we can instantiate a fresh one purely for querying (stateless).
# Since SQLite is the content source, a fresh instance is fine.

def get_flow_context(action: str, query: str = None, limit: int = 5) -> Dict[str, Any]:
    """
    Access your Wispr Flow dictation history/context.
    
    Args:
        action (str): One of ['recent', 'search'].
        query (str): Search keywords (required for 'search' action).
        limit (int): Number of results to return (default 5).
        
    Returns:
        Dict: Contains 'results' list or 'error'.
    """
    # Instantiate service just for this call (stateless read)
    service = WisprService()
    
    if action == "recent":
        results = service.get_recent_transcripts(limit=limit)
        return {"action": "recent", "count": len(results), "results": results}
    
    elif action == "search":
        if not query:
            return {"error": "Query string is required for search action."}
        
        results = service.search_transcripts(query, limit=limit)
        return {"action": "search", "query": query, "count": len(results), "results": results}
        
    return {"error": f"Unknown action: {action}"}
