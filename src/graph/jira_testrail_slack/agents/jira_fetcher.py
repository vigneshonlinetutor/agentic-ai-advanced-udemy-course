"""
Jira Fetcher Agent - Fetches Jira story and puts description into state
"""
from src.core import get_logger
from src.integrations import JiraClient

logger = get_logger("jira_fetcher_agent")

client = JiraClient()


def jira_fetcher_agent(state):
    """Fetch Jira story and put description into state."""
    logger.info("🔍 Jira Fetcher running...")

    jira_key = state["jira_key"]

    try:
        issue = client.fetch_issue(jira_key)

        logger.info(f"✅ Fetched Jira issue: {jira_key} — {issue['summary']}")

        return {
            "jira_summary": issue["summary"],
            "jira_description": issue["description_text"],
            "steps_completed": state["steps_completed"] + ["jira_fetcher"]
        }

    except Exception as e:
        logger.error(f"❌ Jira Fetcher failed: {e}")
        return {
            "jira_summary": "",
            "jira_description": "",
            "steps_completed": state["steps_completed"] + ["jira_fetcher"],
            "errors": state["errors"] + [f"Jira Fetcher: {e}"]
        }
