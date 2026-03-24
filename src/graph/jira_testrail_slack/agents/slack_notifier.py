"""
Slack Notifier Agent - Sends pipeline summary to Slack
"""
from src.core import get_logger
from src.integrations import SlackClient

logger = get_logger("slack_notifier_agent")

client = SlackClient()


def slack_notifier_agent(state):
    """Send pipeline summary to Slack."""
    logger.info("💬 Slack Notifier running...")

    jira_key = state.get("jira_key", "N/A")
    jira_summary = state.get("jira_summary", "N/A")
    test_cases = state.get("test_cases", [])
    testrail_ids = state.get("testrail_case_ids", [])

    try:
        message = client.build_summary(
            jira_key=jira_key,
            jira_summary=jira_summary,
            test_case_count=len(test_cases),
            testrail_ids=testrail_ids
        )

        result = client.post_message(message)
        ts = result.get("ts", "")

        logger.info(f"✅ Slack message sent (ts: {ts})")

        return {
            "slack_message_ts": ts,
            "steps_completed": state["steps_completed"] + ["slack_notifier"]
        }

    except Exception as e:
        logger.error(f"❌ Slack Notifier failed: {e}")
        return {
            "slack_message_ts": "",
            "steps_completed": state["steps_completed"] + ["slack_notifier"],
            "errors": state["errors"] + [f"Slack Notifier: {e}"]
        }
