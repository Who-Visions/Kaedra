import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from kaedra.services.wispr import WisprMonitor

class TestWisprMonitor(unittest.TestCase):
    def test_wake_word_detection(self):
        monitor = WisprMonitor(db_path=":memory:") # Path doesn't matter for this logic test
        
        # Test cases
        test_phrases = [
            ("Hey Kaedra, what time is it?", "what time is it?"),
            ("i was just saying hey kaedra start protocol 1", "start protocol 1"),
            ("hey kaedra    status report", "status report"),
            ("random text with no wake word", None),
            ("Hey Kedra is not supported yet but maybe should be", None) 
        ]

        for input_text, expected_command in test_phrases:
            # We can test the private method _process_text logic by mocking callback
            callback = AsyncMock()
            monitor.callback = callback
            
            # Since _process_text is async, we need to run it
            asyncio.run(monitor._process_text(input_text))
            
            if expected_command:
                callback.assert_called_with(expected_command)
                # print(f"PASS: '{input_text}' -> Detected '{expected_command}'")
            else:
                callback.assert_not_called()
                # print(f"PASS: '{input_text}' -> Ignored")

if __name__ == '__main__':
    unittest.main()
