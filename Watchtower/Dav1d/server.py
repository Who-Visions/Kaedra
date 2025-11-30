from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys
import asyncio

# Add the current directory to sys.path to import dav1d modules if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# For now, we'll use a simple direct interaction with the model 
# instead of importing the full dav1d CLI app which might have side effects.
# We will replicate the core Chat functionality here.

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initialize Gemini Client
PROJECT_ID = os.getenv("PROJECT_ID", "watchtower-441919")
LOCATION = os.getenv("LOCATION", "us-central1")

client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
model_id = "gemini-2.5-flash" # Use the fast model for chat

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Construct the chat session
        # In a real app, we'd manage state properly. 
        # Here we'll just send the history + new message.
        
        chat = client.chats.create(model=model_id)
        
        # Replay history if provided (simplified)
        # for msg in request.history:
        #     chat.send_message(msg['content']) 
        
        # For this simple test, we just send the current message
        response = chat.send_message(request.message)
        
        return {"response": response.text}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
