# Cost rates per 1K tokens (as of January 2026)
COST_RATES = {
    "openai": {
        "gpt-5-nano": {"input": 0.00005, "output": 0.0004},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "google": {
        "gemini-2.5-flash": {"input": 0.0003, "output": 0.0025},
    },
    "ollama": {
        "mistral": {"input": 0, "output": 0},
        "llama3": {"input": 0, "output": 0},
        "codellama": {"input": 0, "output": 0},
    }
}

def calculate_cost(provider: str, model: str, prompt_tokens: int, response_tokens: int) -> float:
    """Calculate cost in USD for an LLM call."""

    # Get rates for provider/model
    if provider not in COST_RATES:
        return 0.0

    if model not in COST_RATES[provider]:
        return 0.0

    rates = COST_RATES[provider][model]

    # Calculate cost (tokens / 1000 * rate per 1K)
    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (response_tokens / 1000) * rates["output"]

    return input_cost + output_cost
