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
from src.core import ConversationMemory, PersistentMemory

# Initialize memory (shared across all nodes)
conversation_memory = ConversationMemory(max_messages=20)
persistent_memory = PersistentMemory(collection_name="log_analyzer_memory")


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

def load_memories(state: LogAnalyzerState) -> LogAnalyzerState:
    """Load short-term and long-term memory."""

    log_content = state["log_content"]
    log_preview = log_content[:300]  # First 300 chars for search

    logger.info("Loading memories...")

    # Short-term: Get conversation history
    conversation_history = conversation_memory.get_history()
    logger.info(f"Loaded conversation history: {len(conversation_history)} messages")

    # Long-term: Retrieve similar past incidents
    past_incidents = persistent_memory.get_context(
        query=f"past incidents similar to: {log_preview}",
        top_k=2
    )

    if past_incidents:
        logger.info("Retrieved past incident patterns from long-term memory")
    else:
        logger.info("No relevant past incidents found")

    return {
        "conversation_history": conversation_history,
        "past_incidents": past_incidents
    }


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
    """Analyze log with RAG + both memories."""
    logger.info("Analyzing log with RAG and memory context...")

    log_content = state["log_content"]
    rag_context = state.get("retrieved_context", "")
    past_incidents = state.get("past_incidents", "")
    conv_history = state.get("conversation_history", [])

    # Build conversation context
    conv_context = ""
    if conv_history:
        recent = conv_history[-3:]  # Last 3 messages
        conv_lines = [f"{msg['role']}: {msg['content'][:100]}..." for msg in recent]
        conv_context = "\n".join(conv_lines)

    # Build enhanced prompt with all context
    user_message = f"""Context from our conversation:
{conv_context if conv_context else "First analysis"}

---

Troubleshooting guides:
{rag_context}

---

Past similar incidents:
{past_incidents if past_incidents else "No past incidents yet"}

---

Now analyze this log:
{log_content}"""

    try:
        response = chain.invoke({"log_content": user_message})
        text_report, json_report, exec_summary = _split_response(response)

        logger.info("Analysis complete with RAG + memory")

        # Store in short-term memory
        conversation_memory.add_message("user", f"Analyze log: {log_content[:100]}...")
        conversation_memory.add_message("agent", f"Analyzed log with {len(text_report)} chars")

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
    """Save analysis to files and long-term memory."""

    if state.get("errors"):
        logger.warning("Skipping save due to errors")
        return {}

    # Save to files (existing code)
    text_file = OUT_DIR / "analysis_report.txt"
    text_file.write_text(state["analysis_text"], encoding="utf-8")
    logger.info(f"Saved text analysis: {text_file.relative_to(ROOT)}")

    json_file = OUT_DIR / "analysis_report.json"
    json_file.write_text(
        json.dumps(state["analysis_json"], indent=2),
        encoding="utf-8"
    )
    logger.info(f"Saved JSON report: {json_file.relative_to(ROOT)}")

    exec_file = OUT_DIR / "executive_summary.txt"
    exec_file.write_text(state["executive_summary"], encoding="utf-8")
    logger.info(f"Saved executive summary: {exec_file.relative_to(ROOT)}")

    # NEW: Store in long-term memory
    log_preview = state.get("log_content", "")[:200]
    json_summary = state.get("analysis_json", {})
    error_count = json_summary.get("error_count", 0)
    severity = json_summary.get("severity", "unknown")

    interaction = f"""Analyzed log with {error_count} errors (severity: {severity})

Log preview: {log_preview}

Root causes: {', '.join(json_summary.get('root_causes', [])[:3])}
Recommendations: {', '.join(json_summary.get('recommendations', [])[:2])}"""

    persistent_memory.store_interaction(
        interaction=interaction,
        metadata={
            "agent": "log_analyzer",
            "type": "incident_analysis",
            "error_count": error_count,
            "severity": severity
        }
    )
    logger.info("Stored analysis in long-term memory")

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
