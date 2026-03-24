"""
TestCase Generator Agent - Generates test cases from Jira description using RAG + Memory + LLM
"""
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.core import get_logger, get_langchain_llm
from src.core import search_vector_store
from src.core import ConversationMemory, PersistentMemory
from src.prompts.testcase_prompts import TESTCASE_SYSTEM_PROMPT

logger = get_logger("testcase_generator_agent")

# Module-level initialization — same pattern as testcase_memory
llm = get_langchain_llm()
prompt_template = ChatPromptTemplate.from_messages([
    ("system", TESTCASE_SYSTEM_PROMPT),
    ("user", "Requirements:\n\n{requirement}")
])
parser = StrOutputParser()
chain = prompt_template | llm | parser

conversation_memory = ConversationMemory(max_messages=20)
persistent_memory = PersistentMemory(collection_name="testcase_memory")


def testcase_generator_agent(state):
    """Generate test cases from Jira description using RAG + memory + LLM."""
    logger.info("🤖 TestCase Generator running...")

    # Key difference from testcase_memory: input comes from state, not a file
    requirement = state["jira_description"]

    # --- Load memories (reused from testcase_memory) ---
    conversation_history = conversation_memory.get_history()
    past_patterns = persistent_memory.get_context(
        query=f"test case patterns for: {requirement[:200]}",
        top_k=2
    )

    # --- Retrieve RAG context (reused from testcase_memory) ---
    results = search_vector_store(
        query=f"test case guidelines for: {requirement[:200]}",
        top_k=3
    )
    context_parts = []
    for doc, score in results:
        source = doc.metadata.get("source", "Unknown").split("/")[-1]
        context_parts.append(f"[Source: {source}]\n{doc.page_content}")
    rag_context = "\n---\n".join(context_parts)

    # --- Build prompt (reused from testcase_memory) ---
    conv_context = ""
    if conversation_history:
        recent = conversation_history[-3:]
        conv_lines = [f"{m['role']}: {m['content'][:100]}..." for m in recent]
        conv_context = "\n".join(conv_lines)

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
        test_cases = json.loads(response)

        logger.info(f"✅ Generated {len(test_cases)} test cases")

        conversation_memory.add_message("user", f"Generate tests: {requirement[:100]}...")
        conversation_memory.add_message("agent", f"Generated {len(test_cases)} test cases")

        return {
            "test_cases": test_cases,
            "retrieved_context": rag_context,
            "past_patterns": past_patterns,
            "conversation_history": conversation_history,
            "steps_completed": state["steps_completed"] + ["testcase_generator"]
        }

    except Exception as e:
        logger.error(f"❌ TestCase Generator failed: {e}")
        return {
            "test_cases": [],
            "steps_completed": state["steps_completed"] + ["testcase_generator"],
            "errors": state["errors"] + [f"TestCase Generator: {e}"]
        }
