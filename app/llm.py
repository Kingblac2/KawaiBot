import requests
import json
import logging
import time
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
            user_model = model if model and "gemini" in model else config.GEMINI_MODEL
            
            # Sequentially try models and API versions to heal compatibility issues automatically
            configs_to_try = [
                (user_model, "v1"),
                (user_model, "v1beta"),
                ("gemini-2.0-flash", "v1"),
                ("gemini-1.5-flash", "v1"),
                ("gemini-2.0-flash", "v1beta"),
                ("gemini-1.5-flash", "v1beta"),
            ]
            
            # Deduplicate while preserving order
            seen = set()
            configs_to_try = [x for x in configs_to_try if not (x in seen or seen.add(x))]
            
            last_error_msg = ""
            for current_model, api_version in configs_to_try:
                url = f"https://generativelanguage.googleapis.com/{api_version}/models/{current_model}:generateContent?key={clean_key}"
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
                    logger.info(f"Attempting Gemini endpoint: {api_version}/models/{current_model}...")
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        response = requests.post(url, headers=headers, json=payload, timeout=40)
                        
                        if response.status_code == 200:
                            break
                        
                        if response.status_code == 429:
                            retry_delay = 4.0
                            try:
                                error_json = response.json()
                                logger.warning(f"Gemini API rate limited (429). Details: {error_json}")
                            except:
                                pass
                            
                            if attempt < max_retries - 1:
                                logger.warning(f"Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                continue
                        
                        break

                    if response.status_code == 200:
                        result = response.json()
                        candidates = result.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                        
                        logger.warning(f"Unexpected response structure for {current_model} ({api_version}): {result}")
                        continue
                    
                    last_error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"Endpoint {api_version}/{current_model} returned: {last_error_msg}")
                except Exception as e:
                    last_error_msg = str(e)
                    logger.warning(f"Endpoint {api_version}/{current_model} connection error: {e}")
            
            # If we attempted Gemini and all options failed:
            masked_key = f"{clean_key[:6]}...{clean_key[-4:]}" if len(clean_key) > 10 else f"Short key ({clean_key})"
            return json.dumps({
                "intent": "unknown",
                "risk_level": "medium",
                "response": f"Gemini API Negotiation failed. API Key in use: {masked_key} (length: {len(clean_key)}). Last error: {last_error_msg}",
                "reasoning_steps": [f"All fallback Gemini configurations failed using key: {masked_key}."]
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
