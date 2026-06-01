import json
import re
import logging

logger = logging.getLogger("parsers.json_parser")

def extract_and_parse_json(text: str) -> dict:
    """
    Finds the first '{' and the last '}' in the text,
    attempts to load it as JSON, and returns a dictionary.
    If parsing fails, returns a fallback dictionary with a safe explanation.
    """
    if not text:
        return {}

    cleaned = text.strip()
    
    # Try regex matching to extract JSON block from markdown or plain text
    try:
        # Match from the first '{' to the last '}'
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = cleaned

        # Basic cleanup: remove markdown wrapper lines
        json_str = re.sub(r"^```json\s*", "", json_str, flags=re.IGNORECASE)
        json_str = re.sub(r"^```\s*", "", json_str, flags=re.IGNORECASE)
        json_str = re.sub(r"\s*```$", "", json_str, flags=re.IGNORECASE)
        json_str = json_str.strip()

        # Parse JSON
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Failed to parse structured JSON: {e}. Raw content: {text}")
        
        # Fallback heuristic: Try to find keys manually or return a safe structure
        fallback = {
            "intent": "unknown",
            "risk_level": "medium",
            "response": text,
            "reasoning_steps": ["Step 1: Failed to parse structural JSON response.", "Step 2: Used fallback text extraction."]
        }
        return fallback
