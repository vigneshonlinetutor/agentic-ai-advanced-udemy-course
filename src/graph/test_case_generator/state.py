"""
TestCase Generator - State Definition
"""
from typing import TypedDict, List, Dict

class TestCaseState(TypedDict):
    """State for test case generation pipeline."""
    requirement: str
    test_cases: List[Dict]
    errors: List[str]
    validation_status: str  # "pass" | "fail" | "pending"
    retry_count: int  # Track retry attempts
    human_approval: str  # "pending" | "approved" | "rejected"
    human_feedback: str  #  Optional feedback from human
