"""
Log Analyzer Agent - Langchain Version
Analyzes log files and generates analysis reports using Langchain.
"""
import sys
import json
from pathlib import Path

# Langchain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Our core utilities
from src.core import get_langchain_llm, pick_log_file, get_logger

# Import prompt
from src.prompts.log_analyzer_prompts import LOG_ANALYZER_SYSTEM_PROMPT

# Project paths
ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "data" / "logs"
OUT_DIR = ROOT / "outputs" / "log_analyzer"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = get_logger("log_analyzer_langchain")

# Build Langchain prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", LOG_ANALYZER_SYSTEM_PROMPT),
    ("user", "Log file content:\\n\\n{log_content}")
])

# Get LLM
llm = get_langchain_llm()

# Get parser (String output - we'll split manually)
parser = StrOutputParser()

# Build chain
chain = prompt_template | llm | parser

"""
Log Analyzer Agent - Langchain Version
Analyzes log files and generates analysis reports using Langchain.
"""
import sys
import json
from pathlib import Path

# Langchain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Our core utilities
from src.core import get_langchain_llm, pick_log_file, get_logger

# Import prompt
from src.prompts.log_analyzer_prompts import LOG_ANALYZER_SYSTEM_PROMPT

# Project paths
ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = ROOT / "data" / "logs"
OUT_DIR = ROOT / "outputs" / "log_analyzer"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = get_logger("log_analyzer_langchain")

# Build Langchain prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", LOG_ANALYZER_SYSTEM_PROMPT),
    ("user", "Log file content:\\n\\n{log_content}")
])

# Get LLM
llm = get_langchain_llm()

# Get parser (String output - we'll split manually)
parser = StrOutputParser()

# Build chain
chain = prompt_template | llm | parser


def main():
    logger.info("Log Analyzer (Langchain) started")

    # 1. Pick log file
    file_arg = sys.argv[1] if len(sys.argv) > 1 else None
    log_file = pick_log_file(file_arg, LOG_DIR)
    log_content = log_file.read_text(encoding="utf-8")
    logger.info(f"Analyzing: {log_file.name}")

    # 2. Run chain
    logger.info("Calling LLM via Langchain...")
    response = chain.invoke({"log_content": log_content})

    # 3. Split response into 3 parts
    text_report = response
    json_text = '{"error": "No JSON generated"}'
    exec_summary = "Executive summary not generated."

    if "```json" in response:
        parts = response.split("```json")
        text_report = parts[0].strip()
        remainder = parts[1]

        if "```" in remainder:
            json_block = remainder.split("```")[0].strip()
            json_text = json_block

            after_json = remainder.split("```", 1)[1]
            if "---EXECUTIVE---" in after_json:
                exec_parts = after_json.split("---EXECUTIVE---")
                exec_summary = exec_parts[1].strip()

    # 4. Parse JSON
    try:
        json_data = json.loads(json_text)
    except json.JSONDecodeError:
        json_data = {"error": "Failed to parse JSON"}

    # 5. Save outputs
    base_name = log_file.stem

    # Text analysis
    text_file = OUT_DIR / f"{base_name}_analysis_langchain.txt"
    text_file.write_text(text_report, encoding="utf-8")

    # JSON report
    json_file = OUT_DIR / f"{base_name}_report_langchain.json"
    json_file.write_text(json.dumps(json_data, indent=2), encoding="utf-8")

    # Executive summary
    exec_file = OUT_DIR / f"{base_name}_executive_langchain.txt"
    exec_file.write_text(exec_summary, encoding="utf-8")

    # 6. Log results
    logger.info(f"Analysis completed")
    logger.info(f"Text report: {text_file.relative_to(ROOT)}")
    logger.info(f"JSON report: {json_file.relative_to(ROOT)}")
    logger.info(f"Executive summary: {exec_file.relative_to(ROOT)}")
    logger.info("Log Analyzer (Langchain) completed")


if __name__ == "__main__":
    main()