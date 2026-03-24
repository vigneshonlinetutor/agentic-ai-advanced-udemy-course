"""
Driver for Jira → TestCase → TestRail → Slack Multi-Agent Pipeline
"""
import sys
from pathlib import Path
from src.graph.jira_testrail_slack.graph import build_graph
from src.core import get_logger

logger = get_logger("jira_testrail_slack_driver")

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "outputs" / "jira_testrail_slack"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    jira_key = sys.argv[1] if len(sys.argv) > 1 else "QA-1"

    logger.info(f"🚀 Starting pipeline for Jira issue: {jira_key}")

    app = build_graph()

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
        "errors": []
    }

    logger.info("=" * 70)
    final_state = app.invoke(init_state)
    logger.info("=" * 70)

    if final_state.get("errors"):
        logger.error(f"⚠️ Completed with errors: {final_state['errors']}")
    else:
        logger.info("✅ Pipeline completed successfully!")

    logger.info(f"📊 Agents executed: {', '.join(final_state['steps_completed'])}")

    report_file = OUT_DIR / f"{jira_key}_report.txt"
    report_file.write_text(final_state["summary_report"], encoding="utf-8")
    logger.info(f"📄 Report saved: {report_file.relative_to(ROOT)}")

    print(final_state["summary_report"])


if __name__ == "__main__":
    main()
