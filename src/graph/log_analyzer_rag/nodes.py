"""
Log Analyzer - Node Functions
"""
import json
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .state import LogAnalyzerState
from src.core import get_langchain_llm, pick_log_file, get_logger
from src.prompts.log_analyzer_prompts import LOG_ANALYZER_SYSTEM_PROMPT
from src.core import search_vector_store


# Setup
logger = get_logger("log_analyzer_graph")
ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = ROOT / "data" / "logs"
OUT_DIR = ROOT / "outputs" / "log_analyzer"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Build Langchain components
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", LOG_ANALYZER_SYSTEM_PROMPT),
    ("user", "Analyze this log:\\n\\n{log_content}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


def read_log(state: LogAnalyzerState) -> LogAnalyzerState:
    """Read log file."""
    log_file = pick_log_file(None, LOG_DIR)
    log_content = log_file.read_text(encoding="utf-8")
    logger.info(f"Read log file: {log_file.name} ({len(log_content)} chars)")
    return {"log_content": log_content}

def retrieve_context(state: LogAnalyzerState) -> LogAnalyzerState:
    """Retrieve relevant troubleshooting guides from knowledge base."""

    log_content = state["log_content"]

    # Extract key error patterns from log (first 500 chars)
    log_preview = log_content[:500]

    logger.info("Retrieving relevant troubleshooting guides...")

    # Search vector store
    results = search_vector_store(
        query=f"troubleshooting guide for: {log_preview}",
        top_k=3
    )

    # Format context
    context_parts = []
    for i, (doc, score) in enumerate(results, 1):
        source = doc.metadata.get('source', 'Unknown').split('/')[-1]
        similarity = 1 - score

        logger.info(f"Retrieved [{i}] {source} (similarity: {similarity:.2f})")

        context_parts.append(f"[Source: {source}]\\n{doc.page_content}\n")

    retrieved_context = "\n---\n".join(context_parts)

    logger.info(f"Retrieved {len(results)} relevant troubleshooting guides")

    return {"retrieved_context": retrieved_context}


def analyze_log(state: LogAnalyzerState) -> LogAnalyzerState:
    """Analyze log with RAG context (troubleshooting guides)."""
    logger.info("Analyzing log with troubleshooting guides...")

    log_content = state["log_content"]
    context = state.get("retrieved_context", "")

    # Build enhanced prompt with context
    user_message = f"""Based on the following troubleshooting guides:

{context}

---

Now analyze this log:

{log_content}"""

    try:
        response = chain.invoke({"log_content": user_message})
        text_report, json_report, exec_summary = _split_response(response)

        logger.info("Analysis complete with RAG context")
        return {
            "analysis_text": text_report,
            "analysis_json": json_report,
            "executive_summary": exec_summary,
            "errors": []
        }

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "analysis_text": "",
            "analysis_json": {},
            "executive_summary": "",
            "errors": [f"LLM error: {e}"]
        }

def save_outputs(state: LogAnalyzerState) -> LogAnalyzerState:
    """Save analysis to 3 files."""

    if state.get("errors"):
        logger.warning("Skipping save due to errors")
        return {}

    # Save text analysis
    text_file = OUT_DIR / "analysis_report.txt"
    text_file.write_text(state["analysis_text"], encoding="utf-8")
    logger.info(f"Saved text analysis: {text_file.relative_to(ROOT)}")

    # Save JSON report
    json_file = OUT_DIR / "analysis_report.json"
    json_file.write_text(
        json.dumps(state["analysis_json"], indent=2),
        encoding="utf-8"
    )
    logger.info(f"Saved JSON report: {json_file.relative_to(ROOT)}")

    # Save executive summary
    exec_file = OUT_DIR / "executive_summary.txt"
    exec_file.write_text(state["executive_summary"], encoding="utf-8")
    logger.info(f"Saved executive summary: {exec_file.relative_to(ROOT)}")

    return {}


def _split_response(response: str) -> tuple:
    """Split LLM response into 3 parts."""
    text_report = response
    json_report = {}
    exec_summary = "Executive summary not generated."

    # Split by ```json markdown fence
    if "```json" in response:
        parts = response.split("```json")
        text_report = parts[0].strip()
        remainder = parts[1]

        # Extract JSON
        if "```" in remainder:
            json_block = remainder.split("```")[0].strip()
            try:
                json_report = json.loads(json_block)
            except json.JSONDecodeError:
                json_report = {"error": "Failed to parse JSON"}

            # Extract executive summary
            after_json = remainder.split("```", 1)[1]
            if "---EXECUTIVE---" in after_json:
                exec_parts = after_json.split("---EXECUTIVE---")
                exec_summary = exec_parts[1].strip()

    return text_report, json_report, exec_summary
