"""
Greeting Generator - State Definition
"""
from typing import TypedDict

class GreetingState(TypedDict):
    name: str
    is_valid: bool
    greeting: str
    timestamp: str