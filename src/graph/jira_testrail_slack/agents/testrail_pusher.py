"""
TestRail Pusher Agent - Pushes LLM-generated test cases to TestRail
"""
import os
from src.core import get_logger
from src.integrations import TestRailClient

logger = get_logger("testrail_pusher_agent")

client = TestRailClient()


def testrail_pusher_agent(state):
    """Push LLM-generated test cases to TestRail."""
    logger.info("📤 TestRail Pusher running...")

    test_cases = state.get("test_cases", [])
    section_id = int(os.getenv("TESTRAIL_SECTION_ID", 1))

    try:
        created_ids = client.add_cases_bulk(section_id=section_id, test_cases=test_cases)

        logger.info(f"✅ Pushed {len(created_ids)} cases to TestRail section {section_id}")
        logger.info(f"   Case IDs: {created_ids}")

        return {
            "testrail_case_ids": created_ids,
            "steps_completed": state["steps_completed"] + ["testrail_pusher"]
        }

    except Exception as e:
        logger.error(f"❌ TestRail Pusher failed: {e}")
        return {
            "testrail_case_ids": [],
            "steps_completed": state["steps_completed"] + ["testrail_pusher"],
            "errors": state["errors"] + [f"TestRail Pusher: {e}"]
        }
