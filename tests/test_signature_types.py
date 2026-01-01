from google.genai import types

try:
    p = types.Part(text="hello", thought_signature="sig_123")
    print("SUCCESS: types.Part accepts thought_signature")
    print(p)
except Exception as e:
    print(f"FAILURE: {e}")
