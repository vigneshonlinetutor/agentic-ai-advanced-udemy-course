"""
Log Analyzer Agent - Analyzes error logs
"""
from src.core import get_logger, get_langchain_llm
from src.prompts import LOG_ANALYZER_PROMPT
from langchain_core.output_parsers import StrOutputParser

logger = get_logger("log_analyzer_agent")

# Initialize LLM and chain
llm = get_langchain_llm()
parser = StrOutputParser()
chain = llm | parser

def log_analyzer_agent(state):
    """Analyze error logs and identify critical issues."""
    logger.info("🔍 Log Analyzer running...")

    log_content = state["log_content"]

    try:
        # Call LLM to analyze log
        prompt = LOG_ANALYZER_PROMPT.format(log_content=log_content)
        analysis = chain.invoke(prompt)

        logger.info(f"✅ Log analysis complete ({len(analysis)} chars)")

        return {
            "log_analysis": analysis,
            "steps_completed": state["steps_completed"] + ["log_analyzer"]
        }

    except Exception as e:
        logger.error(f"❌ Log Analyzer failed: {e}")
        return {
            "log_analysis": f"Error: {e}",
            "steps_completed": state["steps_completed"] + ["log_analyzer"],
            "errors": state["errors"] + [f"Log Analyzer: {e}"]
        }
