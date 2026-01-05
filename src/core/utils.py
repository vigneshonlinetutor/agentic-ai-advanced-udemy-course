# Utility Function for file and Json Handling

import json
from pathlib import Path
from typing import List, Dict

def pick_requirement(file_path: str = None, req_dir: str= "data/requirements") -> Path:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist.")
        return path
    
    # Pick the first requirement file in the directory
    txt_files = sorted(Path(req_dir).glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No requirement files found in directory {req_dir}.")
    return txt_files[0]

def parse_json_safely(text: str, raw_file: Path) -> List[Dict]:
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(text, encoding="utf-8")
    
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except:
        pass
    
    cleaned = text.strip();
    
    if cleaned.startswith("```"):
        # Remove Backticks
        cleaned = cleaned.strip("`")
        # Remove language specifier if present
        if "\\n" in cleaned:
            lines = cleaned.split("\\n",1)
            if lines[0].strip() in ["json", "jsonc", "JSON", ""]:
                cleaned = lines[1]
    
    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError("Expected JSON array. But got something else.")
    return data


def pick_log_file(file_path: str = None, log_dir: str = "data/logs") -> Path:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log File {file_path} does not exist.")
        return path
    
    # Pick the first log file in the directory
    log_files = sorted(Path(log_dir).glob("*.log"))
    if not log_files:
        raise FileNotFoundError(f"No log files found in directory {log_dir}.")
    return log_files[0]

def print_summary(duration: float, metadata: dict, llm_calls: int = 1, status: str = "Success"):
    """Print performance summary."""
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("📊 Performance Summary")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"⏱️  Duration:       {duration:.2f}s")
    print(f"🤖 LLM Calls:      {llm_calls}")
    print(f"📝 Total Tokens:   {metadata['total_tokens']}")
    print(f"💰 Cost:           ${metadata['cost_usd']:.6f}")
    print(f"🔧 Provider:       {metadata['provider']}/{metadata['model']}")
    print(f"✅ Status:         {status}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
