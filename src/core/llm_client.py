# Simple LLM client interface for interacting with language models. - Ollama , OpenAI, Google

import os
from typing import List, Dict
import httpx
from dotenv import load_dotenv
import time

from .cost_tracker import calculate_cost

load_dotenv() # Load environment variables from .env file

# Read configuration from .env
PROVIDER = os.getenv("PROVIDER", "openai")  # Default to openai
MODEL = os.getenv("MODEL", "gpt-4o-mini") # Default to gpt-4o-mini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY","")
OLLAMA_HOST = os.getenv("OLLAMA_HOST","http://localhost:11434")
TIMEOUT = int(os.getenv("TIMEOUT", 60))

# Type alias for message structure
Message = Dict[str, str]

def chat(messages: List[Message]) -> Dict:
    """Send messages to LLM and return response with metadata."""
    if not messages:
        raise ValueError("Messages list cannot be empty")

    start_time = time.time()

    if PROVIDER == "openai":
        response = _call_openai(messages)
    elif PROVIDER == "google":
        response = _call_gemini(messages)
    elif PROVIDER == "ollama":
        response = _call_ollama(messages)
    else:
        raise NotImplementedError(f"Provider {PROVIDER} not implemented")

    duration_ms = int((time.time() - start_time) * 1000)

    # Estimate tokens (rough: 1 token ≈ 4 characters)
    prompt_text = " ".join([m["content"] for m in messages])
    prompt_tokens = len(prompt_text) // 4
    response_tokens = len(response) // 4
    
    # Calculate Cost
    cost = calculate_cost(PROVIDER, MODEL, prompt_tokens, response_tokens)

    return {
        "response": response,
        "metadata": {
            "provider": PROVIDER,
            "model": MODEL,
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": prompt_tokens + response_tokens,
            "duration_ms": duration_ms,
            "cost_usd": cost
        }
    }

def _http_post(url: str, headers: Dict, payload: Dict) -> Dict:
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

def _call_openai(messages: List[Message]) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in the .env file")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
    }
    data = _http_post(url, headers, payload)
    return data["choices"][0]["message"]["content"]

def _call_gemini(messages: List[Message]) -> str:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in the .env file")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    headers = {
        "x-goog-api-key": GOOGLE_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Gemini needs alternating user/model turns
    # Merge system message into first user message
    contents = []
    system_text = ""
    
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        elif msg["role"] == "user":
            # Combine system + user if system exists
            if system_text:
                combined = f"{system_text}\n\n{msg['content']}"
                contents.append({
                    "role": "user",
                    "parts": [{"text": combined}]
                })
                system_text = ""  # Use system only once
            else:
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg["content"]}]
                })
        elif msg["role"] == "assistant":
            contents.append({
                "role": "model",
                "parts": [{"text": msg["content"]}]
            })
    
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": 0}
    }
    
    data = _http_post(url, headers, payload)
    return data["candidates"][0]["content"]["parts"][0]["text"]

def _call_ollama(messages: List[Message]) -> str:
    url = f"{OLLAMA_HOST.rstrip('/')}/api/chat"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    data = _http_post(url, headers, payload)
    
    if "message" not in data or "content" not in data["message"]:
        raise RuntimeError("Ollama returned empty response. Check if Ollama is running ?")
    return data["message"]["content"]
