import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock modules before import
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()
sys.modules['kaedra.services.lifx'] = MagicMock()
sys.modules['kaedra.services.notion'] = MagicMock()
sys.modules['kaedra.core.config'] = MagicMock()
sys.modules['kaedra.core.config'].PROJECT_ID = "mock-project"
sys.modules['kaedra.core.config'].LIFX_TOKEN = "mock-token"

from universe_text import StoryEngine, Mode

class TestLIFXTrigger(unittest.TestCase):
    def test_living_room_trigger(self):
        print("Testing LIFX Trigger Logic...")
        engine = StoryEngine()
        
        # Inject mock LIFX
        mock_lifx = MagicMock()
        engine.lifx = mock_lifx
        
        # 1. Trigger update
        engine.update_lights()
        
        # 2. Check call args
        args, kwargs = mock_lifx.set_color.call_args
        target = args[0]
        
        print(f"LIFX Target: {target}")
        self.assertEqual(target, "group:Living Room", "Lights must target 'group:Living Room'")
        print("✔ Verified: Lights target Living Room Group")

if __name__ == "__main__":
    unittest.main()
