"""
Jira → TestCase → TestRail → Slack Multi-Agent Graph
"""
from langgraph.graph import StateGraph, END
from .state import JiraTestState
from .supervisor import supervisor_router, supervisor_compile, route_next
from .agents import (
    jira_fetcher_agent,
    testcase_generator_agent,
    testrail_pusher_agent,
    slack_notifier_agent
)
from src.core import get_logger

logger = get_logger("jira_testrail_slack_graph")


def build_graph():
    """Build multi-agent graph with central supervisor router."""
    logger.info("Building Jira → TestCase → TestRail → Slack graph...")

    workflow = StateGraph(JiraTestState)

    # Add routing node
    workflow.add_node("router", supervisor_router)

    # Add specialist agent nodes
    workflow.add_node("jira_fetcher", jira_fetcher_agent)
    workflow.add_node("testcase_generator", testcase_generator_agent)
    workflow.add_node("testrail_pusher", testrail_pusher_agent)
    workflow.add_node("slack_notifier", slack_notifier_agent)

    # Add compilation node
    workflow.add_node("compile_report", supervisor_compile)

    # Entry point
    workflow.set_entry_point("router")

    # Router decides which agent to call
    workflow.add_conditional_edges(
        "router",
        route_next,
        {
            "jira_fetcher": "jira_fetcher",
            "testcase_generator": "testcase_generator",
            "testrail_pusher": "testrail_pusher",
            "slack_notifier": "slack_notifier",
            "FINISH": "compile_report"
        }
    )

    # All agents return to router
    workflow.add_edge("jira_fetcher", "router")
    workflow.add_edge("testcase_generator", "router")
    workflow.add_edge("testrail_pusher", "router")
    workflow.add_edge("slack_notifier", "router")

    # Compile and end
    workflow.add_edge("compile_report", END)

    logger.info("✅ Graph built successfully")
    return workflow.compile()
