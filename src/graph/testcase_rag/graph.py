"""
TestCase Generator - Graph Assembly
"""
from langgraph.graph import StateGraph, END
from .state import TestCaseState
from .nodes import (
    read_requirement,
    retrieve_context,
    generate_tests,
    validate_tests,
    retry_generate,
    show_preview,
    human_approval,
    save_outputs,
    route_after_validation,
    route_after_human_approval
)

def build_graph():
    """Build and return compiled testcase generator graph with RAG."""

    workflow = StateGraph(TestCaseState)

    # Add nodes
    workflow.add_node("read", read_requirement)
    workflow.add_node("retrieve", retrieve_context)      # NEW
    workflow.add_node("generate", generate_tests)
    workflow.add_node("validate", validate_tests)
    workflow.add_node("retry", retry_generate)
    workflow.add_node("preview", show_preview)
    workflow.add_node("approval", human_approval)
    workflow.add_node("save", save_outputs)

    # Linear edges
    workflow.set_entry_point("read")
    workflow.add_edge("read", "retrieve")               # NEW
    workflow.add_edge("retrieve", "generate")           # NEW
    workflow.add_edge("generate", "validate")

    # Conditional edges (unchanged)
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {"preview": "preview", "retry": "retry"}
    )

    workflow.add_edge("preview", "approval")

    workflow.add_conditional_edges(
        "approval",
        route_after_human_approval,
        {"save": "save", "retry": "retry"}
    )

    workflow.add_edge("retry", "validate")
    workflow.add_edge("save", END)

    return workflow.compile()
