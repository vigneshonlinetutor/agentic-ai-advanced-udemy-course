"""
Jira → TestCase → TestRail → Slack Multi-Agent System - Shared State
"""
from typing import TypedDict, List, Optional


class JiraTestState(TypedDict):

    # Input
    jira_key: str                          # e.g. "QA-1"

    # Routing
    next_agent: str

    # Agent results (one field per agent)
    jira_summary: Optional[str]            # from jira_fetcher
    jira_description: Optional[str]        # from jira_fetcher
    test_cases: Optional[list]             # from testcase_generator
    testrail_case_ids: Optional[list]      # from testrail_pusher
    slack_message_ts: Optional[str]        # from slack_notifier

    # Reused from testcase_memory
    retrieved_context: Optional[str]
    past_patterns: Optional[str]
    conversation_history: Optional[list]

    # Final output + tracking
    summary_report: str
    steps_completed: List[str]
    errors: List[str]
