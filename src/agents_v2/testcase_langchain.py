"""
TestCase Generator Agent - Langchain Version
Generates test cases from requirements using Langchain.
"""
import sys
import json
import pandas as pd
from pathlib import Path
# Langchain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Our core utilities
from src.core import get_langchain_llm, pick_requirement, get_logger

# Import prompt
from src.prompts.testcase_prompts import TESTCASE_SYSTEM_PROMPT

# Project paths
ROOT = Path(__file__).resolve().parents[2]
REQ_DIR = ROOT / "data" / "requirements"
OUT_DIR = ROOT / "outputs" / "testcase_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = get_logger("testcase_langchain")

# Build Langchain prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", TESTCASE_SYSTEM_PROMPT),
    ("user", "Requirements:\n\n{requirement}")
])

# Get LLM
llm = get_langchain_llm()

# Get Parser
parser = JsonOutputParser()

# Build chain using LECL(Pipe Operator)
chain = prompt_template | llm | parser

def main():
    logger.info("TestCase Agent (Langchain) started")

    # 1. Pick requirement file
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    req_file = pick_requirement(file_arg, REQ_DIR)
    requirement = req_file.read_text(encoding="utf-8")
    logger.info(f"Processing: {req_file.name}")

    # 2. Run chain
    logger.info("Calling LLM via Langchain...")
    testcases = chain.invoke({"requirement": requirement})

    # 3. Save outputs
    # Save raw JSON
    raw_file = OUT_DIR / "raw_output_langchain.txt"
    raw_file.write_text(json.dumps(testcases, indent=2), encoding="utf-8")

    # Save CSV
    csv_file = OUT_DIR / "test_cases_langchain.csv"
    df = pd.DataFrame(testcases)
    df['steps'] = df['steps'].apply(lambda x: ' | '.join(x))
    df.to_csv(csv_file, index=False)

    # 4. Log results
    logger.info(f"Generated {len(testcases)} test cases")
    logger.info(f"Raw JSON: {raw_file.relative_to(ROOT)}")
    logger.info(f"CSV: {csv_file.relative_to(ROOT)}")
    logger.info("TestCase Agent (Langchain) completed")


if __name__ == "__main__":
    main()
