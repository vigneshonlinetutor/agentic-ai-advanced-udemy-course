"""
Driver for Log Analyzer Pipeline
"""
from src.graph.log_analyzer_memory.graph import build_graph
from src.core import get_logger

logger = get_logger("log_analyzer_driver")

def main():
    logger.info("🚀 Starting Log Analyzer pipeline...")

    # Build graph
    app = build_graph()

    # Initialize empty state
    init_state = {
        "log_content": "",
        "retrieved_context": "",
        "conversation_history": [],  # NEW
        "past_incidents": "",  # NEW
        "analysis_text": "",
        "analysis_json": {},
        "executive_summary": "",
        "errors": []
    }

    # Run pipeline
    final_state = app.invoke(init_state)

    # Show results
    logger.info(f"✅ Pipeline complete!")

    if final_state.get('errors'):
        logger.error(f"Errors: {final_state['errors']}")
    else:
        logger.info("Generated 3 reports: text, JSON, executive summary")

if __name__ == "__main__":
    main()
