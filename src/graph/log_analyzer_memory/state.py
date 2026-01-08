"""
Log Analyzer - State Definition
"""
from typing import TypedDict, Dict, List

class LogAnalyzerState(TypedDict):
    """State for log analysis pipeline."""
    log_content: str
    retrieved_context: str
    conversation_history: List[Dict]     # NEW: Short-term memory
    past_incidents: str                  # NEW: Long-term memory
    analysis_text: str
    analysis_json: Dict
    executive_summary: str
    errors: List[str]
