"""
TestCase Generator - Node Functions
"""
import json
from pathlib import Path
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from .state import TestCaseState
from src.core import get_langchain_llm, pick_requirement, get_logger
from src.prompts.testcase_prompts import TESTCASE_SYSTEM_PROMPT
from src.core import search_vector_store
from src.core import ConversationMemory, PersistentMemory


# Initialize memory (shared across all nodes)
conversation_memory = ConversationMemory(max_messages=20)
persistent_memory = PersistentMemory(collection_name="testcase_memory")


# Setup
logger = get_logger("testcase_graph")
ROOT = Path(__file__).resolve().parents[3]
REQ_DIR = ROOT / "data" / "requirements"
OUT_DIR = ROOT / "outputs" / "testcase_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Build Langchain components
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", TESTCASE_SYSTEM_PROMPT),
    ("user", "Requirements:\\n\\n{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser


def read_requirement(state: TestCaseState) -> TestCaseState:
    """Read requirement file."""
    req_file = pick_requirement(None, REQ_DIR)
    requirement = req_file.read_text(encoding="utf-8")
    logger.info(f"Read requirement: {req_file.name}")
    return {"requirement": requirement}

def load_memories(state: TestCaseState) -> TestCaseState:
    """Load short-term and long-term memory."""

    requirement = state["requirement"]

    logger.info("Loading memories...")

    # Short-term: Get conversation history
    conversation_history = conversation_memory.get_history()
    logger.info(f"Loaded conversation history: {len(conversation_history)} messages")

    # Long-term: Retrieve similar past patterns
    past_patterns = persistent_memory.get_context(
        query=f"test case patterns for: {requirement[:200]}",
        top_k=2
    )

    if past_patterns:
        logger.info("Retrieved past test case patterns from long-term memory")
    else:
        logger.info("No relevant past patterns found")

    return {
        "conversation_history": conversation_history,
        "past_patterns": past_patterns
    }


def retrieve_context(state: TestCaseState) -> TestCaseState:
    """Retrieve relevant testing guidelines from knowledge base."""

    requirement = state["requirement"]
    logger.info("Retrieving relevant testing guidelines...")

    # Search vector store
    results = search_vector_store(
        query=f"test case guidelines for: {requirement[:200]}",
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

    logger.info(f"Retrieved {len(results)} relevant documents")

    return {"retrieved_context": retrieved_context}



def generate_tests(state: TestCaseState) -> TestCaseState:
    """Generate test cases with RAG + both memories."""
    logger.info("Generating test cases with RAG and memory context...")

    requirement = state["requirement"]
    rag_context = state.get("retrieved_context", "")
    past_patterns = state.get("past_patterns", "")
    conv_history = state.get("conversation_history", [])

    # Build conversation context
    conv_context = ""
    if conv_history:
        recent = conv_history[-3:]  # Last 3 messages
        conv_lines = [f"{msg['role']}: {msg['content'][:100]}..." for msg in recent]
        conv_context = "\n".join(conv_lines)

    # Build enhanced prompt with all context
    user_message = f"""Context from our conversation:
{conv_context if conv_context else "First interaction"}

---

Company testing guidelines:
{rag_context}

---

Past test case patterns you've used:
{past_patterns if past_patterns else "No past patterns yet"}

---

Now generate test cases for this requirement:
{requirement}"""

    try:
        response = chain.invoke({"requirement": user_message})
        testcases = json.loads(response)
        logger.info(f"Generated {len(testcases)} test cases using RAG + memory")

        # Store in short-term memory
        conversation_memory.add_message("user", f"Generate tests: {requirement[:100]}...")
        conversation_memory.add_message("agent", f"Generated {len(testcases)} test cases")

        return {
            "test_cases": testcases,
            "errors": [],
            "retry_count": state.get("retry_count", 0),
            "validation_status": "pending"
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {
            "test_cases": [],
            "errors": [f"JSON parse error: {e}"],
            "retry_count": state.get("retry_count", 0),
            "validation_status": "fail"
        }
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "test_cases": [],
            "errors": [f"LLM error: {e}"],
            "retry_count": state.get("retry_count", 0),
            "validation_status": "fail"
        }


def save_outputs(state: TestCaseState) -> TestCaseState:
    """Save test cases to files and long-term memory."""
    test_cases = state["test_cases"]

    if not test_cases:
        logger.warning("No test cases to save")
        return {}

    # Save to files (existing code)
    raw_file = OUT_DIR / "raw_output.txt"
    raw_file.write_text(json.dumps(test_cases, indent=2), encoding="utf-8")
    logger.info(f"Saved raw JSON: {raw_file.relative_to(ROOT)}")

    df = pd.DataFrame(test_cases)
    if 'steps' in df.columns:
        df['steps'] = df['steps'].apply(lambda x: ' | '.join(x) if isinstance(x, list) else x)
    csv_file = OUT_DIR / "test_cases.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"Saved CSV: {csv_file.relative_to(ROOT)}")

    # NEW: Store in long-term memory
    requirement = state.get("requirement", "")
    interaction = f"""Generated {len(test_cases)} test cases for: {requirement[:100]}

Test cases included:
{', '.join([tc.get('id', 'N/A') for tc in test_cases[:5]])}

Priorities: {', '.join(set([tc.get('priority', 'N/A') for tc in test_cases]))}"""

    persistent_memory.store_interaction(
        interaction=interaction,
        metadata={
            "agent": "testcase_generator",
            "type": "test_generation",
            "count": len(test_cases)
        }
    )
    logger.info("Stored interaction in long-term memory")

    return {}


def validate_tests(state: TestCaseState) -> TestCaseState:
    """Validate generated test cases."""
    test_cases = state.get("test_cases", [])

    logger.info("Validating test cases...")

    # Validation checks
    if len(test_cases) < 3:
        logger.warning("Validation FAILED: Less than 3 test cases")
        return {"validation_status": "fail"}

    # Check each test case has required fields
    required_fields = ["id", "title", "steps", "expected", "priority"]
    for tc in test_cases:
        missing = [f for f in required_fields if f not in tc or not tc[f]]
        if missing:
            logger.warning(f"Validation FAILED: Missing fields {missing}")
            return {"validation_status": "fail"}

        # Check steps is a list with at least 2 steps
        if not isinstance(tc["steps"], list) or len(tc["steps"]) < 2:
            logger.warning("Validation FAILED: Steps must be list with 2+ items")
            return {"validation_status": "fail"}

    logger.info("✅ Validation PASSED")
    return {"validation_status": "pass"}

def retry_generate(state: TestCaseState) -> TestCaseState:
    """Retry test case generation with RAG context."""
    retry_count = state.get("retry_count", 0) + 1
    logger.warning(f"🔄 Retry attempt {retry_count}/3")

    requirement = state["requirement"]
    context = state.get("retrieved_context", "")

    # Build enhanced prompt with context
    user_message = f"""Based on the following company testing guidelines:

{context}

---

Now generate test cases for this requirement:

{requirement}"""

    try:
        response = chain.invoke({"requirement": user_message})
        testcases = json.loads(response)
        logger.info(f"Regenerated {len(testcases)} test cases with RAG")

        return {
            "test_cases": testcases,
            "errors": [],
            "retry_count": retry_count,
            "validation_status": "pending"
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {
            "test_cases": [],
            "errors": [f"JSON parse error: {e}"],
            "retry_count": retry_count,
            "validation_status": "fail"
        }
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {
            "test_cases": [],
            "errors": [f"LLM error: {e}"],
            "retry_count": retry_count,
            "validation_status": "fail"
        }

def route_after_validation(state: TestCaseState) -> str:
    """Decide next node based on validation result."""

    validation_status = state.get("validation_status", "pending")
    retry_count = state.get("retry_count", 0)

    # If passed validation → show preview for human approval
    if validation_status == "pass":
        logger.info("✅ Routing to PREVIEW (for human approval)")
        return "preview"  # Changed from "save" to "preview"

    # If failed but can retry → retry
    if validation_status == "fail" and retry_count < 3:
        logger.warning(f"⚠️ Routing to RETRY (attempt {retry_count + 1}/3)")
        return "retry"

    # If max retries reached → show preview anyway (human decides)
    logger.error("❌ Max retries reached, routing to PREVIEW")
    return "preview"  # Changed from "save" to "preview"


def show_preview(state: TestCaseState) -> TestCaseState:
    """Show test cases preview to human for approval."""
    test_cases = state.get("test_cases", [])

    print("\n" + "="*60)
    print("📋 TEST CASES PREVIEW - AWAITING APPROVAL")
    print("="*60)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}] {tc.get('id', 'N/A')}: {tc.get('title', 'N/A')}")
        print(f"    Priority: {tc.get('priority', 'N/A')}")
        print(f"    Steps: {len(tc.get('steps', []))} steps")
        print(f"    Expected: {tc.get('expected', 'N/A')[:50]}...")

    print("\\n" + "="*60)
    print(f"Total: {len(test_cases)} test cases generated")
    print("="*60 + "\n")

    logger.info(f"Preview shown: {len(test_cases)} test cases")
    return {"human_approval": "pending"}

def human_approval(state: TestCaseState) -> TestCaseState:
    """Wait for human approval decision."""

    print("\n🤔 What would you like to do?")
    print("  1. APPROVE - Save test cases")
    print("  2. REJECT - Regenerate test cases")
    print("  3. VIEW - Show full details")

    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            logger.info("✅ Human APPROVED test cases")
            return {
                "human_approval": "approved",
                "human_feedback": "Approved by user"
            }

        elif choice == "2":
            feedback = input("Why reject? (optional): ").strip()
            logger.warning(f"❌ Human REJECTED test cases: {feedback}")
            return {
                "human_approval": "rejected",
                "human_feedback": feedback or "No feedback provided"
            }

        elif choice == "3":
            _show_full_details(state)
            continue  # Ask again

        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


def _show_full_details(state: TestCaseState):
    """Show complete test case details."""
    test_cases = state.get("test_cases", [])

    print("\n" + "="*60)
    print("📝 FULL TEST CASE DETAILS")
    print("="*60)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─'*60}")
        print(f"Test Case #{i}")
        print(f"{'─'*60}")
        print(f"ID:       {tc.get('id', 'N/A')}")
        print(f"Title:    {tc.get('title', 'N/A')}")
        print(f"Priority: {tc.get('priority', 'N/A')}")
        print(f"\nSteps:")
        for j, step in enumerate(tc.get('steps', []), 1):
            print(f"  {j}. {step}")
        print(f"\nExpected Result:")
        print(f"  {tc.get('expected', 'N/A')}")

    print("\n" + "="*60 + "\n")
    

def route_after_human_approval(state: TestCaseState) -> str:
    """Decide next node based on human decision."""

    approval = state.get("human_approval", "pending")

    if approval == "approved":
        logger.info("✅ Human approved - routing to SAVE")
        return "save"

    elif approval == "rejected":
        logger.warning("❌ Human rejected - routing to RETRY")
        return "retry"

    else:
        logger.error("⚠️ Unknown approval status - routing to SAVE")
        return "save"
