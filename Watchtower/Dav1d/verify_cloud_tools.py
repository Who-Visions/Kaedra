import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from dav1d import CLI_TOOLS, CLOUD_TOOLS_AVAILABLE
    print(f"Cloud Tools Available: {CLOUD_TOOLS_AVAILABLE}")
    
    tool_names = [t.__name__ for t in CLI_TOOLS]
    print(f"Registered Tools: {tool_names}")
    
    if "search_codebase_semantically" in tool_names:
        print("SUCCESS: search_codebase_semantically is registered.")
    else:
        print("FAILURE: search_codebase_semantically is NOT registered.")
        
    if "query_cloud_sql" in tool_names:
        print("SUCCESS: query_cloud_sql is registered.")
    else:
        print("FAILURE: query_cloud_sql is NOT registered.")

except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")
