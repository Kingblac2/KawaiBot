import requests
import json
import logging
import time
from app import config

logger = logging.getLogger("app.llm")

def call_llm(prompt: str, model: str = None) -> str:
    """
    Calls the Google Gemini 3.1 API to generate a response.
    Uses the model configured in config.GEMINI_MODEL (defaults to gemini-3.1-flash-lite).
    Includes automatic rate limit (429) retries.
    """
    if not config.GEMINI_API_KEY:
        error_msg = "GEMINI_API_KEY is not set. Please add it to your .env file."
        logger.error(error_msg)
        return json.dumps({
            "intent": "unknown",
            "risk_level": "medium",
            "response": error_msg,
            "reasoning_steps": ["No API key configured."]
        })

    clean_key = config.GEMINI_API_KEY.strip().strip('"\'')
    current_model = model if model and "gemini" in model else config.GEMINI_MODEL

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={clean_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0}
    }

    max_retries = 3
    last_error = ""

    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Gemini model {current_model} (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(url, headers=headers, json=payload, timeout=40)

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                last_error = "Gemini returned an empty response."
                logger.warning(last_error)
                break

            if response.status_code == 429 and attempt < max_retries - 1:
                retry_delay = 4.0
                logger.warning(f"Rate limited (429). Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                continue

            last_error = f"HTTP {response.status_code}: {response.text}"
            logger.warning(f"Gemini API error: {last_error}")
            break

        except Exception as e:
            last_error = str(e)
            logger.error(f"Gemini connection error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2.0)
                continue
            break

    return json.dumps({
        "intent": "unknown",
        "risk_level": "medium",
        "response": f"Gemini API call failed: {last_error}",
        "reasoning_steps": ["Gemini 3.1 API execution failed after retries."]
    })
