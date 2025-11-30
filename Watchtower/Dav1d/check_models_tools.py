from google import genai
from google.genai.types import Tool, FunctionDeclaration
import os

client = genai.Client(vertexai=True, project="gen-lang-client-0285887798", location="us-east4")

# Define a simple tool
tool_def = {
    "name": "test_tool",
    "description": "A test tool",
    "parameters": {
        "type": "object",
        "properties": {
            "arg": {"type": "string"}
        }
    }
}

tools = [Tool(function_declarations=[FunctionDeclaration(**tool_def)])]

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

print("Testing models WITH tools...")
for model in models_to_test:
    try:
        print(f"Testing {model}...", end=" ")
        config = genai.types.GenerateContentConfig(tools=tools)
        response = client.models.generate_content(model=model, contents="Hi", config=config)
        print("OK")
    except Exception as e:
        print(f"FAILED: {e}")
