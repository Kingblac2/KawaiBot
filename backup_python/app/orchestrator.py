import logging
import json
from pathlib import Path
from app import config, guardrails, llm, database
from parsers import json_parser

logger = logging.getLogger("app.orchestrator")

def load_prompt_file(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading prompt file {path}: {e}")
        return ""

def run_chat_pipeline(user_query: str) -> dict:
    """
    Executes the advanced AI reasoning workflow:
    User Query -> Heuristic Guardrails -> Safety Prompt Check -> Intent Detection -> ReAct Gen -> JSON parsing.
    """
    logger.info(f"Incoming query: '{user_query}'")

    # Step 1: Heuristic Guardrails Check
    is_unsafe, risk_level, guardrail_response = guardrails.check_input_guardrails(user_query)
    if is_unsafe:
        logger.info("Blocked by heuristic guardrails.")
        database.save_chat(user_query, guardrail_response)
        return guardrail_response

    # Load system prompt
    system_prompt = load_prompt_file(config.SYSTEM_PROMPT_PATH)

    # Step 2: Safety Check via LLM (Double-Check)
    safety_prompt_template = load_prompt_file(config.SAFETY_CHECK_PATH)
    safety_prompt = safety_prompt_template.replace("{{QUERY}}", user_query)
    safety_response_text = llm.call_llm(safety_prompt)
    safety_data = json_parser.extract_and_parse_json(safety_response_text)
    
    is_llm_unsafe = safety_data.get("safety") == "UNSAFE"
    if is_llm_unsafe:
        logger.warning(f"Blocked by LLM safety check: {safety_data.get('reason')}")
        refusal_response = {
            "intent": "unsafe_query",
            "risk_level": "high",
            "response": f"Security Alert: Your request was evaluated as unsafe. Reason: {safety_data.get('reason', 'Policy violation.')}",
            "reasoning_steps": [
                "Step 1: Scanned input against core security guidelines.",
                f"Step 2: LLM flagged query as UNSAFE. Reason: {safety_data.get('reason')}",
                "Step 3: Rejected request and generated refusal."
            ],
            "react_thought": "LLM security check identified a policy violation. Blocking query.",
            "react_action": "refuse_request",
            "react_observation": f"LLM returned safety evaluation: {safety_data.get('reason')}"
        }
        database.save_chat(user_query, refusal_response)
        return refusal_response

    # Step 3: Intent Detection via LLM
    intent_prompt_template = load_prompt_file(config.INTENT_DETECT_PATH)
    intent_prompt = intent_prompt_template.replace("{{QUERY}}", user_query)
    intent_response_text = llm.call_llm(intent_prompt)
    intent_data = json_parser.extract_and_parse_json(intent_response_text)
    intent = intent_data.get("intent", "company_info")

    # Step 4: Response Generation with CoT / ReAct
    gen_prompt_template = load_prompt_file(config.RESPONSE_GEN_PATH)
    
    # Fill prompt chaining variables
    response_prompt = (
        gen_prompt_template
        .replace("{{SYSTEM_PROMPT}}", system_prompt)
        .replace("{{INTENT}}", intent)
        .replace("{{RISK_LEVEL}}", "safe")
        .replace("{{QUERY}}", user_query)
    )

    raw_gen_response = llm.call_llm(response_prompt)
    
    # Step 5: JSON Output Parsing
    parsed_response = json_parser.extract_and_parse_json(raw_gen_response)
    
    # Standardize format in case LLM missed some keys
    if "intent" not in parsed_response:
        parsed_response["intent"] = intent
    if "risk_level" not in parsed_response:
        parsed_response["risk_level"] = "safe"
    if "response" not in parsed_response:
        # If response was just plain text, capture it
        parsed_response["response"] = raw_gen_response
        
    # Safeguard default reasoning steps
    if "reasoning_steps" not in parsed_response or not parsed_response["reasoning_steps"]:
        parsed_response["reasoning_steps"] = [
            "Step 1: Analyzed prompt using intent classification.",
            f"Step 2: Classified intent as {intent} and safety status as safe.",
            "Step 3: Answered user request professionally."
        ]

    # Step 6: Output Guardrails / Redaction
    parsed_response["response"] = guardrails.filter_output_guardrails(parsed_response["response"])

    # Step 7: Persist and Return
    database.save_chat(user_query, parsed_response)
    return parsed_response
