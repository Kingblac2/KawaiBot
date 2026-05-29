import json
import os
import datetime
from pathlib import Path
from typing import List, Dict

CONVO_FILE = Path(__file__).resolve().parent.parent / "conversations.json"

def init_db():
    if not CONVO_FILE.exists():
        with open(CONVO_FILE, "w") as f:
            json.dump([], f)

def save_chat(message: str, response_json: Dict) -> Dict:
    """
    Saves a chat message and response to the local JSON file database.
    """
    init_db()
    
    chat_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": message,
        "intent": response_json.get("intent", "unknown"),
        "risk_level": response_json.get("risk_level", "low"),
        "response": response_json.get("response", ""),
        "reasoning_steps": response_json.get("reasoning_steps", []),
        "react_thought": response_json.get("react_thought", ""),
        "react_action": response_json.get("react_action", ""),
        "react_observation": response_json.get("react_observation", ""),
        "full_data": response_json
    }
    
    try:
        with open(CONVO_FILE, "r") as f:
            data = json.load(f)
    except Exception:
        data = []
        
    data.append(chat_entry)
    
    with open(CONVO_FILE, "w") as f:
        json.dump(data, f, indent=2)
        
    return chat_entry

def get_history() -> List[Dict]:
    init_db()
    try:
        with open(CONVO_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []
