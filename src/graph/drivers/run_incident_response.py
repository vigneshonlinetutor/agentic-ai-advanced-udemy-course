"""
Driver for Incident Response Multi-Agent System
"""
import sys
from pathlib import Path
from src.graph.incident_response.graph import build_incident_response_graph
from src.core import get_logger, pick_log_file

logger = get_logger("incident_response_driver")

# Paths
ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = ROOT / "data" / "logs"
OUT_DIR = ROOT / "outputs" / "incident_response"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    logger.info("🚀 Starting Incident Response Multi-Agent System...")

    # Pick log file
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    log_file = pick_log_file(file_arg, LOG_DIR)
    log_content = log_file.read_text(encoding="utf-8")

    logger.info(f"Processing log: {log_file.name}")
    logger.info(f"Log size: {len(log_content)} characters")

    # Build multi-agent graph
    app = build_incident_response_graph()

    # Initialize state
    init_state = {
        "log_content": log_content,
        "next_agent": "",
        "log_analysis": None,
        "root_cause": None,
        "solution": None,
        "incident_report": "",
        "steps_completed": [],
        "errors": []
    }

    # Run multi-agent workflow
    logger.info("=" * 70)
    final_state = app.invoke(init_state)
    logger.info("=" * 70)

    # Save incident report
    if final_state.get("errors"):
        logger.error(f"⚠️ Workflow completed with errors: {final_state['errors']}")
    else:
        logger.info("✅ Workflow completed successfully!")

    # Save report to file
    report_file = OUT_DIR / "incident_report.txt"
    report_file.write_text(final_state["incident_report"], encoding="utf-8")
    logger.info(f"📄 Incident report saved: {report_file.relative_to(ROOT)}")

    # Show summary
    logger.info(f"📊 Agents executed: {', '.join(final_state['steps_completed'])}")

    # Print report preview (first 500 chars)
    logger.info("\\n" + "="*70)
    logger.info("REPORT PREVIEW:")
    logger.info("="*70)
    print(final_state["incident_report"][:500] + "...\\n")

if __name__ == "__main__":
    main()
