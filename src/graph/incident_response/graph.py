"""
Incident Response Multi-Agent Graph
"""
from langgraph.graph import StateGraph, END
from .state import IncidentState
from .supervisor import supervisor_router, supervisor_compile, route_next
from .agents import (
    log_analyzer_agent,
    root_cause_investigator_agent,
    solution_recommender_agent
)
from src.core import get_logger

logger = get_logger("incident_response_graph")

def build_incident_response_graph():
    """Build multi-agent graph with central router (supervisor pattern)."""

    logger.info("Building incident response graph...")

    workflow = StateGraph(IncidentState)

    # Add routing node (supervisor decides which agent to call)
    workflow.add_node("router", supervisor_router)

    # Add specialist agent nodes
    workflow.add_node("log_analyzer", log_analyzer_agent)
    workflow.add_node("root_cause_investigator", root_cause_investigator_agent)
    workflow.add_node("solution_recommender", solution_recommender_agent)

    # Add compilation node (supervisor compiles final report)
    workflow.add_node("compile_report", supervisor_compile)

    # Entry point: Start at router
    workflow.set_entry_point("router")

    # Router decides which agent to call (SINGLE conditional edge)
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "log_analyzer": "log_analyzer",
            "root_cause_investigator": "root_cause_investigator",
            "solution_recommender": "solution_recommender",
            "FINISH": "compile_report"
        }
    )

    # All agents return to router (supervisor decides next step)
    workflow.add_edge("log_analyzer", "router")
    workflow.add_edge("root_cause_investigator", "router")
    workflow.add_edge("solution_recommender", "router")

    # Compile and end
    workflow.add_edge("compile_report", END)

    logger.info("✅ Graph built successfully")
    return workflow.compile()