import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from dav1d import CLI_TOOLS, API_TOOLS_AVAILABLE
    print(f"API Tools Available: {API_TOOLS_AVAILABLE}")
    
    tool_names = [t.__name__ for t in CLI_TOOLS]
    print(f"Registered Tools: {tool_names}")
    
    expected_tools = [
        "search_youtube_videos", "get_video_details", "get_channel_info",
        "geocode_address", "reverse_geocode", "search_nearby_places",
        "text_to_speech", "speech_to_text",
        "generate_video"
    ]
    
    all_present = True
    for tool in expected_tools:
        if tool in tool_names:
            print(f"SUCCESS: {tool} is registered.")
        else:
            print(f"FAILURE: {tool} is NOT registered.")
            all_present = False
            
    if all_present:
        print("\nAll API tools verified successfully!")
    else:
        print("\nSome API tools are missing.")

except ImportError as e:
    print(f"Import Error: {e}")
except Exception as e:
    print(f"Error: {e}")
