"""
Dummy Agent for Deployment Hygiene Test.
Zero dependencies. Zero imports. Pure Python.
"""

class DummyAgent:
    """
    I am a dummy agent. I exist only to test the deployment pipeline.
    """
    def __init__(self):
        self.status = "Green"

    def query(self, message: str):
        return {
            "response": f"I am alive. You said: {message}",
            "status": self.status
        }
