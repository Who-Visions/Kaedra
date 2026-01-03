from kaedra.tools.wispr import get_flow_context
import json

def test_wispr_tool():
    print("Testing 'recent' action...")
    recent = get_flow_context(action="recent", limit=2)
    print(json.dumps(recent, indent=2))
    
    print("\nTesting 'search' action (query='kaedra')...")
    search = get_flow_context(action="search", query="kaedra", limit=2)
    print(json.dumps(search, indent=2))

if __name__ == "__main__":
    test_wispr_tool()
