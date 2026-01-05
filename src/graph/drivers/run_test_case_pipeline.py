"""
Driver for TestCase Generator Pipeline
"""
from src.graph.test_case_generator.graph import build_graph
from src.core import get_logger

logger = get_logger("testcase_driver")

def main():
    logger.info("🚀 Starting TestCase Generator pipeline (with Human Approval)...")

    # Build graph
    app = build_graph()

    # Initialize state with new fields
    init_state = {
        "requirement": "",
        "test_cases": [],
        "errors": [],
        "validation_status": "pending",
        "retry_count": 0,
        "human_approval": "pending",
        "human_feedback": ""
    }

    # Run pipeline
    final_state = app.invoke(init_state)

    # Show results
    logger.info(f"✅ Pipeline complete!")
    logger.info(f"Generated {len(final_state.get('test_cases', []))} test cases")
    logger.info(f"Validation: {final_state.get('validation_status', 'unknown')}")
    logger.info(f"Human Decision: {final_state.get('human_approval', 'unknown')}")
    logger.info(f"Retries: {final_state.get('retry_count', 0)}")

    if final_state.get('human_feedback'):
        logger.info(f"Human Feedback: {final_state['human_feedback']}")

    if final_state.get('errors'):
        logger.error(f"Errors: {final_state['errors']}")

if __name__ == "__main__":
    main()
