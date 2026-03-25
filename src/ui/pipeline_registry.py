"""
Pipeline registry — defines which pipelines are available in the UI.
Add a new PipelineConfig entry to PIPELINE_REGISTRY to expose a pipeline.
"""
from dataclasses import dataclass
from typing import Callable

from src.graph.incident_response.graph import build_incident_response_graph
from src.graph.jira_testrail_slack.graph import build_graph
from langchain_core.runnables import RunnableConfig


@dataclass
class PipelineConfig:
    name: str
    input_type: str        # "log" | "jira_key"
    description: str
    run_fn: Callable


def run_incident_response(log_content: str) -> dict:
    graph = build_incident_response_graph()
    init_state = {
        "log_content": log_content,
        "next_agent": "",
        "log_analysis": None,
        "root_cause": None,
        "solution": None,
        "incident_report": "",
        "steps_completed": [],
        "errors": [],
    }
    last_state = dict(init_state)
    try:
        for chunk in graph.stream(
            init_state,
            config=RunnableConfig(
                run_name="incident-response",
                metadata={"pipeline": "incident_response", "input_length": len(log_content)},
            ),
        ):
            for node_updates in chunk.values():
                if isinstance(node_updates, dict):
                    last_state.update(node_updates)
        return last_state
    except Exception:
        if last_state.get("errors"):
            return last_state
        return {"errors": ["Pipeline failed unexpectedly. Check console logs."], "steps_completed": [], "incident_report": ""}


def run_jira_testrail_slack(jira_key: str) -> dict:
    graph = build_graph()
    init_state = {
        "jira_key": jira_key,
        "next_agent": "",
        "jira_summary": None,
        "jira_description": None,
        "test_cases": None,
        "testrail_case_ids": None,
        "slack_message_ts": None,
        "retrieved_context": None,
        "past_patterns": None,
        "conversation_history": None,
        "summary_report": "",
        "steps_completed": [],
        "errors": [],
    }
    last_state = dict(init_state)
    try:
        for chunk in graph.stream(
            init_state,
            config=RunnableConfig(
                run_name="jira-testrail-slack",
                metadata={"pipeline": "jira_testrail_slack", "jira_key": jira_key},
            ),
        ):
            for node_updates in chunk.values():
                if isinstance(node_updates, dict):
                    last_state.update(node_updates)
        return last_state
    except Exception:
        if last_state.get("errors"):
            return last_state
        return {"errors": ["Pipeline failed unexpectedly. Check console logs."], "steps_completed": [], "summary_report": ""}


PIPELINE_REGISTRY: list[PipelineConfig] = [
    PipelineConfig(
        name="Incident Response",
        input_type="log",
        description="Analyze a log file and generate an incident report.",
        run_fn=run_incident_response,
    ),
    PipelineConfig(
        name="Jira → TestRail → Slack",
        input_type="jira_key",
        description="Fetch a Jira ticket, generate test cases, push to TestRail, notify Slack.",
        run_fn=run_jira_testrail_slack,
    ),
]
