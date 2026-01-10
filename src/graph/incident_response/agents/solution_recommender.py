"""
Solution Recommender Agent - Suggests fixes
"""
from src.core import get_logger, get_langchain_llm
from src.prompts import SOLUTION_PROMPT
from langchain_core.output_parsers import StrOutputParser

logger = get_logger("solution_recommender")

# Initialize LLM and chain
llm = get_langchain_llm()
parser = StrOutputParser()
chain = llm | parser

def solution_recommender_agent(state):
    """Provide actionable fix recommendations."""
    logger.info("💡 Solution Recommender running...")

    root_cause = state.get("root_cause", "")
    log_analysis = state.get("log_analysis", "")

    try:
        # Call LLM to recommend solutions
        prompt = SOLUTION_PROMPT.format(
            root_cause=root_cause,
            log_analysis=log_analysis
        )
        solution = chain.invoke(prompt)

        logger.info(f"✅ Solutions recommended ({len(solution)} chars)")

        return {
            "solution": solution,
            "steps_completed": state["steps_completed"] + ["solution_recommender"]
        }

    except Exception as e:
        logger.error(f"❌ Solution Recommender failed: {e}")
        return {
            "solution": f"Error: {e}",
            "steps_completed": state["steps_completed"] + ["solution_recommender"],
            "errors": state["errors"] + [f"Solution Recommender: {e}"]
        }
