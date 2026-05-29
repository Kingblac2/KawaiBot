import requests
import json
import logging
from app import config

logger = logging.getLogger("app.llm")

def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls the local Ollama instance with the specified prompt and model.
    """
    if model is None:
        model = config.DEFAULT_MODEL

    url = f"{config.OLLAMA_API_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0  # Zero temperature for deterministic structured outputs
        }
    }
    
    try:
        logger.info(f"Calling Ollama at {url} with model {model}...")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        # Return a JSON string that the parser can intercept as a fallback
        return json.dumps({
            "intent": "unknown",
            "risk_level": "medium",
            "response": "I encountered an issue communicating with my backend AI service. Please verify that Ollama is running and configured correctly.",
            "reasoning_steps": ["Error connecting to Ollama LLM provider."]
        })
