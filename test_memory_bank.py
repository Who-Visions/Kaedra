import os
import uuid
import datetime
from vertexai import types
import vertexai

# Configuration
PROJECT_ID = "gen-lang-client-0939852539"
LOCATION = "us-central1" # Memory Bank is primarily in us-central1
AGENT_ENGINE_ID = "projects/69017097813/locations/us-central1/reasoningEngines/9098403744265011200"

# Initialize Client
vertexai.init(project=PROJECT_ID, location=LOCATION)
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

def test_memory_bank_creation():
    print(f"[*] Using Existing Agent Engine: {AGENT_ENGINE_ID}")
    return AGENT_ENGINE_ID

def test_memory_ingestion(engine_name):
    if not engine_name: return
    
    print("[*] Testing Session & Ingestion...")
    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    
    # 1. Create Session
    session = client.agent_engines.sessions.create(
        name=engine_name,
        user_id="test-user",
        config={"display_name": "Test Session"}
    )
    session_name = session.response.name
    print(f"[+] Session Created: {session_name}")
    
    # 2. Add Event
    client.agent_engines.sessions.events.append(
        name=session_name,
        author="test-user",
        invocation_id="0",
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        config={
            "content": {"role": "user", "parts": [{"text": "I am allergic to peanuts."}]}
        }
    )
    
    # 3. Generate Memories
    print("[*] Generating Memories (blocking)...")
    op = client.agent_engines.memories.generate(
        name=engine_name,
        vertex_session_source={"session": session_name},
        config={"wait_for_completion": True}
    )
    
    if op.response.generated_memories:
        print(f"[+] Memories Generated: {len(op.response.generated_memories)}")
        for mem in op.response.generated_memories:
             full_mem = client.agent_engines.memories.get(name=mem.memory.name)
             print(f"    - {full_mem.fact}")
    else:
        print("[-] No memories generated.")

if __name__ == "__main__":
    engine_name = test_memory_bank_creation()
    test_memory_ingestion(engine_name)
    
    # Cleanup (Optional)
    # if engine_name:
    #     client.agent_engines.delete(name=engine_name, force=True)
