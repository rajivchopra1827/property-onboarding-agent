"""
Simple Tool wrapper class for compatibility with agno workflows.
"""

class Tool:
    """Simple Tool wrapper that mimics the expected Tool interface."""
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
