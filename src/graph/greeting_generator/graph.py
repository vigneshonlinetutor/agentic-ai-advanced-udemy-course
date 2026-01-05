"""
Greeting Generator - Graph Assembly
"""
from langgraph.graph import StateGraph, END
from .state import GreetingState
from .nodes import validate_name, generate_greeting, add_timestamp

def build_graph():
    # Create Graph
    workflow = StateGraph(GreetingState)
    
    # Add nodes
    workflow.add_node("validate", validate_name)
    workflow.add_node("greet", generate_greeting)
    workflow.add_node("timestamp", add_timestamp)
    
    # Connect nodes
    workflow.set_entry_point("validate")
    workflow.add_edge("validate","greet")
    workflow.add_edge("greet", "timestamp")
    workflow.add_edge("timestamp", END)
    
    # Compile graph
    return workflow.compile()