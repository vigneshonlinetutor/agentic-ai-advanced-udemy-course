"""
Greeting Generator - Node Functions
"""
from datetime import datetime
from .state import GreetingState

def validate_name(state: GreetingState) -> GreetingState:
    """Validate the name."""
    name = state["name"].strip()
    is_valid = len(name) > 0 and name.isalpha()
    print(f"✓ Validate: '{name}' → valid={is_valid}")
    return {"name": name, "is_valid": is_valid}

def generate_greeting(state: GreetingState) -> GreetingState:
    """Generate personalized greeting."""
    name = state["name"]
    greeting = f"Hello, {name}! Welcome to LangGraph!"
    print(f"  ✓ Generate: '{greeting}'")
    return {"greeting": greeting}

def add_timestamp(state: GreetingState) -> GreetingState:
    """Add current timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"✓ Timestamp: {timestamp}")
    return {"timestamp": timestamp}