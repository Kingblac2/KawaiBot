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
        clean_key = config.GEMINI_API_KEY.strip().strip('"\'')
        if clean_key:
            gemini_model = model if model and "gemini" in model else config.GEMINI_MODEL
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={clean_key}"
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
                
                if response.status_code != 200:
                    logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
                    return json.dumps({
                        "intent": "unknown",
                        "risk_level": "medium",
                        "response": f"Gemini API Error (HTTP {response.status_code}): {response.text}",
                        "reasoning_steps": [f"Gemini API returned error code {response.status_code}."]
                    })

                result = response.json()
                
                # Extract content from Gemini response path
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                
                logger.warning(f"Unexpected response structure from Gemini API: {result}")
                return json.dumps({
                    "intent": "unknown",
                    "risk_level": "medium",
                    "response": f"Gemini returned an unexpected response format: {result}",
                    "reasoning_steps": ["Unexpected payload format from Gemini."]
                })
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}")
                # If Gemini key was set, return the error instead of confusing fallback
                return json.dumps({
                    "intent": "unknown",
                    "risk_level": "medium",
                    "response": f"Gemini connection error: {str(e)}",
                    "reasoning_steps": ["Failed to establish connection to Gemini endpoint."]
                })

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
