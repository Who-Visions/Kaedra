import importlib
import pkgutil
import pipecat

def find_class(module, class_name):
    if hasattr(module, "__path__"):
        for _, name, _ in pkgutil.walk_packages(module.__path__):
            full_name = module.__name__ + "." + name
            try:
                sub_mod = importlib.import_module(full_name)
                if hasattr(sub_mod, class_name):
                    print(f"FOUND: {class_name} in {full_name}")
                    return full_name
            except Exception as e:
                pass
    return None

print("Searching for LocalSmartTurnAnalyzerV3...")
find_class(pipecat, "LocalSmartTurnAnalyzerV3") # This might take too long if it walks everything recursively improperly, but let's try.
