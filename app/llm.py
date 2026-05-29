import requests
import json
import logging
import time
from app import config

logger = logging.getLogger("app.llm")

def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls OpenAI API if OPENAI_API_KEY is configured.
    Otherwise, calls Gemini API if GEMINI_API_KEY is configured. 
    Otherwise, falls back to local Ollama instance.
    Includes sequential model fallback loops and automatic rate limit (429) retries.
    """
    openai_error = None
    gemini_error = None
    
    # 1. OpenAI API Engine
    if config.OPENAI_API_KEY:
        clean_key = config.OPENAI_API_KEY.strip().strip('"\'')
        if clean_key:
            user_model = model if model and ("gpt" in model or "o1" in model) else config.OPENAI_MODEL
            openai_models = [
                user_model,
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-3.5-turbo"
            ]
            seen = set()
            openai_models = [x for x in openai_models if not (x in seen or seen.add(x))]
            
            last_openai_error = ""
            for current_model in openai_models:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {clean_key}"
                }
                payload = {
                    "model": current_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0
                }
                try:
                    logger.info(f"Attempting OpenAI model {current_model}...")
                    
                    max_retries = 3
                    for attempt in range(max_retries):
                        response = requests.post(url, headers=headers, json=payload, timeout=40)
                        if response.status_code == 200:
                            break
                        if response.status_code == 429 and attempt < max_retries - 1:
                            logger.warning(f"OpenAI Rate limited (429) on {current_model}. Retrying in 4s...")
                            time.sleep(4.0)
                            continue
                        break

                    if response.status_code == 200:
                        result = response.json()
                        choices = result.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "").strip()
                    
                    last_openai_error = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(f"OpenAI model {current_model} returned error: {last_openai_error}")
                except Exception as e:
                    last_openai_error = str(e)
                    logger.warning(f"OpenAI model {current_model} connection error: {e}")
            
            openai_error = last_openai_error
            logger.warning(f"OpenAI Engine failed: {openai_error}. Moving to next provider...")

    # 2. Gemini API Engine
    if config.GEMINI_API_KEY:
        clean_key = config.GEMINI_API_KEY.strip().strip('"\'')
        if clean_key:
            user_model = model if model and "gemini" in model else config.GEMINI_MODEL
            configs_to_try = [
                (user_model, "v1"),
                (user_model, "v1beta"),
                ("gemini-2.0-flash", "v1"),
                ("gemini-1.5-flash", "v1"),
                ("gemini-2.0-flash", "v1beta"),
                ("gemini-1.5-flash", "v1beta"),
            ]
            seen = set()
            configs_to_try = [x for x in configs_to_try if not (x in seen or seen.add(x))]
            
            last_gemini_error = ""
            for current_model, api_version in configs_to_try:
                url = f"https://generativelanguage.googleapis.com/{api_version}/models/{current_model}:generateContent?key={clean_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.0}
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
                        continue
                    
                    last_gemini_error = f"HTTP {response.status_code}: {response.text}"
                except Exception as e:
                    last_gemini_error = str(e)
            
            gemini_error = last_gemini_error
            logger.warning(f"Gemini Engine failed: {gemini_error}. Moving to next provider...")

    # 3. Local Ollama Fallback Engine
    if model is None or "gemini" in model or "gpt" in model:
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
        
        # Build consolidated error message
        error_msg = "All configured AI services failed to execute."
        if openai_error:
            error_msg += f" [OpenAI Error: {openai_error}]"
        if gemini_error:
            error_msg += f" [Gemini Error: {gemini_error}]"
        error_msg += f" [Local Ollama Error: {str(e)}]."
        
        return json.dumps({
            "intent": "unknown",
            "risk_level": "medium",
            "response": error_msg,
            "reasoning_steps": ["Triple fallback API execution pipeline failed."]
        })
