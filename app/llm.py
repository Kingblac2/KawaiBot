import requests
import json
import logging
from app import config

logger = logging.getLogger("app.llm")

def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls Gemini API if GEMINI_API_KEY is configured. 
    Otherwise, falls back to local Ollama instance.
    """
    # 1. Gemini API Engine
    if config.GEMINI_API_KEY:
        gemini_model = model if model and "gemini" in model else config.GEMINI_MODEL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={config.GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.0
            }
        }
        try:
            logger.info(f"Calling Gemini API model {gemini_model}...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Extract content from Gemini response path
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            
            logger.warning(f"Unexpected response structure from Gemini API: {result}")
            return ""
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            # Fall through to local Ollama as backup if Gemini API fails
            logger.info("Falling back to local Ollama...")

    # 2. Local Ollama Fallback Engine
    if model is None or "gemini" in model:
        model = config.DEFAULT_MODEL

    url = f"{config.OLLAMA_API_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        logger.info(f"Calling local Ollama at {url} with model {model}...")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        logger.error(f"Error calling Ollama fallback: {e}")
        return json.dumps({
            "intent": "unknown",
            "risk_level": "medium",
            "response": "I encountered an issue communicating with the AI service. If you are using Gemini, check your GEMINI_API_KEY setting. Otherwise, verify local Ollama status.",
            "reasoning_steps": ["Error connecting to all configured LLM providers."]
        })
