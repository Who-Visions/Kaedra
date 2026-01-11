import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kaedra.story.context import ContextManager
from google.genai import types

class TestContextCaching(unittest.TestCase):
    """
    Validation Suite for Gemini Long Context Caching.
    Verifies the 'Stable Past' strategy and API integration logic.
    """
    
    def setUp(self):
        self.client = MagicMock()
        self.cm = ContextManager(self.client)
        
    def test_cache_eligibility_under_limit(self):
        """Verify we DO NOT cache if context < 32k tokens."""
        print("\n[TEST] Verifying Cache Eligibility (Under Limit)...")
        # Ensure token count is small
        self.cm._estimate_tokens = MagicMock(return_value=1000)
        self.cm.history = ["A", "B"]
        
        res = self.cm.update_cache("gemini-flash")
        
        self.assertIsNone(res)
        self.client.caches.create.assert_not_called()
        print(">> [PASS] Ignored small context.")

    @patch('kaedra.story.context.types')
    def test_stable_past_strategy(self, mock_types):
        """Verify we cache everything EXCEPT the last turn (Suffix Strategy)."""
        print("\n[TEST] Verifying Stable Past Strategy...")
        
        # Simulate > 32k tokens
        self.cm._estimate_tokens = MagicMock(return_value=40000)
        
        # Setup mock types to return dummy config
        mock_config = MagicMock()
        mock_types.CreateCachedContentConfig.return_value = mock_config
        
        # History: [System, Turn1_User, Turn1_Model, Turn2_User]
        # We can use simple objects now since types is mocked
        self.cm.history = ["Sys", "U1", "M1", "U2"]
        
        # Mock cache response
        mock_cache = MagicMock()
        mock_cache.name = "caches/12345"
        self.client.caches.create.return_value = mock_cache
        
        # Act
        res = self.cm.update_cache("gemini-flash")
        
        # Assert
        self.assertEqual(res, "caches/12345")
        self.assertEqual(self.cm.cached_content_name, "caches/12345")
        
        # Verify CreateCachedContentConfig called with correct contents check
        call_args = mock_types.CreateCachedContentConfig.call_args
        # contents should be history[:-1]
        self.assertEqual(call_args.kwargs['contents'], ["Sys", "U1", "M1"])
        
        print(">> [PASS] Strategy correctly split History vs Suffix.")

    def test_cache_expiration_handling(self):
        """Verify we handle empty/reset history gracefully."""
        self.cm.cached_content_name = "caches/old"
        self.cm.clear() # Should theoretically invalidate?
        # ContextManager.clear() just resets list. 
        # Ideally update_cache should detect mismatch?
        # update_cache calls _estimate_tokens -> 0 -> returns None -> cached_content_name = None.
        
        self.cm._estimate_tokens = MagicMock(return_value=0)
        self.cm.update_cache("flash")
        
        self.assertIsNone(self.cm.cached_content_name)
        print(">> [PASS] Cleared stale cache handle on small context.")

if __name__ == "__main__":
    # Pretty print runner
    suite = unittest.TestLoader().loadTestsFromTestCase(TestContextCaching)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("\n[SUCCESS] Caching Logic Verified (Mock Mode).")
    else:
        print("\n[FAILURE] Caching Validation Failed.")
        sys.exit(1)
