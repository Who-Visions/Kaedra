from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, FunctionDeclaration
import os

# Force Vertex AI
client = genai.Client(vertexai=True, project="gen-lang-client-0285887798", location="us-east4")

def list_files_func(directory="."):
    print(f"Listing files in {directory}")
    return {"files": ["file1.txt", "file2.py"]}

# Define tool manually to be safe
list_files_tool = {
    "name": "list_files",
    "description": "List files in a directory",
    "parameters": {
        "type": "object",
        "properties": {
            "directory": {"type": "string"}
        }
    }
}

print("Testing automatic function calling...")
try:
    # In the new SDK, we might need to handle the loop manually if auto-calling isn't supported directly in generate_content
    # But let's try to see if we can pass the function implementation.
    
    # Actually, for the 'dav1d.py' refactor, I should probably stick to manual execution but fix the history.
    # But let's try to see if 'chat' works better.
    
    chat = client.chats.create(model="gemini-2.5-flash")
    
    # We need to register the function for execution?
    # The SDK usually requires us to execute the function and send back the result.
    
    print("Skipping auto-tool test, focusing on manual fix.")
    
except Exception as e:
    print(f"FAILED: {e}")
