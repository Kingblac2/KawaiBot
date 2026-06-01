import re
import logging
from typing import Tuple, Dict, Any
from app import config

logger = logging.getLogger("app.guardrails")

def check_input_guardrails(query: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Checks if a user query triggers any local security blocklists or patterns.
    Returns (is_unsafe, risk_level, response_data).
    """
    if not query or not query.strip():
        return True, "low", {
            "intent": "smalltalk",
            "risk_level": "low",
            "response": "Please enter a valid message.",
            "reasoning_steps": ["Step 1: Analyzed empty input.", "Step 2: Applied guardrails check.", "Step 3: Refused query."]
        }
        
    cleaned_query = query.lower().strip()
    
    # 1. Blocked Keyword Check
    for keyword in config.BLOCKED_KEYWORDS:
        # Use regex to match keyword as word boundaries or inline
        if re.search(r'\b' + re.escape(keyword) + r'\b', cleaned_query) or keyword in cleaned_query:
            logger.warning(f"Guardrail triggered! Query matched blocked keyword: '{keyword}'")
            return True, "high", {
                "intent": "unsafe_query",
                "risk_level": "high",
                "response": "Security Alert: Your query has been flagged for containing restricted keywords or unsafe requests.",
                "reasoning_steps": [
                    "Step 1: Scanned query for sensitive patterns.",
                    f"Step 2: Matched restricted keyword: '{keyword}'.",
                    "Step 3: Triggered local guardrail rule and blocked request."
                ],
                "react_thought": "The query contains restricted terms. Safety check fails.",
                "react_action": "block_request",
                "react_observation": f"Matched blocked keyword '{keyword}'"
            }
            
    # 2. SQL Injection basic heuristic check
    sql_patterns = [
        r"union\s+select", r"select\s+.*\s+from", r"drop\s+table", 
        r"alter\s+table", r"insert\s+into", r"'\s+or\s+'1'='1", r'"\s+or\s+"1"="1'
    ]
    for pattern in sql_patterns:
        if re.search(pattern, cleaned_query):
            logger.warning(f"Guardrail triggered! Query matched SQL Injection pattern.")
            return True, "high", {
                "intent": "unsafe_query",
                "risk_level": "high",
                "response": "Security Alert: Your request was blocked due to detecting database injection patterns.",
                "reasoning_steps": [
                    "Step 1: Scanned query for SQL syntaxes.",
                    "Step 2: Matched potential SQL injection pattern.",
                    "Step 3: Triggered local guardrail rules."
                ],
                "react_thought": "SQL Injection attempt detected. Blocking query.",
                "react_action": "block_request",
                "react_observation": "Matched SQL pattern"
            }
            
    return False, "safe", {}

def filter_output_guardrails(response_text: str) -> str:
    """
    Scrubs sensitive company keys or admin tokens from the response.
    """
    cleaned = response_text
    for token in config.SENSITIVE_RESPONSE_FILTER:
        if token in cleaned:
            logger.warning(f"Output Guardrail triggered! Redacting sensitive token: '{token}'")
            cleaned = cleaned.replace(token, "[REDACTED_SENSITIVE_DATA]")
            
    return cleaned
