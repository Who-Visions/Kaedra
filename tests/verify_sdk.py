
from google.genai.types import Part, Content

def verify_serialization():
    print("--- VERIFYING SDK PART SERIALIZATION ---")
    
    print(f"Part dir: {dir(Part)}")

    # 1. Try Snake Case Constructor
    try:
        p1 = Part(thought_signature="TEST_SIG", function_call={"name": "test", "args": {}})
        print(f"SnakeCase Input -> Object: {p1}")
        try:
             print(f"SnakeCase Input -> Dict: {p1.to_json_dict()}")
        except:
             print(f"SnakeCase Input -> Dict (FAIL): {p1.__dict__}")
    except Exception as e:
        print(f"SnakeCase Input Failed: {e}")

    # 2. Try Camel Case Constructor
    try:
        p2 = Part(thoughtSignature="TEST_SIG", functionCall={"name": "test", "args": {}})
        print(f"CamelCase Input -> Object: {p2}")
        try:
             print(f"CamelCase Input -> Dict: {p2.to_json_dict()}")
        except:
             print(f"CamelCase Input -> Dict (FAIL): {p2.__dict__}")
    except Exception as e:
        print(f"CamelCase Input Failed: {e}")
        
    # 3. Try Direct Constructor
    try:
        # Check if thought_signature is an allowed init arg
        # We can't check arguments easily without inspecting or trying
        pass 
    except:
        pass

if __name__ == "__main__":
    verify_serialization()
